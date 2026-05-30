"""
main.py — FastAPI application for the LP Solver.
Hỗ trợ chạy local (uvicorn) và deploy Vercel (Mangum ASGI adapter).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from solver import SimplexSolver
from graphical_solver import GraphicalSolver

app = FastAPI(title="LP Solver API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ────────────────────────────────────────────────

class Constraint(BaseModel):
    coeffs: List[float]
    type: str  # "<=", ">=", "="
    rhs: float

class SolveRequest(BaseModel):
    method: str = Field("standard", description="standard | bland | two-phase | graphical")
    objective: str = Field("max", description="max | min")
    c: List[float] = Field(..., description="Objective function coefficients")
    constraints: List[Constraint]
    bounds: Optional[List[List[Optional[float]]]] = None
    show_steps: bool = True


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "ok", "message": "LP Solver API is running."}


@app.post("/api/solve")
def solve(req: SolveRequest):
    # Validate method
    if req.method not in ("standard", "bland", "two-phase", "graphical"):
        raise HTTPException(
            status_code=400,
            detail="method must be 'standard', 'bland', 'two-phase', or 'graphical'.",
        )

    # Validate dimensions
    n = len(req.c)
    for i, con in enumerate(req.constraints):
        if len(con.coeffs) != n:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Ràng buộc {i+1}: số hệ số ({len(con.coeffs)}) "
                    f"không khớp với số biến ({n})."
                ),
            )
        if con.type not in ("<=", ">=", "="):
            raise HTTPException(
                status_code=400,
                detail=f"Loại ràng buộc '{con.type}' không hợp lệ.",
            )

    # Standard / Bland chỉ hỗ trợ <= (không có biến nhân tạo)
    if req.method in ("standard", "bland"):
        for con in req.constraints:
            if con.type in (">=", "="):
                return {
                    "status": "method_error",
                    "message": (
                        "Bài toán chứa ràng buộc ≥ hoặc =. Phương pháp Đơn hình cơ bản / Bland "
                        "yêu cầu tất cả ràng buộc ở dạng ≤. "
                        "Vui lòng chọn phương pháp Two-Phase để giải bài toán này."
                    ),
                    "optimal_value": None,
                    "solution": {},
                    "steps": [],
                }

    constraints_dict = [
        {"coeffs": con.coeffs, "type": con.type, "rhs": con.rhs}
        for con in req.constraints
    ]

    if req.method == "graphical":
        if n != 2:
            raise HTTPException(
                status_code=400,
                detail="Phương pháp hình học (Graphical) chỉ hỗ trợ bài toán có đúng 2 biến.",
            )
        solver = GraphicalSolver(
            c=req.c,
            constraints=constraints_dict,
            objective=req.objective,
            bounds=req.bounds,
            method=req.method,
        )
    else:
        solver = SimplexSolver(
            c=req.c,
            constraints=constraints_dict,
            objective=req.objective,
            bounds=req.bounds,
            method=req.method,
        )

    try:
        result = solver.solve()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi giải: {str(e)}")

    if n == 2 and req.method != "graphical":
        try:
            # Lấy thông tin đồ thị (geometry) để vẽ đường đi của các điểm từ vựng
            gs = GraphicalSolver(
                c=req.c,
                constraints=constraints_dict,
                objective=req.objective,
                bounds=req.bounds,
                method="graphical"
            )
            gs.solve()
            if gs.steps and gs.steps[-1].get("phase") == "graphical":
                graph_step = gs.steps[-1]
                
                # 1. Trích xuất đường đi từ Simplex
                simplex_path = []
                used_names = set()
                
                for step in result.get("steps", []):
                    if "point_coords" in step and "point_str" in step:
                        coords = step["point_coords"]
                        name_str = step["point_str"].split('(')[0]
                        simplex_path.append({
                            "name": name_str,
                            "x1": coords[0],
                            "x2": coords[1]
                        })
                        used_names.add(name_str)
                
                # 2. Đổi tên các đỉnh trong đồ thị cho khớp với Simplex
                vertices = graph_step.get("vertices", [])
                
                for v in vertices:
                    v_matched = False
                    for p in simplex_path:
                        if abs(v["x1"] - p["x1"]) < 1e-5 and abs(v["x2"] - p["x2"]) < 1e-5:
                            v["name"] = p["name"]
                            v_matched = True
                            break
                    if not v_matched:
                        v["name"] = "" 
                        
                available_letters = [chr(i) for i in range(ord('A'), ord('Z')+1) if chr(i) not in used_names and chr(i) != 'O']
                avail_idx = 0
                for v in vertices:
                    if v["name"] == "":
                        if abs(v["x1"]) < 1e-5 and abs(v["x2"]) < 1e-5 and 'O' not in used_names:
                            v["name"] = 'O'
                            used_names.add('O')
                        else:
                            if avail_idx < len(available_letters):
                                v["name"] = available_letters[avail_idx]
                                avail_idx += 1
                            else:
                                v["name"] = "V"
                
                result["graph_data"] = {
                    "vertices": vertices,
                    "constraints": graph_step.get("constraints", []),
                    "objective_line": graph_step.get("objective_line", {}),
                    "bounding_box": graph_step.get("bounding_box", {}),
                    "simplex_path": simplex_path
                }
        except Exception:
            pass

    if not req.show_steps:
        result["steps"] = []

    return result


@app.post("/api/standard-form")
def get_standard_form(req: SolveRequest):
    constraints_dict = [
        {"coeffs": con.coeffs, "type": con.type, "rhs": con.rhs}
        for con in req.constraints
    ]
    solver = SimplexSolver(
        c=req.c,
        constraints=constraints_dict,
        objective=req.objective,
        bounds=req.bounds,
        method=req.method,
    )
    return solver.get_standard_form()


# ─── Vercel Serverless Handler ─────────────────────────────────────────────────
# Mangum wrap FastAPI thành ASGI handler mà Vercel Python runtime hiểu được.
# Khi chạy local bằng uvicorn thì biến `handler` không được dùng tới.
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    # Nếu mangum chưa được cài (môi trường dev local), bỏ qua
    handler = None
