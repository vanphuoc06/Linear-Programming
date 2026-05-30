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

    # 1. Tên biến gốc
    actual_vars = [f"x{j+1}" for j in range(n)]
    var_mapping = {v: [(v, Fraction(1))] for v in actual_vars}
    var_consts  = {v: Fraction(0) for v in actual_vars}

    # 2. Hàm mục tiêu — QHTT giải MIN, nếu max thì đảo dấu
    c_raw = [_frac(ci) for ci in c_orig]
    if is_max:
        c_arr = [-ci for ci in c_raw]
    else:
        c_arr = list(c_raw)

    # 3. Ràng buộc chính
    A = []
    b = []

    for con in constraints:
        a_row = [_frac(ai) for ai in con["coeffs"]]
        rhs   = _frac(con["rhs"])
        t     = con["type"]

        if t == "<=":
            A.append(list(a_row))
            b.append(rhs)
        elif t == ">=":
            # Nhân -1: ax >= b  <=>  -ax <= -b
            A.append([-ai for ai in a_row])
            b.append(-rhs)
        elif t == "=":
            # Tách thành 2 ràng buộc <=
            A.append(list(a_row))
            b.append(rhs)
            A.append([-ai for ai in a_row])
            b.append(-rhs)

    # 4. Bounds (ngoài [0, None] mặc định)
    if bounds:
        for j, bnd in enumerate(bounds):
            lo, hi = bnd[0], bnd[1]
            # lo != 0 hoặc lo is None → thêm ràng buộc
            if lo is not None and lo != 0:
                # x_{j+1} >= lo  <=>  -x_{j+1} <= -lo
                row = [Fraction(0)] * n
                row[j] = Fraction(-1)
                A.append(row)
                b.append(-_frac(lo))
            if hi is not None:
                # x_{j+1} <= hi
                row = [Fraction(0)] * n
                row[j] = Fraction(1)
                A.append(row)
                b.append(_frac(hi))

    return c_arr, A, b, actual_vars, var_mapping, var_consts, is_max


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
        c_arr, A, b, actual_vars, var_mapping, var_consts, is_max = \
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
                original_vars=actual_vars,
                force_two_phase=force_two_phase,
                var_consts=var_consts,
                zeta_offset=Fraction(0)
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

        # Bước text (dùng từng dòng làm step)
        self.steps = self._build_steps(full_text)

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

    def _build_steps(self, text: str):
        """Chuyển output text của QHTT thành list steps."""
        steps = []
        lines = text.split("\n")
        current_block = []

        for line in lines:
            if line.strip() == "" and current_block:
                steps.append({"note": "\n".join(current_block)})
                current_block = []
            else:
                current_block.append(line)

        if current_block:
            steps.append({"note": "\n".join(current_block)})

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
