import os
import sys
import contextlib
import shutil
import tempfile
import re
import base64
from io import StringIO
from fractions import Fraction
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --- PyInstaller compatibility ---
# Khi chạy dưới dạng frozen exe, các file tĩnh nằm trong sys._MEIPASS
# Khi chạy bình thường (python), dùng thư mục chứa file này
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS          # thư mục temp chứa file bundle
    WORK_DIR = os.path.dirname(sys.executable)  # thư mục chứa exe (ghi được)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    WORK_DIR = BASE_DIR

GRAPH_PATH = os.path.join(tempfile.gettempdir(), 'qhtt_do_thi.png')
GUI_DIR = os.path.join(BASE_DIR, 'gui')

# Tự động đồng bộ bg.jpg từ thư mục chính sang thư mục gui/bg.jpg để phục vụ tĩnh
try:
    src_bg = os.path.join(WORK_DIR, 'bg.jpg')
    dst_bg = os.path.join(GUI_DIR, 'bg.jpg')
    if os.path.exists(src_bg):
        # Đảm bảo thư mục đích có sẵn
        os.makedirs(GUI_DIR, exist_ok=True)
        # Chỉ copy nếu file nguồn khác biệt hoặc chưa tồn tại ở đích
        if not os.path.exists(dst_bg) or os.path.getmtime(src_bg) > os.path.getmtime(dst_bg):
            shutil.copy2(src_bg, dst_bg)
            print(f"[*] Da dong bo anh nen: {src_bg} -> {dst_bg}")
except Exception as e:
    print(f"[!] Khong the tu dong copy bg.jpg: {e}")

def normalize_ocr_text(lines):
    # Ghép các dòng kết quả thành chuỗi văn bản toán học chuẩn hóa
    cleaned_lines = []
    
    for line in lines:
        s = line.strip()
        if not s:
            continue
            
        # Loại bỏ các khoảng trắng thừa giữa chữ và số của biến (ví dụ: 'x 1' -> 'x1', 'x _ 1' -> 'x1')
        s = re.sub(r'x\s*[_]*\s*([0-9]+)', r'x\1', s, flags=re.IGNORECASE)
        
        # Loại bỏ các khoảng trắng thừa giữa các ký hiệu bất đẳng thức (ví dụ: '< =' -> '<=')
        s = re.sub(r'<\s*=\s*', r'<=', s)
        s = re.sub(r'>\s*=\s*', r'>=', s)
        s = re.sub(r'=\s*=\s*', r'=', s)
        s = re.sub(r'\s*-\s*', r' - ', s)
        s = re.sub(r'\s*\+\s*', r' + ', s)
        s = re.sub(r'\s*<=\s*', r' <= ', s)
        s = re.sub(r'\s*>=\s*', r' >= ', s)
        s = re.sub(r'(?<![<>])\s*=\s*', r' = ', s)
        
        # Chuẩn hóa chữ thường của biến
        s = s.lower()
        
        # Loại bỏ khoảng trắng kép thừa
        s = re.sub(r'\s+', r' ', s).strip()
        
        # Sửa các từ mục tiêu 'minimize', 'maximize', 'min z =', 'max z =' -> 'min', 'max'
        s = re.sub(r'^(minimize|min\s*z\s*=)', 'min', s, flags=re.IGNORECASE)
        s = re.sub(r'^(maximize|max\s*z\s*=)', 'max', s, flags=re.IGNORECASE)
        
        cleaned_lines.append(s)
        
    return '\n'.join(cleaned_lines)

# Import các hàm giải toán có sẵn của dự án
from tien_ich import parse_problem, print_standard_form, to_subscript, format_fraction
from phuong_phap_hai_pha import giai_hai_pha
from phuong_phap_hinh_hoc import giai_phuong_phap_hinh_hoc

app = FastAPI(
    title="QHTT Solver Backend API",
    description="API Server kết nối giao diện React với bộ giải Quy hoạch tuyến tính Python",
    version="1.0.0"
)

# Cấu hình CORS để cho phép frontend gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import Optional

# Model định nghĩa dữ liệu gửi lên từ Frontend
class SolveRequest(BaseModel):
    problem: str
    method: Optional[str] = None

class OcrRequest(BaseModel):
    image: str
    apiKey: str = ""

class RedrawRequest(BaseModel):
    xmin: float
    xmax: float
    ymin: float
    ymax: float

# Context manager để bắt đầu ra terminal (sys.stdout)
@contextlib.contextmanager
def capture_stdout():
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = old_stdout

def deduplicate_problem_input(problem_input):
    import re
    sub_map = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    
    lines = problem_input.strip().split('\n')
    unique_lines = []
    seen_normalized = set()
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        if "<=" not in line_stripped and ">=" not in line_stripped and "=" not in line_stripped:
            unique_lines.append(line_stripped)
            continue
            
        norm = line_stripped.translate(sub_map)
        norm = re.sub(r'\s+', '', norm)
        norm = norm.replace(';', ',').lower()
        
        if norm in seen_normalized:
            continue
            
        seen_normalized.add(norm)
        unique_lines.append(line_stripped)
        
    return '\n'.join(unique_lines)

def format_expr(terms):
    from tien_ich import format_fraction, to_subscript
    if not terms: return "0"
    res = []
    for coeff, v in terms:
        if coeff == 0: continue
        term_str = to_subscript(v) if abs(coeff) == 1 else f"{format_fraction(abs(coeff))}{to_subscript(v)}"
        if not res:
            res.append(f"-{term_str}" if coeff < 0 else term_str)
        else:
            sign = " - " if coeff < 0 else " + "
            res.append(f"{sign}{term_str}")
    if not res: return "0"
    return "".join(res)

@app.post("/api/solve")
async def solve_lp(request: SolveRequest):
    problem_input = request.problem.strip()
    if not problem_input:
        raise HTTPException(status_code=400, detail="Nội dung bài toán không được để trống.")

    # 1. Tự động lược bỏ các ràng buộc trùng lặp
    problem_input = deduplicate_problem_input(problem_input)

    output_buffer = StringIO()
    solver_status = "Optimal"
    has_graph = False

    try:
        # 1. Phân tích bài toán
        c, A, b, var_names, var_mapping, is_max, actual_vars, var_consts, zeta_offset, orig_obj_terms, orig_parsed_constraints = parse_problem(problem_input)
        
        has_negative_b = any(val < 0 for val in b)
        has_zero_b = any(val == 0 for val in b)
        
        req_method = request.method
        if req_method:
            used_method = req_method
        else:
            if has_negative_b:
                used_method = "two_phase"
            elif has_zero_b:
                used_method = "bland"
            else:
                used_method = "simplex"
                
        if used_method == "two_phase":
            method_title = "Phương pháp đơn hình 2 pha"
        elif used_method == "bland":
            method_title = "Phương pháp Bland"
        else:
            method_title = "Phương pháp đơn hình"

        with capture_stdout() as captured:
            # In tên phương pháp ở đầu mỗi lời giải bài toán
            print(method_title)
            print()
            
            # 2. Hiển thị bước đặt biến thay thế (nếu có)
            has_substitution = False
            substitution_lines = []
            for v in var_names:
                mapping = var_mapping.get(v, [])
                const_val = var_consts.get(v, Fraction(0))
                if len(mapping) == 1:
                    new_v, mult = mapping[0]
                    if mult == -1:
                        has_substitution = True
                        if const_val != 0:
                            substitution_lines.append(f"{to_subscript(new_v)} = {format_fraction(const_val)} - {to_subscript(v)} với {to_subscript(new_v)} >= 0")
                        else:
                            substitution_lines.append(f"{to_subscript(new_v)} = -{to_subscript(v)} với {to_subscript(new_v)} >= 0")
                    elif mult == 1 and const_val != 0:
                        has_substitution = True
                        sign = " - " if const_val > 0 else " + "
                        substitution_lines.append(f"{to_subscript(new_v)} = {to_subscript(v)}{sign}{format_fraction(abs(const_val))} với {to_subscript(new_v)} >= 0")
                elif len(mapping) == 2:
                    has_substitution = True
                    new_v1, mult1 = mapping[0]
                    new_v2, mult2 = mapping[1]
                    substitution_lines.append(f"{to_subscript(v)} = {to_subscript(new_v1)} - {to_subscript(new_v2)} với {to_subscript(new_v1)}, {to_subscript(new_v2)} >= 0")

            if is_max:
                # Kiểm tra xem có the terms nào thay đổi không
                pass # Sẽ xử lý chung bên dưới

            if has_substitution:
                for idx, line in enumerate(substitution_lines):
                    if idx == 0:
                        print(f"Đặt {line}")
                    else:
                        print(f"    {line}")
                print()
                
                equiv_lines = []
                
                # 1. Hàm mục tiêu
                orig_obj_str = f"{'max' if is_max else 'min'} {format_expr(orig_obj_terms)}"
                
                new_obj_terms_dict = {v: Fraction(0) for v in actual_vars}
                new_zeta = Fraction(0)
                for coeff, v in orig_obj_terms:
                    new_zeta += coeff * var_consts.get(v, Fraction(0))
                    for new_v, mult in var_mapping.get(v, [(v, Fraction(1))]):
                        new_obj_terms_dict[new_v] += coeff * mult
                new_obj_list = [(new_obj_terms_dict[v], v) for v in actual_vars if new_obj_terms_dict[v] != 0]
                
                mid_obj_str = f"{'max' if is_max else 'min'} {format_expr(new_obj_list)}"
                if new_zeta != 0:
                     mid_obj_str += f" {'+' if new_zeta > 0 else '-'} {format_fraction(abs(new_zeta))}"
                
                if is_max:
                    final_obj_list = [(-coeff, v) for coeff, v in new_obj_list]
                    final_zeta = -new_zeta
                    final_expr = format_expr(final_obj_list)
                    if final_zeta != 0:
                        final_expr += f" {'+' if final_zeta > 0 else '-'} {format_fraction(abs(final_zeta))}"
                    final_obj_str = f"- min {final_expr}"
                    if not final_expr: final_obj_str = "- min 0"
                    
                    equiv_lines.append((f"+) {orig_obj_str}", f"<=> {mid_obj_str}"))
                    equiv_lines.append(("", f"<=> {final_obj_str}"))
                else:
                    if mid_obj_str != orig_obj_str:
                        equiv_lines.append((f"+) {orig_obj_str}", f"<=> {mid_obj_str}"))
                        
                # 2. Ràng buộc
                processed_eqs = set()
                for constr in orig_parsed_constraints:
                    is_affected = False
                    for coeff, v in constr['terms']:
                        if v in var_mapping and var_mapping[v] != [(v, Fraction(1))]:
                            is_affected = True
                            break
                    if is_affected:
                        orig_idx = constr['original_line_idx']
                        is_eq = constr.get('is_eq', False)
                        
                        if is_eq:
                            if orig_idx in processed_eqs: continue
                            processed_eqs.add(orig_idx)
                            op = '='
                        else:
                            op = constr['op']
                            
                        orig_lhs = format_expr(constr['terms'])
                        orig_str = f"{orig_lhs} {op} {format_fraction(constr['rhs'])}"
                        
                        new_terms_dict = {v: Fraction(0) for v in actual_vars}
                        new_const = Fraction(0)
                        for coeff, v in constr['terms']:
                            new_const += coeff * var_consts.get(v, Fraction(0))
                            for new_v, mult in var_mapping.get(v, [(v, Fraction(1))]):
                                new_terms_dict[new_v] += coeff * mult
                                
                        new_list = [(new_terms_dict[v], v) for v in actual_vars if new_terms_dict[v] != 0]
                        new_lhs = format_expr(new_list)
                        new_rhs = constr['rhs'] - new_const
                        new_str = f"{new_lhs} {op} {format_fraction(new_rhs)}"
                        
                        # Kiểm tra nếu kết quả là ràng buộc non-negativity hiển nhiên (yi >= 0)
                        # thì chỉ hiển thị dòng biến đổi, KHÔNG thêm bước nhân -1 thành <= 0
                        is_trivial_nonneg = (
                            op == '>=' and new_rhs == 0
                            and len(new_list) == 1 and new_list[0][0] == 1
                        )
                        
                        equiv_lines.append((f"+) {orig_str}", f"<=> {new_str}"))
                        
                        if is_trivial_nonneg:
                            # y >= 0 là ràng buộc mặc định, không cần viết thêm -y <= 0
                            pass
                        elif op == '>=':
                            # Nhân -1 cả 2 vế để đổi >= thành <=
                            neg_list = [(-c, v) for c, v in new_list]
                            neg_lhs = format_expr(neg_list)
                            neg_rhs = format_fraction(-new_rhs)
                            equiv_lines.append(("", f"<=> {neg_lhs} <= {neg_rhs}"))
                        elif op == '=':
                            # Tách = thành 2 ràng buộc <=
                            neg_list = [(-c, v) for c, v in new_list]
                            neg_lhs = format_expr(neg_list)
                            equiv_lines.append(("", f"<=> ⎧ {neg_lhs} <= {format_fraction(-new_rhs)}"))
                            equiv_lines.append(("", f"    ⎩ {new_lhs} <= {format_fraction(new_rhs)}"))

                # 3. Ràng buộc dấu âm (x <= 0)
                # Tính signs để check
                # Do hàm parse_problem không trả về signs, ta có thể suy ra từ var_mapping
                for v in var_names:
                    mapping = var_mapping.get(v, [])
                    if len(mapping) == 1 and mapping[0][1] == Fraction(-1) and var_consts.get(v, 0) == 0:
                        new_v = mapping[0][0]
                        equiv_lines.append((f"+) {to_subscript(v)} <= 0", f"<=> {to_subscript(new_v)} >= 0"))

                # In các dòng căn lề
                if equiv_lines:
                    max_lhs_len = max(len(lhs) for lhs, rhs in equiv_lines if lhs)
                    for lhs, rhs in equiv_lines:
                        if lhs:
                            print(f"{lhs:<{max_lhs_len}} {rhs}")
                        else:
                            print(f"{'':<{max_lhs_len}} {rhs}")
                print()
            elif is_max:
                orig_obj_str = f"max {format_expr(orig_obj_terms)}"
                final_obj_list = [(-coeff, v) for coeff, v in orig_obj_terms]
                final_expr = format_expr(final_obj_list)
                if not final_expr: final_expr = "0"
                print(f"+) {orig_obj_str} <=> -min({final_expr})")
                print()                
            # 3. Chuẩn hóa bài toán
            # Kiểm tra xem bài toán gốc có cần biến đổi không:
            # - Không thay biến (has_substitution)
            # - Không phải bài max (is_max)
            # - Không có hằng số zeta (zeta_offset != 0)
            # - Không có ràng buộc >= hoặc = trong bài gốc
            has_ge_constraint = any(
                c['op'] == '>=' and not c.get('is_eq', False)
                for c in orig_parsed_constraints
            )
            has_eq_constraint = any(c.get('is_eq', False) for c in orig_parsed_constraints)
            
            is_already_standard = (
                not has_substitution and not is_max
                and zeta_offset == 0
                and not has_ge_constraint and not has_eq_constraint
            )
            
            # Bước biến đổi ràng buộc >= và = (nếu có, và chưa được xử lý bởi has_substitution)
            if not has_substitution and (has_ge_constraint or has_eq_constraint):
                constraint_equiv_lines = []
                processed_eq_idxs = set()
                
                for constr in orig_parsed_constraints:
                    orig_idx = constr['original_line_idx']
                    is_eq = constr.get('is_eq', False)
                    op = constr['op']
                    
                    lhs_str = format_expr(constr['terms'])
                    rhs_str = format_fraction(constr['rhs'])
                    
                    if is_eq:
                        # Ràng buộc = : chỉ xử lý 1 lần cho cả 2 rows
                        if orig_idx in processed_eq_idxs:
                            continue
                        processed_eq_idxs.add(orig_idx)
                        orig_str = f"+) {lhs_str} = {rhs_str}"
                        # Dòng 1: tách thành >= và <=
                        line1 = f"⎧ {lhs_str} >= {rhs_str}"
                        line2 = f"⎩ {lhs_str} <= {rhs_str}"
                        # Dòng 2: đổi >= -> nhân -1 thành <=
                        neg_terms = [(-coeff, v) for coeff, v in constr['terms']]
                        neg_lhs = format_expr(neg_terms)
                        neg_rhs = format_fraction(-constr['rhs'])
                        line3 = f"⎧ {neg_lhs} <= {neg_rhs}"
                        line4 = f"⎩ {lhs_str} <= {rhs_str}"
                        constraint_equiv_lines.append((orig_str, f"<=> {line1}"))
                        constraint_equiv_lines.append(("", f"    {line2}"))
                        constraint_equiv_lines.append(("", f"<=> {line3}"))
                        constraint_equiv_lines.append(("", f"    {line4}"))
                    elif op == '>=':
                        # Ràng buộc >= : nhân -1 cả 2 vế
                        orig_str = f"+) {lhs_str} >= {rhs_str}"
                        neg_terms = [(-coeff, v) for coeff, v in constr['terms']]
                        neg_lhs = format_expr(neg_terms)
                        neg_rhs = format_fraction(-constr['rhs'])
                        new_str = f"{neg_lhs} <= {neg_rhs}"
                        constraint_equiv_lines.append((orig_str, f"<=> {new_str}"))
                
                if constraint_equiv_lines:
                    max_lhs = max((len(lhs) for lhs, _ in constraint_equiv_lines if lhs), default=0)
                    for lhs, rhs in constraint_equiv_lines:
                        if lhs:
                            print(f"{lhs:<{max_lhs}} {rhs}")
                        else:
                            print(f"{'':<{max_lhs}} {rhs}")
                    print()
            
            if is_already_standard:
                print("Bài toán gốc là dạng chuẩn.")
            else:
                print("Ta chuyển bài toán ban đầu về dạng chuẩn:")
            print_standard_form(c, A, b, actual_vars, zeta_offset=zeta_offset)
            print()


            # 4. Phân tích hệ số b_i để chọn phương pháp phù hợp
            has_negative = any(val < 0 for val in b)
            has_zero = any(val == 0 for val in b)
            
            if req_method is None:
                # Chế độ tự động (người dùng bấm Giải Toán ở màn hình chính)
                if has_negative:
                    used_method = 'two_phase'
                elif has_zero:
                    used_method = 'bland'
                else:
                    used_method = 'simplex'
            else:
                # Chế độ người dùng yêu cầu phương pháp cụ thể từ danh sách đề xuất
                if used_method == 'simplex' and has_negative:
                    used_method = 'two_phase'
                elif used_method == 'bland' and has_negative:
                    used_method = 'two_phase'

            # 5. Giải bài toán theo phương pháp đã chọn
            if used_method == 'bland':
                res, solver = giai_hai_pha(c, A, b, actual_vars, var_mapping, verbose=True, method='bland', is_max=is_max, original_vars=var_names, var_consts=var_consts, zeta_offset=zeta_offset)
                if res != "Infeasible" and solver:
                    solver.in_ket_luan(is_max)
                solver_status = res
            elif used_method == 'simplex':
                res, solver = giai_hai_pha(c, A, b, actual_vars, var_mapping, verbose=True, method='simplex', is_max=is_max, original_vars=var_names, var_consts=var_consts, zeta_offset=zeta_offset)
                if res != "Infeasible" and solver:
                    solver.in_ket_luan(is_max)
                solver_status = res
            else: # two_phase
                res, solver = giai_hai_pha(c, A, b, actual_vars, var_mapping, verbose=True, method='simplex', is_max=is_max, original_vars=var_names, force_two_phase=True, var_consts=var_consts, zeta_offset=zeta_offset)
                if res != "Infeasible" and solver:
                    solver.in_ket_luan(is_max)
                solver_status = res

            # Khắc phục xoay vòng tự động khi chạy chế độ tự chọn simplex thường
            if req_method is None and used_method == 'simplex' and res == "Cycling":
                print("\n" + "="*50)
                print("[!] CẢNH BÁO: Phát hiện xoay vòng vô hạn (Cycling) ở phương pháp Đơn hình thường!")
                print("Hệ thống tự động giải lại bằng Phương pháp xoay Bland để tìm kết quả...")
                print("="*50 + "\n")
                
                res_bland, solver_bland = giai_hai_pha(c, A, b, actual_vars, var_mapping, verbose=True, method='bland', is_max=is_max, original_vars=var_names)
                if res_bland != "Infeasible" and solver_bland:
                    solver_bland.in_ket_luan(is_max)
                res, solver = res_bland, solver_bland
                solver_status = f"Bland (Cycling Resolved)"
                used_method = "bland"

        # Lấy toàn bộ log text in ra
        output_steps = captured.getvalue()

        # 5. Tự động xử lý đồ thị hình học nếu bài toán có đúng 2 biến
        geom_steps = ""
        graph_bounds = None
        graph_data = None
        if len(var_names) == 2:
            try:
                with capture_stdout() as geom_captured:
                    graph_bounds = giai_phuong_phap_hinh_hoc(problem_input, res, solver, is_max)
                geom_steps = geom_captured.getvalue()
                has_graph = True
                
                from phuong_phap_hinh_hoc import LAST_PLOT_DATA
                if LAST_PLOT_DATA:
                    def to_float(val):
                        if isinstance(val, Fraction):
                            return float(val)
                        return val
                        
                    formatted_constraints = []
                    for c in LAST_PLOT_DATA.get('parsed_constraints', []):
                        formatted_constraints.append({
                            'a': to_float(c.get('a', 0)),
                            'b': to_float(c.get('b', 0)),
                            'c': to_float(c.get('c', 0)),
                            'sign': c.get('sign', '<='),
                            'str': c.get('str', ''),
                            'index': c.get('index', 0)
                        })
                        
                    formatted_vertices = []
                    for v in LAST_PLOT_DATA.get('vertices', []):
                        formatted_vertices.append({
                            'x1': to_float(v.get('x1', 0)),
                            'x2': to_float(v.get('x2', 0)),
                            'x1_str': format_fraction(v.get('x1', 0)),
                            'x2_str': format_fraction(v.get('x2', 0)),
                            'name': v.get('name', ''),
                            'intersect': v.get('intersect', (0, 0))
                        })
                        
                    graph_data = {
                        'constraints': formatted_constraints,
                        'vertices': formatted_vertices,
                        'signs': LAST_PLOT_DATA.get('signs', {}),
                        'c1': to_float(LAST_PLOT_DATA.get('c1', 0)),
                        'c2': to_float(LAST_PLOT_DATA.get('c2', 0)),
                        'lcm_val': to_float(LAST_PLOT_DATA.get('lcm_val', 0)),
                        'is_max': LAST_PLOT_DATA.get('is_max', False),
                        'res': LAST_PLOT_DATA.get('res', '')
                    }
                    
            except Exception as geom_err:
                print(f"[!] Lỗi khi chuẩn bị dữ liệu hình học: {geom_err}")
        
        # Ánh xạ trạng thái hiển thị
        status_map = {
            "Optimal": "Nhiệm tối ưu (Duy nhất / Vô số)",
            "Unbounded": "Không giới nội",
            "Infeasible": "Vô nghiệm (Miền chấp nhận rỗng)",
            "Bland (Cycling Resolved)": "Khắc phục xoay vòng thành công (Bland)"
        }
        display_status = status_map.get(solver_status, solver_status)

        return {
            "status": "success",
            "solver_status": display_status,
            "output_steps": output_steps,
            "has_graph": has_graph,
            "graph_bounds": {"xmin": graph_bounds[0][0], "xmax": graph_bounds[0][1], "ymin": graph_bounds[1][0], "ymax": graph_bounds[1][1]} if graph_bounds and graph_bounds[0] else None,
            "graph_data": graph_data,
            "geom_steps": geom_steps,
            "method": used_method
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            "status": "error",
            "message": f"Lỗi phân tích bài toán: {str(e)}",
            "debug": error_details
        }



# Endpoint nhận diện ảnh bằng OCR
@app.post("/api/ocr")
async def recognize_image(request: OcrRequest):
    # 1. Thử nhận diện bằng Gemini API trước nếu có API Key
    api_key = request.apiKey.strip()
    if api_key:
        try:
            import urllib.request
            import json
            
            raw_base64 = request.image
            if "," in raw_base64:
                raw_base64 = raw_base64.split(",")[1]
                
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    "Bạn là chuyên gia toán học tối ưu hóa. Hãy đọc hình ảnh bài toán quy hoạch tuyến tính "
                                    "(viết tay hoặc in ấn) và trích xuất hàm mục tiêu cùng toàn bộ các ràng buộc.\n\n"
                                    "Hãy chuẩn hóa toán học trích xuất được theo định dạng sau (mỗi phương trình trên một dòng):\n"
                                    "1. Dòng hàm mục tiêu: ví dụ 'max 3x1 + 2x2' hoặc 'min -x1 + x2'.\n"
                                    "2. Các dòng ràng buộc: ví dụ '-x1 + 2x2 >= -1' hoặc 'x1 - x2 <= 2'.\n"
                                    "3. Các ràng buộc dấu của biến: ví dụ 'x1 >= 0', 'x2 >= 0'.\n\n"
                                    "LƯU Ý QUAN TRỌNG: Chỉ trả về các dòng toán học thuần túy. TUYỆT ĐỐI không ghi thêm từ ngữ giải thích, markdown code block (như ```) hay các ký tự thừa khác."
                                )
                            },
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": raw_base64
                                }
                            }
                        ]
                    }
                ]
            }
            
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode("utf-8"), 
                headers=headers, 
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                # Loại bỏ các ký tự Markdown block rác
                text = text.replace("```json", "").replace("```text", "").replace("```", "").strip()
                if text:
                    return {"status": "success", "text": text}
        except Exception as gemini_err:
            print(f"[!] Lỗi nhận diện bằng Gemini API (đang tự động chuyển sang offline): {gemini_err}")

    # 2. Dự phòng ngoại tuyến (Offline Fallback)
    img_data = request.image
    if "," in img_data:
        img_data = img_data.split(",")[1]
        
    try:
        img_bytes = base64.b64decode(img_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể giải mã dữ liệu Base64 của ảnh: {e}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        temp_file.write(img_bytes)
        temp_path = temp_file.name

    try:
        # Thử sử dụng EasyOCR ngoại tuyến
        try:
            import easyocr
            reader = easyocr.Reader(['en'])
            ocr_results = reader.readtext(temp_path, detail=0)
            if not ocr_results:
                raise Exception("Không nhận diện được ký tự nào trong ảnh.")
            
            recognized_text = normalize_ocr_text(ocr_results)
            return {"status": "success", "text": recognized_text}
            
        except Exception as e_easyocr:
            # Thử sử dụng pytesseract ngoại tuyến làm backup
            try:
                import pytesseract
                from PIL import Image
                text = pytesseract.image_to_string(Image.open(temp_path))
                if not text.strip():
                    raise Exception("Không tìm thấy chữ hoặc phương trình trong ảnh.")
                
                recognized_text = normalize_ocr_text(text.strip().split('\n'))
                return {"status": "success", "text": recognized_text}
            except Exception as e_pytesseract:
                # Hướng dẫn người dùng cài đặt easyocr chi tiết kèm log lỗi
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Hệ thống cần thư viện EasyOCR ngoại tuyến để tự động quét đề bài.\n\n"
                        "Vui lòng mở Terminal và chạy lệnh sau để cài đặt:\n"
                        "pip install easyocr\n\n"
                        f"(Chi tiết kỹ thuật EasyOCR: {str(e_easyocr)})\n"
                        f"(Chi tiết kỹ thuật Pytesseract: {str(e_pytesseract)})"
                    )
                )
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

# Gắn kết thư mục tĩnh 'gui' (chứa HTML/CSS/JS) để phục vụ giao diện
# Dùng GUI_DIR đã detect đúng cho cả chế độ dev và frozen exe
if os.path.exists(GUI_DIR):
    app.mount("/", StaticFiles(directory=GUI_DIR, html=True), name="static")

if __name__ == "__main__":
    print("[*] Đang khởi chạy QHTT Solver API Server tại http://127.0.0.1:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)

