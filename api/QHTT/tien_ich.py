import re
import numpy as np
from fractions import Fraction

def format_fraction(val):
    """
    Định dạng số dưới dạng phân số hoặc số nguyên.
    """
    f = Fraction(val).limit_denominator()
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"

def to_subscript(text):
    """
    Chuyển đổi các số đi kèm sau biến thành chỉ số dưới (subscript).
    Ví dụ: x1 -> x₁, w12 -> w₁₂, y3 -> y₃. Các hệ số hay số khác giữ nguyên.
    """
    def replace_sub(match):
        letter = match.group(1)
        digits = match.group(2)
        sub_map = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        return letter + digits.translate(sub_map)
    
    return re.sub(r'([xywz])(\d+)', replace_sub, text, flags=re.IGNORECASE)

def parse_problem(problem_str):
    """
    Phân tích chuỗi bài toán QHTT.
    Hỗ trợ cả chuỗi nhập trên 1 dòng duy nhất.
    """
    # Xử lý các chỉ số dưới (subscript) do người dùng nhập hoặc copy/paste
    sub_map = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    problem_str = problem_str.translate(sub_map)
    
    # Hỗ trợ dấu phẩy trong số thập phân (VD: 0,5 -> 0.5)
    problem_str = re.sub(r'(\d),(\d)', r'\1.\2', problem_str)
    
    # Chuẩn hóa các toán tử so sánh có khoảng trắng dạng < = hoặc > =
    problem_str = re.sub(r'<\s*=', '<=', problem_str)
    problem_str = re.sub(r'>\s*=', '>=', problem_str)
    
    # Format lại để hỗ trợ nhập trên 1 dòng
    s = problem_str.replace('\n', ' ')
    
    # Tách sau mỗi RHS
    pattern_rhs = r'((?:<=|>=|=)\s*[+-]?\s*\d+(?:\.\d+)?(?:/\d+)?(?:[eE][+-]?\d+)?)'
    s = re.sub(pattern_rhs, r'\1\n', s)
    
    # Tách sau free/tùy ý
    pattern_free = r'(tùy ý|free|tuy y)'
    s = re.sub(pattern_free, r'\1\n', s, flags=re.IGNORECASE)
    
    raw_lines = [l.strip() for l in s.split('\n') if l.strip()]
    lines = []
    
    for line in raw_lines:
        obj_match = re.search(r'(min|max)', line, flags=re.IGNORECASE)
        op_match = re.search(r'(<=|>=|=)', line)
        if obj_match and op_match:
            # Dòng chứa cả hàm mục tiêu và ràng buộc -> Phân tách
            var_matches = list(re.finditer(r'x\d+', line))
            seen_vars = set()
            split_pos = -1
            
            for v_match in var_matches:
                v_name = v_match.group()
                if v_name in seen_vars:
                    # Lặp biến -> Tách từ term này
                    pos = v_match.start()
                    # Đi lùi để tìm dấu hoặc khoảng trắng
                    while pos > 0 and line[pos-1] not in ('+', '-', ' ', '\t', '<', '>', '='):
                        pos -= 1
                    # Cố gắng lùi qua khoảng trắng để lấy dấu + hoặc -
                    temp_pos = pos
                    while temp_pos > 0 and line[temp_pos-1] in (' ', '\t'):
                        temp_pos -= 1
                    if temp_pos > 0 and line[temp_pos-1] in ('+', '-'):
                        pos = temp_pos - 1
                    split_pos = pos
                    break
                seen_vars.add(v_name)
                
            if split_pos != -1:
                lines.append(line[:split_pos].strip())
                lines.append(line[split_pos:].strip())
            else:
                lines.append(line)
        else:
            lines.append(line)
    
    # 1. Tìm tất cả các biến x1, x2, ...
    vars_found = sorted(list(set(re.findall(r'x\d+', problem_str))), key=lambda x: int(x[1:]))
    
    # signs: var_name -> 'pos', 'neg', hoặc 'free'
    signs = {v: 'free' for v in vars_found}
    pure_sign_lines = set()
    
    # Tìm dòng chứa hàm mục tiêu (dòng chứa 'max' hoặc 'min')
    obj_line_idx = 0
    for i, line in enumerate(lines):
        if "max" in line.lower() or "min" in line.lower():
            obj_line_idx = i
            break

    for i, line in enumerate(lines):
        if i == obj_line_idx:
            continue # Bỏ qua dòng hàm mục tiêu
            
        s = line.replace(" ", "").replace("\t", "").replace(";", ",")
        
        # Regex tìm xem toàn bộ dòng có khớp với một chuỗi các ràng buộc dấu không
        # Ví dụ: x1>=0, x2<=0, x3,x4>=0
        if re.match(r'^((?:x\d+,?)+(?:>=|<=)0,?)+$', s):
            pure_sign_lines.add(i)
            for match in re.finditer(r'((?:x\d+,?)+)(>=|<=)0', s):
                vars_str = match.group(1)
                op = match.group(2)
                for v in re.findall(r'x\d+', vars_str):
                    if op == ">=": signs[v] = 'pos'
                    elif op == "<=": signs[v] = 'neg'
                    
        # Hỗ trợ explicitly khai báo "tùy ý" hoặc "free"
        elif re.match(r'^((?:x\d+,?)+)(?:tùyý|free|tuyy),?$', s.lower()):
            pure_sign_lines.add(i)
            for v in re.findall(r'x\d+', s):
                signs[v] = 'free'

    # Intermediate constraints
    parsed_constraints = []
    for i, line in enumerate(lines):
        if i == obj_line_idx or i in pure_sign_lines:
            continue
        
        if "<=" in line:
            lhs, rhs = line.split("<=")
            ops = ['<=']
        elif ">=" in line:
            lhs, rhs = line.split(">=")
            ops = ['>=']
        elif "=" in line:
            lhs, rhs = line.split("=")
            ops = ['<=', '>=']
        else: continue
            
        rhs_match = re.search(r'([+-]?\s*\d+(?:\.\d+)?(?:/\d+)?)', rhs)
        if not rhs_match: continue
        try:
            rhs_val = Fraction(rhs_match.group(1).replace(" ", ""))
        except: continue
            
        terms = re.findall(r'([+-]?\s*[\d\./]*)\s*(x\d+)', lhs)
        parsed_terms = []
        for coeff_str, var_name in terms:
            coeff_str = coeff_str.replace(" ", "")
            if not coeff_str or coeff_str == "+": coeff = Fraction(1)
            elif coeff_str == "-": coeff = Fraction(-1)
            else: coeff = Fraction(coeff_str)
            parsed_terms.append((coeff, var_name))
        
        for op in ops:
            parsed_constraints.append({
                'terms': parsed_terms,
                'op': op,
                'rhs': rhs_val,
                'original_line_idx': i,
                'is_eq': len(ops) == 2
            })

    actual_vars = []
    var_mapping = {} 
    var_consts = {}
    
    current_idx = 1
    constraints_to_remove = set()
    
    for v in vars_found:
        if signs[v] == 'pos':
            actual_vars.append(v)
            var_mapping[v] = [(v, Fraction(1))]
            var_consts[v] = Fraction(0)
        elif signs[v] == 'neg':
            new_v = f"y{current_idx}"
            actual_vars.append(new_v)
            var_mapping[v] = [(new_v, Fraction(-1))]
            var_consts[v] = Fraction(0)
            current_idx += 1
        else: # free
            bound_found = False
            for idx, c_dict in enumerate(parsed_constraints):
                if idx in constraints_to_remove: continue
                if len(c_dict['terms']) == 1 and c_dict['terms'][0][1] == v:
                    coeff, _ = c_dict['terms'][0]
                    rhs = c_dict['rhs']
                    op = c_dict['op']
                    if coeff == 0: continue
                    bound_val = rhs / coeff
                    is_le = (op == '<=') if coeff > 0 else (op == '>=')
                    
                    new_v = f"y{current_idx}"
                    actual_vars.append(new_v)
                    if is_le:
                        var_mapping[v] = [(new_v, Fraction(-1))]
                        var_consts[v] = bound_val
                    else:
                        var_mapping[v] = [(new_v, Fraction(1))]
                        var_consts[v] = bound_val
                        
                    current_idx += 1
                    bound_found = True
                    constraints_to_remove.add(idx)
                    break
                    
            if not bound_found:
                idx_str = v[1:]
                v_p = f"x{idx_str}⁺"
                v_n = f"x{idx_str}⁻"
                actual_vars.extend([v_p, v_n])
                var_mapping[v] = [(v_p, Fraction(1)), (v_n, Fraction(-1))]
                var_consts[v] = Fraction(0)

    n_new = len(actual_vars)
    c_arr = [Fraction(0)] * n_new
    zeta_offset = Fraction(0)
    
    obj_line = lines[obj_line_idx].lower()
    is_max = "max" in obj_line
    obj_line = obj_line.replace("min", "").replace("max", "").strip()
    
    terms = re.findall(r'([+-]?\s*[\d\./]*)\s*(x\d+)', obj_line)
    orig_obj_terms = []
    for coeff_str, var_name in terms:
        coeff_str = coeff_str.replace(" ", "")
        if not coeff_str or coeff_str == "+": coeff = Fraction(1)
        elif coeff_str == "-": coeff = Fraction(-1)
        else: coeff = Fraction(coeff_str)
        
        orig_obj_terms.append((coeff, var_name))
        
        zeta_offset += coeff * var_consts.get(var_name, Fraction(0))
        for new_v, mult in var_mapping[var_name]:
            idx = actual_vars.index(new_v)
            c_arr[idx] += coeff * mult
    
    if is_max:
        c_arr = [-val for val in c_arr]
        zeta_offset = -zeta_offset
        
    A = []
    b = []
    
    for idx, constr in enumerate(parsed_constraints):
        if idx in constraints_to_remove: continue
        
        sign = 1 if constr['op'] == '<=' else -1
        rhs_val = constr['rhs']
        
        row = [Fraction(0)] * n_new
        const_shift = Fraction(0)
        
        for coeff, var_name in constr['terms']:
            const_shift += coeff * var_consts.get(var_name, Fraction(0))
            for new_v, mult in var_mapping[var_name]:
                var_idx = actual_vars.index(new_v)
                row[var_idx] += coeff * mult
                
        shifted_rhs = rhs_val - const_shift
        A.append([sign * val for val in row])
        b.append(sign * shifted_rhs)
        
    return c_arr, A, b, vars_found, var_mapping, is_max, actual_vars, var_consts, zeta_offset, orig_obj_terms, parsed_constraints

def print_standard_form(c, A, b, var_names, zeta_offset=Fraction(0)):
    n = len(c)
    m = len(A)
    lines = []
    
    # 1. Hàm mục tiêu
    c_terms = []
    for j, coeff in enumerate(c):
        if coeff != 0:
            term_str = to_subscript(var_names[j]) if abs(coeff) == 1 else f"{format_fraction(abs(coeff))}{to_subscript(var_names[j])}"
            if not c_terms:
                c_terms.append(f"-{term_str}" if coeff < 0 else term_str)
            else:
                sign = " - " if coeff < 0 else " + "
                c_terms.append(f"{sign}{term_str}")
                
    if zeta_offset != 0:
        sign = " - " if zeta_offset < 0 else " + "
        if not c_terms:
            c_terms.append(f"-{format_fraction(abs(zeta_offset))}" if zeta_offset < 0 else f"{format_fraction(zeta_offset)}")
        else:
            c_terms.append(f"{sign}{format_fraction(abs(zeta_offset))}")
            
    z_expr = "".join(c_terms)
    if not z_expr: z_expr = "0"
    lines.append(f"min {z_expr}")
    
    # 2. Ràng buộc
    col_widths = [0] * n
    for j in range(n):
        for i in range(m):
            if A[i][j] != 0:
                term = to_subscript(var_names[j]) if abs(A[i][j]) == 1 else f"{format_fraction(abs(A[i][j]))}{to_subscript(var_names[j])}"
                col_widths[j] = max(col_widths[j], len(term) + 3)
                
    for i in range(m):
        row_str = ""
        first = True
        for j in range(n):
            if A[i][j] != 0:
                term = to_subscript(var_names[j]) if abs(A[i][j]) == 1 else f"{format_fraction(abs(A[i][j]))}{to_subscript(var_names[j])}"
                if first:
                     sign = "-" if A[i][j] < 0 else " "
                     first = False
                else:
                     sign = " - " if A[i][j] < 0 else " + "
                row_str += f"{sign}{term:>{col_widths[j]-3}}"
            else:
                row_str += " " * col_widths[j]
        lines.append(f"{row_str} <= {format_fraction(b[i])}")
        
    lines.append(", ".join([to_subscript(v) for v in var_names]) + " >= 0")
    
    # Vẽ ngoặc
    num_lines = len(lines)
    for idx, line in enumerate(lines):
        if num_lines == 1:
            brace = "{"
        elif num_lines == 2:
            brace = "⎧" if idx == 0 else "⎩"
        else:
            if idx == 0:
                brace = "⎧"
            elif idx == num_lines - 1:
                brace = "⎩"
            elif idx == num_lines // 2:
                brace = "⎨"
            else:
                brace = "⎪"
        print(f"  {brace} {line}")

def visualize_geometric(c, A, b, var_names, var_mapping, is_max):
    # Placeholder
    pass
