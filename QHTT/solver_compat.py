"""
solver_compat.py — Lớp tương thích (Compatibility Layer) cho api/solver.py.

Cung cấp class SimplexSolverCompat với interface giống hệt SimplexSolver trong api/solver.py,
nhưng sử dụng lõi thuật toán của QHTT (BoGiaiDonHinh + giai_hai_pha + tien_ich).

Mục tiêu:
  - Không sửa bất kỳ file gốc nào trong QHTT/
  - Cho phép các hệ thống dùng JSON input/output (như api/) gọi vào lõi QHTT
  - Hỗ trợ đầy đủ 3 phương thức: standard, bland, two-phase

Input  (giống api/solver.py):
    c           : List[float] — hệ số hàm mục tiêu
    constraints : List[dict] — [{"coeffs": [...], "type": "<=|>=|=", "rhs": float}, ...]
    objective   : "max" | "min"
    bounds      : Optional[List[List[Optional[float]]]] — giới hạn biến
    method      : "standard" | "bland" | "two-phase"

Output (giống api/solver.py):
    {
        "status":        "optimal" | "infeasible" | "unbounded" | "multiple" | "cycling" | "method_error",
        "message":       str,
        "optimal_value": str | None,
        "solution":      dict,   # {"x1": "...", "x2": "...", ...}
        "steps":         list    # danh sách bước (text-based, từ QHTT)
    }
"""

import sys
import os
import contextlib
from io import StringIO
from fractions import Fraction

# Đảm bảo import được các module QHTT (khi chạy từ ngoài thư mục QHTT)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from tien_ich import format_fraction, to_subscript
from phuong_phap_don_hinh import BoGiaiDonHinh
from phuong_phap_hai_pha import giai_hai_pha


# ─── Context manager bắt stdout ──────────────────────────────────────────────

@contextlib.contextmanager
def _capture_stdout():
    old = sys.stdout
    sys.stdout = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = old


# ─── Hàm tiện ích nội bộ ─────────────────────────────────────────────────────

def _frac(x) -> Fraction:
    if isinstance(x, Fraction):
        return x
    return Fraction(x).limit_denominator(10 ** 9)


def _build_standard_input(c_orig, constraints, objective, bounds):
    """
    Chuyển input dạng JSON (như api/) sang các mảng (c, A, b, actual_vars, var_mapping)
    tương thích với QHTT's giai_hai_pha.

    Quy tắc:
      - Nội bộ QHTT luôn giải bài MIN; nếu objective=max thì đảo dấu c.
      - Ràng buộc >= được nhân -1 để thành <=.
      - Ràng buộc = được tách thành 2 dòng <=.
      - bounds được chuyển thành ràng buộc bổ sung nếu cần.
    """
    n = len(c_orig)
    is_max = (objective == "max")

    # 1. Hàm mục tiêu — QHTT giải MIN, nếu max thì đảo dấu
    c_raw = [_frac(ci) for ci in c_orig]
    if is_max:
        c_base = [-ci for ci in c_raw]
    else:
        c_base = list(c_raw)

    # Đọc bounds gốc
    bounds_list = bounds if bounds else [[0, None] for _ in range(n)]

    # 2. Xử lý phép thế biến (substitutions)
    actual_vars = []
    var_mapping = {}
    var_consts = {}
    
    new_c_arr = []
    # Khởi tạo ma trận A mới, tạm thời để rỗng các cột
    new_A_cols = [] 
    
    zeta_offset = Fraction(0)
    b_offsets = [Fraction(0)] * len(constraints)
    
    # Biến phụ cho các constraint upper bound
    upper_bounds = []

    for j in range(n):
        orig_var = f"x{j+1}"
        lo, hi = bounds_list[j]
        c_j = c_base[j]
        col_j = [_frac(con["coeffs"][j]) for con in constraints]
        
        # TH1: x_j >= 0 (Chuẩn)
        if lo == 0 and hi is None:
            actual_vars.append(orig_var)
            var_mapping[orig_var] = [(orig_var, Fraction(1))]
            var_consts[orig_var] = Fraction(0)
            
            new_c_arr.append(c_j)
            new_A_cols.append(col_j)
            
        # TH2: x_j <= 0 (Tương đương lo is None, hi == 0)
        elif lo is None and hi == 0:
            new_var = f"x{j+1}'"
            actual_vars.append(new_var)
            var_mapping[orig_var] = [(new_var, Fraction(-1))]
            var_consts[orig_var] = Fraction(0)
            
            new_c_arr.append(-c_j)
            new_A_cols.append([-a for a in col_j])
            
        # TH3: x_j tùy ý (Free variable: lo is None, hi is None)
        elif lo is None and hi is None:
            v1 = f"x{j+1}'"
            v2 = f"x{j+1}''"
            actual_vars.extend([v1, v2])
            var_mapping[orig_var] = [(v1, Fraction(1)), (v2, Fraction(-1))]
            var_consts[orig_var] = Fraction(0)
            
            new_c_arr.extend([c_j, -c_j])
            new_A_cols.extend([col_j, [-a for a in col_j]])
            
        # TH4: x_j >= lo (hoặc x_j trong [lo, hi])
        else:
            new_var = f"{orig_var}'" if (lo is not None and lo != 0) else orig_var
            actual_vars.append(new_var)
            
            offset = _frac(lo) if lo is not None else Fraction(0)
            
            var_mapping[orig_var] = [(new_var, Fraction(1))]
            var_consts[orig_var] = offset
            
            # x_j = x_j' + offset
            new_c_arr.append(c_j)
            new_A_cols.append(col_j)
            
            # Cập nhật hằng số
            zeta_offset += c_j * offset
            for i in range(len(constraints)):
                b_offsets[i] += col_j[i] * offset
                
            # Nếu có cận trên, thêm ràng buộc phụ: x_j' <= hi - offset
            if hi is not None:
                upper_bounds.append((len(actual_vars) - 1, _frac(hi) - offset))

    # 3. Tạo ma trận A và b cho các ràng buộc gốc
    A = []
    b = []
    for i, con in enumerate(constraints):
        t = con["type"]
        rhs = _frac(con["rhs"]) - b_offsets[i]
        
        row = [new_A_cols[col_idx][i] for col_idx in range(len(new_A_cols))]
        
        if t == "<=":
            A.append(row)
            b.append(rhs)
        elif t == ">=":
            A.append([-a for a in row])
            b.append(-rhs)
        elif t == "=":
            A.append(list(row))
            b.append(rhs)
            A.append([-a for a in row])
            b.append(-rhs)

    # 4. Thêm các ràng buộc upper bound
    for col_idx, max_val in upper_bounds:
        row = [Fraction(0)] * len(actual_vars)
        row[col_idx] = Fraction(1)
        A.append(row)
        b.append(max_val)

    return new_c_arr, A, b, actual_vars, var_mapping, var_consts, is_max, zeta_offset


# ─── SimplexSolverCompat ─────────────────────────────────────────────────────

class SimplexSolverCompat:
    """
    Lớp tương thích với api/solver.py SimplexSolver.

    Sử dụng lõi QHTT (BoGiaiDonHinh + giai_hai_pha) nhưng nhận/trả về
    cùng format JSON như SimplexSolver gốc trong api/.

    Hỗ trợ method: "standard", "bland", "two-phase"
    """

    def __init__(self, c, constraints, objective="max", bounds=None, method="standard"):
        self.c           = c
        self.constraints = constraints
        self.objective   = objective
        self.bounds      = bounds
        self.method      = method

        self.status        = None
        self.optimal_value = None
        self.solution      = {}
        self.steps         = []

    # ── Public ───────────────────────────────────────────────────────────────

    def solve(self):
        """Giải bài toán và trả về dict tương thích api/solver.py."""
        # Kiểm tra phương thức standard/bland không hỗ trợ >= hoặc =
        if self.method in ("standard", "bland"):
            for con in self.constraints:
                if con["type"] in (">=", "="):
                    self.status = "method_error"
                    return self._result(
                        "Bài toán chứa ràng buộc ≥ hoặc =. "
                        "Phương pháp Đơn hình gốc/Bland yêu cầu tất cả ở dạng ≤. "
                        "Vui lòng chọn Đơn hình 2 Pha."
                    )

        # Xây dựng input cho QHTT
        c_arr, A, b, actual_vars, var_mapping, var_consts, is_max, zeta_offset = \
            _build_standard_input(self.c, self.constraints, self.objective, self.bounds)

        # Chọn phương thức
        if self.method in ("standard", "bland"):
            qhtt_method = "bland" if self.method == "bland" else "simplex"
            force_two_phase = False
        else:
            # two-phase
            qhtt_method = "simplex"
            force_two_phase = True

        # Kiểm tra b_i < 0 → bắt buộc dùng two_phase
        has_negative_b = any(val < Fraction(0) for val in b)
        if has_negative_b and not force_two_phase:
            force_two_phase = True

        # Giải và bắt output text
        with _capture_stdout() as captured:
            res, solver_obj = giai_hai_pha(
                c=c_arr,
                A=A,
                b=b,
                standard_vars=actual_vars,
                substitutions=var_mapping,
                verbose=True,
                method=qhtt_method,
                is_max=is_max,
                original_vars=[f"x{i+1}" for i in range(len(self.c))],
                force_two_phase=force_two_phase,
                var_consts=var_consts,
                zeta_offset=zeta_offset
            )

            # Lấy kết luận nếu thành công
            output_text_before = captured.getvalue()
            conclusion_text = ""

            if res not in ("Infeasible", "Cycling") and solver_obj is not None:
                with _capture_stdout() as cap2:
                    solver_obj.in_ket_luan(is_max)
                conclusion_text = cap2.getvalue()

        full_text = output_text_before + conclusion_text

        # Ánh xạ trạng thái QHTT → api status
        status_map = {
            "Optimal":      "optimal",
            "Infeasible":   "infeasible",
            "Unbounded":    "unbounded",
            "Cycling":      "cycling",
            "LimitReached": "cycling",
        }
        self.status = status_map.get(res, "optimal")

        # Trích nghiệm
        if solver_obj is not None and res == "Optimal":
            self._extract_solution(solver_obj, is_max, actual_vars)
            # Kiểm tra vô số nghiệm
            if any(v == Fraction(0) for v in solver_obj.c):
                self.status = "multiple"

        # Bước text (dùng từng dòng làm step) và trích xuất point_coords
        self.steps = self._build_steps(full_text, len(actual_vars))

        # Thông điệp kết luận
        msg = self._make_message(res, is_max)
        return self._result(msg)

    def get_standard_form(self):
        """
        Trả về bài toán dạng chuẩn (min, tất cả <=, biến >= 0).
        Tương thích với api/solver.py SimplexSolver.get_standard_form().
        """
        bounds = self.bounds if self.bounds else [[0, None] for _ in range(len(self.c))]

        # 1. Mục tiêu → min
        if self.objective == "max":
            c_std = [-float(ci) for ci in self.c]
        else:
            c_std = [float(ci) for ci in self.c]

        # 2. Ràng buộc → <=
        std_constraints = []
        for con in self.constraints:
            a = [float(x) for x in con["coeffs"]]
            b = float(con["rhs"])
            t = con["type"]

            if t == ">=":
                std_constraints.append({
                    "coeffs": [-x for x in a],
                    "type": "<=",
                    "rhs": -b
                })
            elif t == "<=":
                std_constraints.append({
                    "coeffs": list(a),
                    "type": "<=",
                    "rhs": b
                })
            elif t == "=":
                std_constraints.append({
                    "coeffs": list(a),
                    "type": "<=",
                    "rhs": b
                })
                std_constraints.append({
                    "coeffs": [-x for x in a],
                    "type": "<=",
                    "rhs": -b
                })

        # 3. Chuyển đổi biến theo bounds
        final_c = []
        final_constraints = [
            {"coeffs": [], "type": "<=", "rhs": con["rhs"]}
            for con in std_constraints
        ]
        var_names = []

        for j in range(len(self.c)):
            bnd = bounds[j]
            is_nonneg = (bnd[0] is not None and bnd[0] >= 0)
            is_nonpos = (bnd[1] is not None and bnd[1] <= 0)

            if is_nonpos and not is_nonneg:
                # x_j <= 0 → y_j = -x_j >= 0
                final_c.append(-c_std[j])
                for i, con in enumerate(std_constraints):
                    final_constraints[i]["coeffs"].append(-con["coeffs"][j])
                var_names.append(f"y{j+1} (=-x{j+1})")
            elif not is_nonneg and not is_nonpos:
                # tự do → x_j' - x_j''
                final_c.append(c_std[j])
                final_c.append(-c_std[j])
                for i, con in enumerate(std_constraints):
                    final_constraints[i]["coeffs"].append(con["coeffs"][j])
                    final_constraints[i]["coeffs"].append(-con["coeffs"][j])
                var_names.append(f"x{j+1}'")
                var_names.append(f"x{j+1}''")
            else:
                # x_j >= 0
                final_c.append(c_std[j])
                for i, con in enumerate(std_constraints):
                    final_constraints[i]["coeffs"].append(con["coeffs"][j])
                var_names.append(f"x{j+1}")

        return {
            "objective":   "min",
            "c":           final_c,
            "constraints": final_constraints,
            "variables":   var_names
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _extract_solution(self, solver_obj: BoGiaiDonHinh, is_max: bool, actual_vars):
        """Đọc nghiệm từ BoGiaiDonHinh đã giải xong."""
        n = len(actual_vars)

        # Giá trị tối ưu: QHTT lưu zeta = giá trị min nội bộ
        raw_zeta = solver_obj.zeta  # zeta của min
        if is_max:
            opt = -raw_zeta
        else:
            opt = raw_zeta
        self.optimal_value = format_fraction(opt)

        # Giá trị từng biến
        for j, vname in enumerate(actual_vars):
            if vname in solver_obj.basic_vars:
                idx = solver_obj.basic_vars.index(vname)
                self.solution[f"x{j+1}"] = format_fraction(solver_obj.b[idx])
            else:
                self.solution[f"x{j+1}"] = "0"

    def _build_steps(self, text: str, n_vars: int):
        """Chuyển output text của QHTT thành list steps, đồng thời parse point_coords."""
        import re
        from tien_ich import to_subscript
        
        steps = []
        lines = text.split("\n")
        current_block = []

        def process_block(block_lines):
            block_text = "\n".join(block_lines)
            step_dict = {"note": block_text}
            
            # Nếu block chứa bảng đơn hình (có đường gạch ngang)
            if "──" in block_text:
                # Phân tích tìm biến cơ sở và hằng số
                # Pattern: {var_name} = {constant} ...
                basic_vars_vals = {}
                for line in block_lines:
                    line_clean = line.strip().lstrip('←').strip()
                    # Tìm dạng: "x₁ = 5 - ..." hoặc "w₁ = 2 + ..."
                    match = re.match(r'^([a-zA-Z]+[₀-₉]+)\s*=\s*(-?\s*\d+(?:\.\d+)?(?:/\d+)?)', line_clean)
                    if match:
                        var = match.group(1)
                        # Loại bỏ khoảng trắng giữa dấu trừ và số nếu có
                        val_str = match.group(2).replace(' ', '')
                        try:
                            basic_vars_vals[var] = float(Fraction(val_str))
                        except Exception:
                            basic_vars_vals[var] = 0.0

                # Lấy tọa độ của các biến quyết định x₁, x₂, ..., xₙ
                coords = []
                for i in range(1, n_vars + 1):
                    var_sub = to_subscript(f"x{i}")
                    # Nếu biến quyết định nằm trong cơ sở, lấy giá trị hằng số, ngược lại = 0
                    val = basic_vars_vals.get(var_sub, 0.0)
                    coords.append(val)
                
                step_dict["point_coords"] = coords
                step_dict["point_str"] = f"x({', '.join(str(round(c, 4)) for c in coords)})"

            steps.append(step_dict)

        for line in lines:
            if line.strip() == "" and current_block:
                process_block(current_block)
                current_block = []
            else:
                current_block.append(line)

        if current_block:
            process_block(current_block)

        return steps

    def _make_message(self, res: str, is_max: bool) -> str:
        z_display = "zₘₐₓ" if is_max else "zₘᵢₙ"
        if res == "Optimal":
            if self.status == "multiple":
                return (
                    f"Vô số nghiệm tối ưu — tồn tại biến không-cơ-sở "
                    f"có hệ số = 0 trong dòng z ({z_display} = {self.optimal_value})."
                )
            return (
                f"Nghiệm tối ưu duy nhất — "
                f"mọi hệ số biến không-cơ-sở trong dòng z đều > 0 "
                f"({z_display} = {self.optimal_value})."
            )
        elif res == "Infeasible":
            return "Vô nghiệm — miền chấp nhận được là rỗng."
        elif res == "Unbounded":
            sign = "+∞" if is_max else "-∞"
            return f"Bài toán không giới nội — hàm mục tiêu tiến tới {sign}."
        elif res in ("Cycling", "LimitReached"):
            return (
                "Bài toán bị lặp vòng (Cycling Detected). "
                "Vui lòng chuyển sang Quy tắc Bland."
            )
        return f"Trạng thái: {res}"

    def _result(self, message: str) -> dict:
        return {
            "status":        self.status,
            "message":       message,
            "optimal_value": self.optimal_value,
            "solution":      self.solution,
            "steps":         self.steps,
        }
