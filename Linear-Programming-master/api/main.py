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

    constraints_dict = [
        {"coeffs": con.coeffs, "type": con.type, "rhs": con.rhs}
        for con in req.constraints
    ]

    # ── Tự động chọn phương pháp phù hợp (giống QHTT gui_server.py dòng 188-459) ──
    effective_method = req.method
    auto_note = None

    if req.method != "graphical":
        # Kiểm tra các điều kiện cần nâng cấp phương pháp
        has_non_le   = any(c.type in (">=", "=") for c in req.constraints)
        has_neg_rhs  = any(c.rhs < 0 for c in req.constraints if c.type == "<=")
        has_zero_rhs = any(c.rhs == 0 for c in req.constraints)

        if req.method in ("standard", "bland"):
            if has_non_le:
                # Bài toán có >= hoặc = → tự nâng cấp (giống QHTT: parse_problem chuyển >= thành <= và gui_server auto-upgrade)
                effective_method = "two-phase"
                auto_note = (
                    "⚠️ Bài toán có ràng buộc ≥ hoặc =. "
                    "Tự động chuyển sang Đơn hình 2 Pha."
                )
            elif has_neg_rhs:
                # b_i < 0 cho ràng buộc <= → tự nâng cấp (giống QHTT dòng 456-459)
                effective_method = "two-phase"
                auto_note = (
                    "⚠️ Bài toán có vế phải âm (b_i < 0). "
                    "Tự động chuyển sang Đơn hình 2 Pha."
                )
            elif has_zero_rhs and req.method == "standard":
                # b_i = 0 (suy biến) → tự dùng Bland (giống QHTT dòng 197-199)
                effective_method = "bland"
                auto_note = (
                    "⚠️ Bài toán có vế phải bằng 0 (có thể suy biến). "
                    "Tự động chuyển sang Quy tắc Bland để tránh xoay vòng."
                )

    if effective_method == "graphical":
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
            method=effective_method,
        )
    else:
        solver = SimplexSolver(
            c=req.c,
            constraints=constraints_dict,
            objective=req.objective,
            bounds=req.bounds,
            method=effective_method,
        )

    try:
        result = solver.solve()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi giải: {str(e)}")

    # Đính kèm ghi chú auto-upgrade vào thông báo
    if auto_note:
        result["message"] = auto_note + " | " + (result.get("message") or "")
        result["auto_upgraded_method"] = effective_method

    # ── Tự động retry bằng Bland khi Cycling (giống QHTT dòng 478-490) ──
    if result.get("status") == "cycling" and effective_method in ("standard", "two-phase"):
        try:
            solver_bland = SimplexSolver(
                c=req.c,
                constraints=constraints_dict,
                objective=req.objective,
                bounds=req.bounds,
                method="bland",
            )
            result_bland = solver_bland.solve()
            if result_bland.get("status") != "cycling":
                result = result_bland
                result["message"] = (
                    "[Tự động Bland — đã khắc phục xoay vòng] "
                    + (result_bland.get("message") or "")
                )
                result["auto_upgraded_method"] = "bland"
        except Exception:
            pass  # Giữ kết quả cycling gốc nếu Bland cũng lỗi

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
