"""
solver_compat.py — Adapter JSON → QHTT pipeline.

Chuyển đổi input dạng JSON (api/) → text bài toán → gọi pipeline QHTT
(parse_problem → giai_hai_pha → in_ket_luan → giai_phuong_phap_hinh_hoc)
y hệt như gui_server.py làm.

Đây là cách duy nhất đảm bảo 100% các trường hợp (>=, =, x<=0, x free,
cycling, two-phase auto-select, ...) được xử lý đúng giống QHTT mẫu.
"""

import os
import sys
import contextlib
from io import StringIO
from fractions import Fraction

# Đảm bảo import được các module QHTT (khi chạy từ bất kỳ thư mục nào)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from tien_ich import parse_problem, format_fraction, to_subscript
from phuong_phap_hai_pha import giai_hai_pha
from phuong_phap_hinh_hoc import giai_phuong_phap_hinh_hoc, LAST_PLOT_DATA


# ─── Context manager bắt stdout ──────────────────────────────────────────────

@contextlib.contextmanager
def _capture_stdout():
    old = sys.stdout
    sys.stdout = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = old


# ─── Hàm chuyển JSON → text bài toán ─────────────────────────────────────────

def _json_to_problem_text(c, constraints, objective, bounds=None):
    """
    Chuyển input JSON (giống api/) sang chuỗi bài toán text mà parse_problem() hiểu.

    Ví dụ output:
        max 3x1 + 2x2
        x1 + x2 <= 4
        x1 + 3x2 <= 6
        x1 >= 0
        x2 <= 0
    """
    n = len(c)

    # 1. Hàm mục tiêu
    obj_terms = []
    for j, cj in enumerate(c):
        frac = Fraction(cj).limit_denominator(10**9)
        if frac == 0:
            continue
        var = f"x{j+1}"
        if frac == 1:
            obj_terms.append(f"+{var}" if obj_terms else var)
        elif frac == -1:
            obj_terms.append(f"-{var}")
        else:
            coeff_str = format_fraction(frac)
            if obj_terms:
                obj_terms.append(f"+{coeff_str}{var}" if frac > 0 else f"{coeff_str}{var}")
            else:
                obj_terms.append(f"{coeff_str}{var}")

    # Làm sạch dấu +- đầu
    obj_str = " ".join(obj_terms).replace("+-", "-").replace("+ -", "- ").replace("+ +", "+")
    lines = [f"{objective} {obj_str}"]

    # 2. Ràng buộc chính
    for con in constraints:
        coeffs = con["coeffs"]
        t = con["type"]
        rhs = con["rhs"]

        term_parts = []
        for j, aij in enumerate(coeffs):
            frac = Fraction(aij).limit_denominator(10**9)
            if frac == 0:
                continue
            var = f"x{j+1}"
            if frac == 1:
                term_parts.append(f"+{var}" if term_parts else var)
            elif frac == -1:
                term_parts.append(f"-{var}")
            else:
                coeff_str = format_fraction(frac)
                if term_parts:
                    term_parts.append(f"+{coeff_str}{var}" if frac > 0 else f"{coeff_str}{var}")
                else:
                    term_parts.append(f"{coeff_str}{var}")

        lhs = " ".join(term_parts).replace("+-", "-").replace("+ -", "- ")
        rhs_str = format_fraction(Fraction(rhs).limit_denominator(10**9))
        lines.append(f"{lhs} {t} {rhs_str}")

    # 3. Ràng buộc dấu biến (bounds)
    bounds_list = bounds if bounds else [[0, None] for _ in range(n)]
    for j in range(n):
        lo, hi = bounds_list[j][0], bounds_list[j][1]
        var = f"x{j+1}"

        # x_j >= lo
        if lo is None and hi is None:
            # Biến tự do: không ghi ràng buộc dấu → parse_problem hiểu là free
            pass
        elif lo is None:
            # x_j <= hi (có thể âm)
            if hi == 0:
                lines.append(f"{var} <= 0")
            else:
                lines.append(f"{var} <= {format_fraction(Fraction(hi).limit_denominator(10**9))}")
        elif hi is None:
            if lo == 0:
                lines.append(f"{var} >= 0")
            else:
                lines.append(f"{var} >= {format_fraction(Fraction(lo).limit_denominator(10**9))}")
        else:
            # Cả lo và hi đều có
            if lo == 0:
                lines.append(f"{var} >= 0")
            else:
                lines.append(f"{var} >= {format_fraction(Fraction(lo).limit_denominator(10**9))}")
            lines.append(f"{var} <= {format_fraction(Fraction(hi).limit_denominator(10**9))}")

    return "\n".join(lines)


# ─── SimplexSolverCompat ─────────────────────────────────────────────────────

class SimplexSolverCompat:
    """
    Adapter tương thích với api/solver.py SimplexSolver.

    Nhận JSON input giống api/, chuyển sang text, gọi đúng pipeline QHTT
    (parse_problem → giai_hai_pha) y hệt gui_server.py.

    Hỗ trợ đầy đủ:
      - method: "standard", "bland", "two-phase"
      - bounds: x_i <= 0, x_i tự do, x_i >= lo, x_i trong [lo, hi]
      - ràng buộc: <=, >=, =
      - tự động chuyển two-phase khi b_i < 0
      - tự động dùng bland khi b_i = 0
      - tự động retry bland khi cycling
    """

    def __init__(self, c, constraints, objective="max", bounds=None, method="standard"):
        self.c = c
        self.constraints = constraints
        self.objective = objective
        self.bounds = bounds
        self.method = method

        self.status = None
        self.optimal_value = None
        self.solution = {}
        self.steps = []

    def solve(self) -> dict:
        """Giải bài toán, trả về dict tương thích api/solver.py."""
        # Chuyển JSON → text
        problem_text = _json_to_problem_text(
            self.c, self.constraints, self.objective, self.bounds
        )

        # Gọi parse_problem y hệt gui_server.py
        try:
            (c_arr, A, b, var_names, var_mapping, is_max,
             actual_vars, var_consts, zeta_offset,
             orig_obj_terms, orig_parsed_constraints) = parse_problem(problem_text)
        except Exception as e:
            self.status = "error"
            return self._result(f"Lỗi phân tích bài toán: {e}")

        # Chọn method y hệt gui_server.py (dòng 188–459)
        has_negative_b = any(val < 0 for val in b)
        has_zero_b = any(val == 0 for val in b)

        # Map method từ api → QHTT
        api_to_qhtt = {
            "standard": "simplex",
            "bland": "bland",
            "two-phase": "two_phase",
        }
        req_method_qhtt = api_to_qhtt.get(self.method, "simplex")

        # Auto-upgrade giống gui_server.py dòng 455-459
        if req_method_qhtt in ("simplex", "bland") and has_negative_b:
            req_method_qhtt = "two_phase"
        # Auto-bland khi suy biến (chỉ ở auto mode)
        elif req_method_qhtt == "simplex" and has_zero_b:
            req_method_qhtt = "bland"

        force_two_phase = (req_method_qhtt == "two_phase")
        method_for_call = "simplex" if req_method_qhtt == "two_phase" else req_method_qhtt

        # Giải và bắt output text (y hệt gui_server.py)
        solver_status_str = "Optimal"
        solver_obj = None
        full_text = ""

        with _capture_stdout() as cap:
            try:
                res, solver_obj = giai_hai_pha(
                    c_arr, A, b, actual_vars, var_mapping,
                    verbose=True,
                    method=method_for_call,
                    is_max=is_max,
                    original_vars=var_names,
                    force_two_phase=force_two_phase,
                    var_consts=var_consts,
                    zeta_offset=zeta_offset,
                )
                if res not in ("Infeasible", "Cycling") and solver_obj is not None:
                    solver_obj.in_ket_luan(is_max)
                solver_status_str = res

                # Auto-retry bland khi cycling (giống gui_server.py dòng 478-490)
                if res == "Cycling" and req_method_qhtt == "simplex":
                    print("\n" + "=" * 50)
                    print("[!] CẢNH BÁO: Phát hiện xoay vòng vô hạn (Cycling)!")
                    print("Hệ thống tự động giải lại bằng Quy tắc Bland...")
                    print("=" * 50 + "\n")
                    res2, solver2 = giai_hai_pha(
                        c_arr, A, b, actual_vars, var_mapping,
                        verbose=True,
                        method="bland",
                        is_max=is_max,
                        original_vars=var_names,
                        var_consts=var_consts,
                        zeta_offset=zeta_offset,
                    )
                    if res2 not in ("Infeasible", "Cycling") and solver2 is not None:
                        solver2.in_ket_luan(is_max)
                    res, solver_obj = res2, solver2
                    solver_status_str = "Bland (Cycling Resolved)"

            except Exception as e:
                self.status = "error"
                full_text = cap.getvalue()
                self.steps = [{"note": full_text}] if full_text else []
                return self._result(f"Lỗi giải toán: {e}")

        full_text = cap.getvalue()

        # Ánh xạ trạng thái
        status_map = {
            "Optimal": "optimal",
            "Infeasible": "infeasible",
            "Unbounded": "unbounded",
            "Cycling": "cycling",
            "LimitReached": "cycling",
            "Bland (Cycling Resolved)": "optimal",
        }
        self.status = status_map.get(solver_status_str, "optimal")

        # Trích nghiệm
        if solver_obj is not None and res == "Optimal":
            self._extract_solution(solver_obj, is_max, var_names, var_mapping, var_consts)
            # Kiểm tra vô số nghiệm
            if any(v == Fraction(0) for v in solver_obj.c):
                self.status = "multiple"

        # Tạo steps từ text
        self.steps = self._build_steps(full_text, len(self.c))

        msg = self._make_message(res, is_max)
        return self._result(msg)

    def get_standard_form(self) -> dict:
        """Trả về bài toán dạng chuẩn (min, tất cả <=, biến >= 0)."""
        problem_text = _json_to_problem_text(
            self.c, self.constraints, self.objective, self.bounds
        )
        try:
            (c_arr, A, b, var_names, var_mapping, is_max,
             actual_vars, var_consts, zeta_offset,
             orig_obj_terms, orig_parsed_constraints) = parse_problem(problem_text)
        except Exception:
            return {"objective": "min", "c": list(self.c), "constraints": [], "variables": []}

        c_std = [float(v) for v in c_arr]
        cons_std = []
        for i in range(len(A)):
            cons_std.append({
                "coeffs": [float(v) for v in A[i]],
                "type": "<=",
                "rhs": float(b[i]),
            })
        return {
            "objective": "min",
            "c": c_std,
            "constraints": cons_std,
            "variables": actual_vars,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _extract_solution(self, solver_obj, is_max: bool, var_names, var_mapping, var_consts):
        """Trích nghiệm về biến gốc (xử lý phép thế x_i=y_i+offset, x_i=-y_i, v.v.)."""
        n = len(self.c)

        # Giá trị tối ưu
        raw_zeta = solver_obj.zeta
        if is_max:
            opt = -raw_zeta
        else:
            opt = raw_zeta
        self.optimal_value = format_fraction(opt)

        # Giá trị biến nội bộ (actual_vars sau thế)
        internal_vals = {}
        for vname in solver_obj.basic_vars:
            idx = solver_obj.basic_vars.index(vname)
            internal_vals[vname] = solver_obj.b[idx]

        # Truy ngược về biến gốc x1..xn
        for j, orig_var in enumerate(var_names):
            mapping = var_mapping.get(orig_var, [(orig_var, Fraction(1))])
            const_offset = var_consts.get(orig_var, Fraction(0))
            val = const_offset
            for new_v, mult in mapping:
                inner = internal_vals.get(new_v, Fraction(0))
                val += mult * inner
            self.solution[f"x{j+1}"] = format_fraction(val)

    def _build_steps(self, text: str, n_vars: int) -> list:
        """Chuyển output text QHTT thành list steps (với point_coords nếu có bảng đơn hình)."""
        import re

        steps = []
        lines = text.split("\n")
        current_block = []

        def process_block(block_lines):
            block_text = "\n".join(block_lines)
            step_dict = {"note": block_text}

            # Nếu block chứa bảng đơn hình (có đường gạch ngang)
            if "──" in block_text or "=" * 5 in block_text:
                basic_vars_vals = {}
                for line in block_lines:
                    line_clean = line.strip().lstrip("←").strip()
                    # Tìm: "x₁ = 5 - ..." hoặc "w₁ = 3 + ..."
                    m = re.match(
                        r'^([a-zA-Zxyw][₀-₉\d]+)\s*=\s*(-?\s*\d+(?:[.,]\d+)?(?:/\d+)?)',
                        line_clean
                    )
                    if m:
                        var = m.group(1)
                        val_str = m.group(2).replace(" ", "").replace(",", ".")
                        try:
                            basic_vars_vals[var] = float(Fraction(val_str))
                        except Exception:
                            pass

                # Lấy tọa độ x₁..xₙ
                coords = []
                for i in range(1, n_vars + 1):
                    sub = to_subscript(f"x{i}")
                    coords.append(basic_vars_vals.get(sub, 0.0))

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
        z = "zₘₐₓ" if is_max else "zₘᵢₙ"
        if res == "Optimal":
            if self.status == "multiple":
                return (
                    f"Vô số nghiệm tối ưu — tồn tại biến không-cơ-sở "
                    f"có hệ số = 0 trong dòng z ({z} = {self.optimal_value})."
                )
            return (
                f"Nghiệm tối ưu duy nhất — mọi hệ số biến không-cơ-sở "
                f"trong dòng z đều > 0 ({z} = {self.optimal_value})."
            )
        elif res == "Infeasible":
            return "Vô nghiệm — miền chấp nhận được là rỗng."
        elif res == "Unbounded":
            sign = "+∞" if is_max else "-∞"
            return f"Bài toán không giới nội — hàm mục tiêu tiến tới {sign}."
        elif res in ("Cycling", "LimitReached"):
            return "Bài toán bị lặp vòng (Cycling Detected). Vui lòng chuyển sang Quy tắc Bland."
        elif "Bland" in str(res):
            return f"Đã khắc phục xoay vòng bằng Bland — {z} = {self.optimal_value}."
        return f"Trạng thái: {res}"

    def _result(self, message: str) -> dict:
        return {
            "status": self.status,
            "message": message,
            "optimal_value": self.optimal_value,
            "solution": self.solution,
            "steps": self.steps,
        }


# ─── GraphicalSolverCompat ───────────────────────────────────────────────────

class GraphicalSolverCompat:
    """
    Adapter cho bài toán 2 biến, dùng SimplexSolverCompat + phuong_phap_hinh_hoc.
    Trả về đúng format graph_data mà api/main.py cần.
    """

    def __init__(self, c, constraints, objective="max", bounds=None, method="graphical"):
        assert len(c) == 2, "GraphicalSolverCompat chỉ hỗ trợ bài toán 2 biến."
        self.c = c
        self.constraints = constraints
        self.objective = objective
        self.bounds = bounds

        self.status = None
        self.optimal_value = None
        self.solution = {}
        self.steps = []

    def solve(self) -> dict:
        # 1. Dùng SimplexSolverCompat để lấy nghiệm
        simplex = SimplexSolverCompat(
            c=self.c,
            constraints=self.constraints,
            objective=self.objective,
            bounds=self.bounds,
            method="two-phase",
        )
        simplex_res = simplex.solve()
        self.status = simplex_res["status"]
        self.optimal_value = simplex_res["optimal_value"]
        self.solution = simplex_res["solution"]
        self.steps = simplex_res.get("steps", [])

        # 2. Lấy dữ liệu hình học từ phuong_phap_hinh_hoc
        problem_text = _json_to_problem_text(
            self.c, self.constraints, self.objective, self.bounds
        )
        try:
            (c_arr, A, b, var_names, var_mapping, is_max,
             actual_vars, var_consts, zeta_offset, _, _) = parse_problem(problem_text)

            # Tìm solver object để truyền vào hàm hình học
            with _capture_stdout():
                res2, solver_obj = giai_hai_pha(
                    c_arr, A, b, actual_vars, var_mapping,
                    verbose=False,
                    method="simplex",
                    is_max=is_max,
                    original_vars=var_names,
                    force_two_phase=True,
                    var_consts=var_consts,
                    zeta_offset=zeta_offset,
                )

            import phuong_phap_hinh_hoc as _hhoc
            with _capture_stdout():
                giai_phuong_phap_hinh_hoc(problem_text, res2, solver_obj, is_max)

            plot_data = _hhoc.LAST_PLOT_DATA

            if plot_data:
                def _f(v):
                    return float(v) if isinstance(v, Fraction) else v

                formatted_constraints = [
                    {
                        "a": _f(c.get("a", 0)),
                        "b": _f(c.get("b", 0)),
                        "c": _f(c.get("c", 0)),
                        "sign": c.get("sign", "<="),
                        "str": c.get("str", ""),
                        "index": c.get("index", 0),
                    }
                    for c in plot_data.get("parsed_constraints", [])
                ]
                formatted_vertices = [
                    {
                        "x1": _f(v.get("x1", 0)),
                        "x2": _f(v.get("x2", 0)),
                        "x1_str": format_fraction(v.get("x1", 0)),
                        "x2_str": format_fraction(v.get("x2", 0)),
                        "name": v.get("name", ""),
                        "intersect": v.get("intersect", (0, 0)),
                    }
                    for v in plot_data.get("vertices", [])
                ]

                graphical_step = {
                    "phase": "graphical",
                    "note": "Biểu diễn hình học (tìm giao điểm các ràng buộc và trượt đường mức).",
                    "vertices": formatted_vertices,
                    "constraints": formatted_constraints,
                    "objective_line": {
                        "c1": _f(plot_data.get("c1", 0)),
                        "c2": _f(plot_data.get("c2", 0)),
                        "lcm": _f(plot_data.get("lcm_val", 1)),
                        "objective": self.objective,
                    },
                    "bounding_box": self._compute_bounding_box(formatted_vertices),
                }
                self.steps.append(graphical_step)

        except Exception:
            pass

        # 3. Thông điệp
        x1 = self.solution.get("x1", "0")
        x2 = self.solution.get("x2", "0")
        z = self.optimal_value

        if self.status == "optimal":
            message = f"Bài toán có nghiệm tối ưu tại x₁ = {x1}, x₂ = {x2} với Z = {z}."
        elif self.status == "multiple":
            message = f"Bài toán có vô số nghiệm. Giá trị tối ưu Z = {z}."
        elif self.status == "infeasible":
            message = "Theo phương pháp hình học, miền chấp nhận được là rỗng (Vô nghiệm)."
        elif self.status == "unbounded":
            message = "Bài toán không giới nội, hàm mục tiêu tiến tới cực trị vô hạn."
        else:
            message = f"Trạng thái: {self.status}"

        return {
            "status": self.status,
            "message": message,
            "optimal_value": self.optimal_value,
            "solution": self.solution,
            "steps": self.steps,
        }

    def _compute_bounding_box(self, vertices: list) -> dict:
        if not vertices:
            return {"x_min": -1, "x_max": 10, "y_min": -1, "y_max": 10}
        xs = [v["x1"] for v in vertices]
        ys = [v["x2"] for v in vertices]
        pad_x = max(3.0, 0.3 * (max(xs) - min(xs)))
        pad_y = max(3.0, 0.3 * (max(ys) - min(ys)))
        return {
            "x_min": min(xs) - pad_x,
            "x_max": max(xs) + pad_x,
            "y_min": min(ys) - pad_y,
            "y_max": max(ys) + pad_y,
        }
