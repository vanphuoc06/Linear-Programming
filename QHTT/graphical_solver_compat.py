"""
graphical_solver_compat.py — Lớp tương thích (Compatibility Layer) cho api/graphical_solver.py.

Cung cấp class GraphicalSolverCompat với interface giống hệt GraphicalSolver trong
api/graphical_solver.py, nhưng sử dụng lõi thuật toán của QHTT
(giai_hai_pha + giai_phuong_phap_hinh_hoc + tien_ich).

Mục tiêu:
  - Không sửa bất kỳ file gốc nào trong QHTT/
  - Cho phép các hệ thống dùng JSON input/output gọi vào lõi QHTT
  - Chỉ dành cho bài toán 2 biến (x1, x2)

Input  (giống api/graphical_solver.py):
    c           : List[float]       — hệ số hàm mục tiêu [c1, c2]
    constraints : List[dict]        — [{"coeffs": [a,b], "type": "<=|>=|=", "rhs": r}, ...]
    objective   : "max" | "min"
    bounds      : Optional[...]]

Output (giống api/graphical_solver.py):
    {
        "status":        "optimal" | "infeasible" | "unbounded" | "multiple",
        "message":       str,
        "optimal_value": str | None,
        "solution":      dict,   # {"x1": "...", "x2": "..."}
        "steps":         list    # bao gồm step "graphical" cuối cùng
    }
"""

import sys
import os
import math
import contextlib
from io import StringIO
from fractions import Fraction

# Đảm bảo import được các module QHTT
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from tien_ich import format_fraction
from solver_compat import SimplexSolverCompat, _capture_stdout


# ─── Hàm tiện ích ────────────────────────────────────────────────────────────

def _fraction_lcm(f1: Fraction, f2: Fraction) -> Fraction:
    """Tính LCM của hai phân số: LCM(a/b, c/d) = LCM(a,c) / GCD(b,d)."""
    a = abs(f1.numerator)
    b = f1.denominator
    c = abs(f2.numerator)
    d = f2.denominator
    if a == 0 or c == 0:
        return Fraction(0)
    num = math.lcm(a, c)
    den = math.gcd(b, d)
    return Fraction(num, den)


# ─── GraphicalSolverCompat ───────────────────────────────────────────────────

class GraphicalSolverCompat:
    """
    Lớp tương thích với api/graphical_solver.py GraphicalSolver.

    Sử dụng lõi QHTT (SimplexSolverCompat cho nghiệm chính xác,
    giai_phuong_phap_hinh_hoc cho tọa độ đỉnh/đồ thị) nhưng nhận/trả về
    cùng format JSON như GraphicalSolver gốc trong api/.

    Chỉ hỗ trợ bài toán có đúng 2 biến (n = 2).
    """

    def __init__(self, c, constraints, objective="max", bounds=None, method="graphical"):
        assert len(c) == 2, "GraphicalSolverCompat chỉ hỗ trợ bài toán 2 biến."
        self.c           = c
        self.constraints = constraints
        self.objective   = objective
        self.bounds      = bounds

        self.status        = None
        self.optimal_value = None
        self.solution      = {}
        self.steps         = []

    # ── Public ───────────────────────────────────────────────────────────────

    def solve(self) -> dict:
        """Giải bài toán và trả về dict tương thích api/graphical_solver.py."""

        # 1. Dùng SimplexSolverCompat (two-phase) để lấy nghiệm chính xác
        simplex = SimplexSolverCompat(
            c=self.c,
            constraints=self.constraints,
            objective=self.objective,
            bounds=self.bounds,
            method="two-phase"
        )
        try:
            simplex_res    = simplex.solve()
            self.status    = simplex_res["status"]
            self.optimal_value = simplex_res["optimal_value"]
            self.solution  = simplex_res["solution"]
            # Cũng lưu các bước text từ simplex
            self.steps     = simplex_res.get("steps", [])
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "optimal_value": None,
                "solution": {},
                "steps": []
            }

        # 2. Xây dựng danh sách constraints phẳng (flat) cho hình học
        flat_constraints = []
        for con in self.constraints:
            flat_constraints.append({
                "a":        float(con["coeffs"][0]),
                "b":        float(con["coeffs"][1]),
                "type":     con["type"],
                "rhs":      float(con["rhs"]),
                "is_bound": False
            })

        bounds = self.bounds if self.bounds else [[0, None], [0, None]]
        # Ràng buộc dấu x1
        if bounds[0][0] is not None:
            flat_constraints.append({"a": 1.0, "b": 0.0, "type": ">=", "rhs": float(bounds[0][0]), "is_bound": True})
        if bounds[0][1] is not None:
            flat_constraints.append({"a": 1.0, "b": 0.0, "type": "<=", "rhs": float(bounds[0][1]), "is_bound": True})
        # Ràng buộc dấu x2
        if bounds[1][0] is not None:
            flat_constraints.append({"a": 0.0, "b": 1.0, "type": ">=", "rhs": float(bounds[1][0]), "is_bound": True})
        if bounds[1][1] is not None:
            flat_constraints.append({"a": 0.0, "b": 1.0, "type": "<=", "rhs": float(bounds[1][1]), "is_bound": True})

        # 3. Tìm giao điểm các đường thẳng (vertices)
        vertices = self._find_vertices(flat_constraints)

        # 4. Đặt tên đỉnh O, A, B, C...
        names     = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        name_idx  = 0
        for v in vertices:
            if abs(v["x1"]) < 1e-7 and abs(v["x2"]) < 1e-7:
                v["name"] = "O"
            else:
                v["name"] = names[name_idx % len(names)]
                name_idx += 1

        # 5. Thông điệp kết luận
        message = self._make_message(vertices)

        # 6. Hàm mục tiêu (để vẽ đường trượt)
        c1_val, c2_val = self.c[0], self.c[1]
        try:
            f1       = Fraction(str(c1_val))
            f2       = Fraction(str(c2_val))
            lcm_val  = float(_fraction_lcm(f1, f2))
            if lcm_val == 0:
                lcm_val = max(abs(c1_val), abs(c2_val)) if max(abs(c1_val), abs(c2_val)) > 0 else 1.0
        except Exception:
            lcm_val = max(abs(c1_val), abs(c2_val)) if max(abs(c1_val), abs(c2_val)) > 0 else 1.0

        # 7. Tính bounding box
        bounding_box = self._compute_bounding_box(vertices, flat_constraints)

        # 8. Step cuối cùng dạng "graphical" — giống api/graphical_solver.py
        graphical_step = {
            "phase":            "graphical",
            "note":             "Biểu diễn hình học (tìm giao điểm các ràng buộc và trượt đường mức).",
            "vertices":         vertices,
            "constraints":      flat_constraints,
            "objective_line":   {
                "c1":        float(c1_val),
                "c2":        float(c2_val),
                "lcm":       lcm_val,
                "objective": self.objective
            },
            "bounding_box":     bounding_box
        }
        self.steps.append(graphical_step)

        return {
            "status":        self.status,
            "message":       message,
            "optimal_value": self.optimal_value,
            "solution":      self.solution,
            "steps":         self.steps,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _find_vertices(self, flat_constraints: list) -> list:
        """Tìm tất cả đỉnh giao điểm khả thi của các cặp ràng buộc."""
        vertices = []
        n_c = len(flat_constraints)

        for i in range(n_c):
            for j in range(i + 1, n_c):
                c1 = flat_constraints[i]
                c2 = flat_constraints[j]

                det = c1["a"] * c2["b"] - c1["b"] * c2["a"]
                if abs(det) > 1e-9:
                    x1 = (c1["rhs"] * c2["b"] - c1["b"] * c2["rhs"]) / det
                    x2 = (c1["a"] * c2["rhs"] - c1["rhs"] * c2["a"]) / det

                    # Kiểm tra khả thi với tất cả ràng buộc
                    feasible = True
                    for k in range(n_c):
                        ck  = flat_constraints[k]
                        val = ck["a"] * x1 + ck["b"] * x2
                        if ck["type"] == "<=" and val > ck["rhs"] + 1e-7:
                            feasible = False; break
                        elif ck["type"] == ">=" and val < ck["rhs"] - 1e-7:
                            feasible = False; break
                        elif ck["type"] == "=" and abs(val - ck["rhs"]) > 1e-7:
                            feasible = False; break

                    if feasible:
                        # Tránh trùng lặp đỉnh
                        if not any(
                            abs(v["x1"] - x1) < 1e-7 and abs(v["x2"] - x2) < 1e-7
                            for v in vertices
                        ):
                            vertices.append({
                                "x1":          x1,
                                "x2":          x2,
                                "intersect_of": [i, j]
                            })

        return vertices

    def _compute_bounding_box(self, vertices: list, flat_constraints: list) -> dict:
        """Tính khung vẽ đồ thị (bounding box)."""
        box_points = [(v["x1"], v["x2"]) for v in vertices]

        for ck in flat_constraints:
            a, b, rhs = ck["a"], ck["b"], ck["rhs"]
            if abs(a) > 1e-7:
                x_int = rhs / a
                if -25 <= x_int <= 25:
                    box_points.append((x_int, 0))
            if abs(b) > 1e-7:
                y_int = rhs / b
                if -25 <= y_int <= 25:
                    box_points.append((0, y_int))

        if not box_points:
            box_points = [(0, 0), (10, 10)]

        xs    = [p[0] for p in box_points]
        ys    = [p[1] for p in box_points]
        pad_x = max(3.0, 0.3 * (max(xs) - min(xs)))
        pad_y = max(3.0, 0.3 * (max(ys) - min(ys)))

        return {
            "x_min": min(xs) - pad_x,
            "x_max": max(xs) + pad_x,
            "y_min": min(ys) - pad_y,
            "y_max": max(ys) + pad_y
        }

    def _make_message(self, vertices: list) -> str:
        """Tạo thông điệp kết luận theo từng trạng thái."""
        x1_val = self.solution.get("x1", "0")
        x2_val = self.solution.get("x2", "0")
        z_val  = self.optimal_value

        if self.status == "optimal":
            return (
                f"Bài toán có nghiệm duy nhất tại x₁ = {x1_val}, x₂ = {x2_val} "
                f"với Z = {z_val}."
            )
        elif self.status == "multiple":
            return f"Bài toán có vô số nghiệm. Giá trị tối ưu Z = {z_val}."
        elif self.status == "infeasible":
            return "Theo phương pháp hình học, miền chấp nhận được là rỗng (Vô nghiệm)."
        elif self.status == "unbounded":
            return "Bài toán không giới nội, hàm mục tiêu tiến tới cực trị vô hạn."
        return f"Trạng thái: {self.status}"
