import math
from fractions import Fraction
from solver import SimplexSolver

def fraction_lcm(f1, f2):
    a = abs(f1.numerator)
    b = f1.denominator
    c = abs(f2.numerator)
    d = f2.denominator
    if a == 0 or c == 0:
        return Fraction(0)
    num = math.lcm(a, c)
    den = math.gcd(b, d)
    return Fraction(num, den)

class GraphicalSolver:
    """
    Giải bài toán Quy hoạch Tuyến tính bằng phương pháp Hình học (chỉ dành cho 2 biến).
    Sử dụng SimplexSolver (2-pha) làm lõi để xác định trạng thái và nghiệm tối ưu chính xác.
    Đồng thời tính toán các tọa độ đỉnh (vertices) và miền nghiệm để Frontend render.
    """
    def __init__(self, c, constraints, objective="max", bounds=None, method="graphical"):
        self.c = c
        self.constraints = constraints
        self.objective = objective
        self.bounds = bounds
        self.status = None
        self.optimal_value = None
        self.solution = {}
        self.steps = []

    def solve(self):
        # 1. Dùng Đơn hình 2 Pha để lấy nghiệm toán học chuẩn xác
        simplex = SimplexSolver(
            c=self.c,
            constraints=self.constraints,
            objective=self.objective,
            bounds=self.bounds,
            method="two-phase"
        )
        try:
            simplex_res = simplex.solve()
            self.status = simplex_res["status"]
            self.optimal_value = simplex_res["optimal_value"]
            self.solution = simplex_res["solution"]
        except Exception as e:
            return {"status": "error", "message": str(e), "optimal_value": None, "solution": {}, "steps": []}

        # 2. Xây dựng mô hình hình học
        flat_constraints = []
        for con in self.constraints:
            flat_constraints.append({
                "a": float(con["coeffs"][0]),
                "b": float(con["coeffs"][1]),
                "type": con["type"],
                "rhs": float(con["rhs"]),
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
                    
                    # Kiểm tra tính khả thi của giao điểm đối với tất cả ràng buộc
                    feasible = True
                    for k in range(n_c):
                        ck = flat_constraints[k]
                        val = ck["a"] * x1 + ck["b"] * x2
                        if ck["type"] == "<=" and val > ck["rhs"] + 1e-7:
                            feasible = False
                            break
                        elif ck["type"] == ">=" and val < ck["rhs"] - 1e-7:
                            feasible = False
                            break
                        elif ck["type"] == "=" and abs(val - ck["rhs"]) > 1e-7:
                            feasible = False
                            break
                            
                    if feasible:
                        # Tránh trùng lặp đỉnh
                        if not any(abs(v["x1"] - x1) < 1e-7 and abs(v["x2"] - x2) < 1e-7 for v in vertices):
                            vertices.append({
                                "x1": x1,
                                "x2": x2,
                                "intersect_of": [i, j]
                            })
                            
        # Đặt tên các đỉnh O, A, B, C...
        names = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        name_idx = 0
        for v in vertices:
            if abs(v["x1"]) < 1e-7 and abs(v["x2"]) < 1e-7:
                v["name"] = "O"
            else:
                v["name"] = names[name_idx % len(names)]
                name_idx += 1

        # 4. Xác định thông điệp kết luận
        message = ""
        if self.status == "optimal":
            message = f"Bài toán có nghiệm duy nhất tại x₁ = {self.solution.get('x1', '0')}, x₂ = {self.solution.get('x2', '0')} với Z = {self.optimal_value}."
        elif self.status == "multiple":
            message = f"Bài toán có vô số nghiệm. Giá trị tối ưu Z = {self.optimal_value}."
        elif self.status == "infeasible":
            message = "Theo phương pháp hình học, miền chấp nhận được là rỗng (Vô nghiệm)."
        elif self.status == "unbounded":
            message = "Bài toán không giới nội, hàm mục tiêu tiến tới cực trị vô hạn."
            
        # 5. Hàm mục tiêu (để vẽ đường trượt)
        c1, c2 = self.c
        try:
            f1, f2 = Fraction(str(c1)), Fraction(str(c2))
            lcm_val = float(fraction_lcm(f1, f2))
            if lcm_val == 0:
                lcm_val = max(abs(c1), abs(c2)) if max(abs(c1), abs(c2)) > 0 else 1.0
        except:
            lcm_val = max(abs(c1), abs(c2)) if max(abs(c1), abs(c2)) > 0 else 1.0

        # Tính Bounding Box (khung vẽ đồ thị)
        box_points = [(v["x1"], v["x2"]) for v in vertices]
        for ck in flat_constraints:
            a, b, rhs = ck["a"], ck["b"], ck["rhs"]
            if abs(a) > 1e-7:
                x_int = rhs / a
                if -25 <= x_int <= 25: box_points.append((x_int, 0))
            if abs(b) > 1e-7:
                y_int = rhs / b
                if -25 <= y_int <= 25: box_points.append((0, y_int))
                
        if not box_points:
            box_points = [(0, 0), (10, 10)]
            
        xs = [p[0] for p in box_points]
        ys = [p[1] for p in box_points]
        pad_x = max(3.0, 0.3 * (max(xs) - min(xs)))
        pad_y = max(3.0, 0.3 * (max(ys) - min(ys)))

        bounding_box = {
            "x_min": min(xs) - pad_x,
            "x_max": max(xs) + pad_x,
            "y_min": min(ys) - pad_y,
            "y_max": max(ys) + pad_y
        }

        # Step cuối hiển thị riêng dữ liệu hình học
        step = {
            "phase": "graphical",
            "note": "Biểu diễn hình học (tìm giao điểm các ràng buộc và trượt đường mức).",
            "vertices": vertices,
            "constraints": flat_constraints,
            "objective_line": {"c1": float(c1), "c2": float(c2), "lcm": lcm_val, "objective": self.objective},
            "bounding_box": bounding_box
        }
        self.steps.append(step)

        return {
            "status": self.status,
            "message": message,
            "optimal_value": self.optimal_value,
            "solution": self.solution,
            "steps": self.steps
        }
