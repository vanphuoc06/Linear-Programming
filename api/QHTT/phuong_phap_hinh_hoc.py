import sys
import os
import numpy as np
import math
from fractions import Fraction
import re
from tien_ich import format_fraction, to_subscript
LAST_PLOT_DATA = {}

# PyInstaller compatibility: lưu file vào thư mục ghi được
if getattr(sys, 'frozen', False):
    _WORK_DIR = os.path.dirname(sys.executable)
else:
    _WORK_DIR = os.path.dirname(os.path.abspath(__file__))


def fraction_lcm(f1, f2):
    """
    Tính LCM của hai phân số.
    LCM(a/b, c/d) = LCM(a, c) / GCD(b, d)
    """
    a = abs(f1.numerator)
    b = f1.denominator
    c = abs(f2.numerator)
    d = f2.denominator
    if a == 0 or c == 0:
        return Fraction(0)
    num = math.lcm(a, c)
    den = math.gcd(b, d)
    return Fraction(num, den)


def giai_phuong_phap_hinh_hoc(problem_input, res, solver, is_max):
    print("\n" + "="*60)
    print("                PHƯƠNG PHÁP HÌNH HỌC")
    print("="*60)
    
    # 1. Phân tích bài toán
    # Chuẩn hóa các toán tử so sánh có khoảng trắng dạng < = hoặc > =
    problem_input = re.sub(r'<\s*=', '<=', problem_input)
    problem_input = re.sub(r'>\s*=', '>=', problem_input)
    lines = [line.strip() for line in problem_input.strip().split('\n') if line.strip()]
    
    # Tìm dòng chứa hàm mục tiêu (dòng chứa 'max' hoặc 'min')
    obj_line_idx = 0
    for i, line in enumerate(lines):
        if "max" in line.lower() or "min" in line.lower():
            obj_line_idx = i
            break
            
    # Tìm các dòng ràng buộc dấu
    pure_sign_lines = set()
    vars_found = sorted(list(set(re.findall(r'x\d+', problem_input))), key=lambda x: int(x[1:]))
    signs = {v: 'free' for v in vars_found}
    
    for i, line in enumerate(lines):
        if i == obj_line_idx:
            continue
        s = line.replace(" ", "").replace("\t", "").replace(";", ",")
        if re.match(r'^((?:x\d+,?)+(?:>=|<=)0,?)+$', s):
            pure_sign_lines.add(i)
            for match in re.finditer(r'((?:x\d+,?)+)(>=|<=)0', s):
                vars_str = match.group(1)
                op = match.group(2)
                for v in re.findall(r'x\d+', vars_str):
                    if op == ">=": signs[v] = 'pos'
                    elif op == "<=": signs[v] = 'neg'
                    
    # 2. Thu thập và đánh số các ràng buộc
    constraints_list = []
    
    # Ràng buộc gốc
    for i, line in enumerate(lines):
        if i == obj_line_idx or i in pure_sign_lines:
            continue
        if line.strip():
            constraints_list.append(line.strip())
            
    # Ràng buộc dấu của từng biến
    for v in vars_found:
        sign = signs[v]
        if sign == 'pos':
            constraints_list.append(f"{v} >= 0")
        elif sign == 'neg':
            constraints_list.append(f"{v} <= 0")
            
    print("Ta gán các số thứ tự cho các ràng buộc:")
    for idx, const_str in enumerate(constraints_list):
        sub_str = to_subscript(const_str)
        print(f"    {sub_str:<30} ({idx + 1})")
    print()
    
    # 3. Biểu diễn các ràng buộc dưới dạng phương trình / bất phương trình tuyến tính
    # Ràng buộc dạng: a*x1 + b*x2 <= c hoặc a*x1 + b*x2 >= c
    parsed_constraints = []
    for idx, const_str in enumerate(constraints_list):
        # clean spaces
        s = const_str.replace(" ", "")
        sign = "<="
        if ">=" in s:
            sign = ">="
            lhs, rhs = s.split(">=")
        elif "<=" in s:
            sign = "<="
            lhs, rhs = s.split("<=")
        elif "=" in s:
            sign = "="
            lhs, rhs = s.split("=")
        else:
            continue
            
        rhs_val = Fraction(rhs)
        
        # Tìm hệ số x1, x2
        coeff = {v: Fraction(0) for v in vars_found}
        terms = re.findall(r'([+-]?\s*[\d\./]*)\s*(x\d+)', lhs)
        for c_str, var_name in terms:
            c_str = c_str.replace(" ", "")
            if not c_str or c_str == "+": val = Fraction(1)
            elif c_str == "-": val = Fraction(-1)
            else: val = Fraction(c_str)
            coeff[var_name] = val
            
        parsed_constraints.append({
            'index': idx + 1,
            'a': coeff.get('x1', Fraction(0)),
            'b': coeff.get('x2', Fraction(0)),
            'sign': sign,
            'c': rhs_val,
            'str': const_str
        })
        
    # 4. Tìm các đỉnh giao của miền nghiệm
    # Một điểm giao là giao điểm của 2 đường thẳng biên thỏa mãn tất cả các ràng buộc
    vertices = []
    num_consts = len(parsed_constraints)
    
    for i in range(num_consts):
        for j in range(i + 1, num_consts):
            c1 = parsed_constraints[i]
            c2 = parsed_constraints[j]
            
            # Giải hệ phương trình:
            # c1.a * x1 + c1.b * x2 = c1.c
            # c2.a * x1 + c2.b * x2 = c2.c
            A_mat = np.array([[float(c1['a']), float(c1['b'])], [float(c2['a']), float(c2['b'])]])
            B_mat = np.array([float(c1['c']), float(c2['c'])])
            
            try:
                sol = np.linalg.solve(A_mat, B_mat)
                x1_val, x2_val = sol[0], sol[1]
                
                # Kiểm tra xem giao điểm có thỏa mãn tất cả các ràng buộc khác không
                feasible = True
                for k in range(num_consts):
                    ck = parsed_constraints[k]
                    lhs = float(ck['a']) * x1_val + float(ck['b']) * x2_val
                    rhs = float(ck['c'])
                    if ck['sign'] == "<=":
                        if lhs > rhs + 1e-7: feasible = False
                    elif ck['sign'] == ">=":
                        if lhs < rhs - 1e-7: feasible = False
                    elif ck['sign'] == "=":
                        if abs(lhs - rhs) > 1e-7: feasible = False
                        
                if feasible:
                    # Rút gọn tọa độ thành Fraction để chính xác tuyệt đối
                    det = c1['a'] * c2['b'] - c1['b'] * c2['a']
                    if det != 0:
                        x1_frac = (c1['c'] * c2['b'] - c1['b'] * c2['c']) / det
                        x2_frac = (c1['a'] * c2['c'] - c1['c'] * c2['a']) / det
                        
                        # Tránh trùng lặp
                        if not any(abs(v['x1'] - x1_frac) < 1e-9 and abs(v['x2'] - x2_frac) < 1e-9 for v in vertices):
                            vertices.append({
                                'x1': x1_frac,
                                'x2': x2_frac,
                                'intersect': (c1['index'], c2['index'])
                            })
            except np.linalg.LinAlgError:
                continue

    # Đặt tên các đỉnh A, B, C...
    vertex_names = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    current_name_idx = 0
    for v in vertices:
        if abs(v['x1']) < 1e-9 and abs(v['x2']) < 1e-9:
            v['name'] = 'O'
        else:
            name = vertex_names[current_name_idx % len(vertex_names)]
            if name == 'O':
                current_name_idx += 1
                name = vertex_names[current_name_idx % len(vertex_names)]
            v['name'] = name
            current_name_idx += 1
        
    print("Các đỉnh giao của miền nghiệm (các giao điểm thỏa mãn tất cả các ràng buộc):")
    if not vertices:
        if res == "Infeasible":
            print("    Không có đỉnh giao nào thỏa mãn (Miền chấp nhận được là rỗng).")
        else:
            print("    Miền nghiệm không có đỉnh hữu hạn.")
    else:
        for v in vertices:
            coord_str = f"({format_fraction(v['x1'])}, {format_fraction(v['x2'])})"
            print(f"    Đỉnh {v['name']}{coord_str} là giao điểm của ({v['intersect'][0]}) và ({v['intersect'][1]})")
    print()
    
    # 5. Phân tích hàm mục tiêu
    # z = c1*x1 + c2*x2
    obj_line = lines[obj_line_idx].lower()
    obj_line = obj_line.replace("min", "").replace("max", "").strip()
    
    c_coeff = {'x1': Fraction(0), 'x2': Fraction(0)}
    terms = re.findall(r'([+-]?\s*[\d\./]*)\s*(x\d+)', obj_line)
    for c_str, var_name in terms:
        c_str = c_str.replace(" ", "")
        if not c_str or c_str == "+": val = Fraction(1)
        elif c_str == "-": val = Fraction(-1)
        else: val = Fraction(c_str)
        c_coeff[var_name] = val
        
    c1, c2 = c_coeff['x1'], c_coeff['x2']
    
    # Tính lcm(|c1|, |c2|)
    c1_abs = abs(c1)
    c2_abs = abs(c2)
    lcm_val = fraction_lcm(c1_abs, c2_abs)
    if lcm_val == 0:
        lcm_val = Fraction(1)
        
    # In bước trượt hàm mục tiêu
    print("Tìm vector pháp tuyến và vẽ đường mức z:")
    z_lhs = ""
    if c1 != 0:
        z_lhs += f"{format_fraction(c1)}x₁"
    if c2 != 0:
        op = " + " if c2 > 0 else " - "
        if not z_lhs:
            op = "-" if c2 < 0 else ""
        z_lhs += f"{op}{format_fraction(abs(c2))}x₂"
        
    lcm_expr = f"lcm(|{format_fraction(c1)}|, |{format_fraction(c2)}|)"
    print(f"    Vẽ đường thẳng hàm mục tiêu z: {to_subscript(z_lhs)} = {lcm_expr} = {format_fraction(lcm_val)}")
    print("    Tịnh tiến đường z theo hướng tăng/giảm giá trị của hàm mục tiêu:")
    print("        - Tịnh tiến về hướng +∞ và -∞ để xác định điểm tối ưu.")
    print()
    
    # 6. Biện luận & Kết luận
    z_display = "zₘₐₓ" if is_max else "zₘᵢₙ"
    opt_val_text = ""
    
    if res == "Optimal" and solver:
        opt_val = -solver.zeta if is_max else solver.zeta
        opt_val_text = format_fraction(opt_val)
        
        has_multiple = any(val == 0 for val in solver.c)
        if has_multiple:
            # TH2: Vô số nghiệm
            # Tìm 2 đỉnh đạt giá trị tối ưu
            opt_vertices = []
            for v in vertices:
                val = c1 * v['x1'] + c2 * v['x2']
                if abs(val - opt_val) < 1e-7:
                    opt_vertices.append(v)
            
            print("Kết luận:")
            if len(opt_vertices) >= 2:
                v1, v2 = opt_vertices[0], opt_vertices[1]
                v1_coords = f"({format_fraction(v1['x1'])}, {format_fraction(v1['x2'])})"
                v2_coords = f"({format_fraction(v2['x1'])}, {format_fraction(v2['x2'])})"
                print(f"    Theo phương pháp trượt hàm mục tiêu, bài toán vô số nghiệm và nghiệm là đoạn thẳng nối 2 điểm "
                      f"{v1['name']}{v1_coords} và {v2['name']}{v2_coords} với "
                      f"{v1['name']} là nghiệm của hệ ({v1['intersect'][0]}, {v1['intersect'][1]}), "
                      f"{v2['name']} là nghiệm của hệ ({v2['intersect'][0]}, {v2['intersect'][1]}) "
                      f"và giá trị tối ưu là {z_display} = {opt_val_text}")
            else:
                print(f"    Theo phương pháp trượt hàm mục tiêu, bài toán vô số nghiệm và giá trị tối ưu là {z_display} = {opt_val_text}")
        else:
            # TH1: Nghiệm duy nhất
            # Tìm đỉnh tối ưu
            opt_v = None
            for v in vertices:
                val = c1 * v['x1'] + c2 * v['x2']
                if abs(val - opt_val) < 1e-7:
                    opt_v = v
                    break
                    
            print("Kết luận:")
            if opt_v:
                print(f"    Theo phương pháp trượt hàm mục tiêu, bài toán có nghiệm duy nhất tại "
                      f"{opt_v['name']} (x₁ = {format_fraction(opt_v['x1'])}, x₂ = {format_fraction(opt_v['x2'])}) "
                      f"và giá trị tối ưu {z_display} = {opt_val_text}")
            else:
                # Nếu không tìm thấy đỉnh hữu hạn (do lỗi sai số), tìm đỉnh có giá trị khớp nhất
                best_v = min(vertices, key=lambda v: abs((c1 * v['x1'] + c2 * v['x2']) - opt_val))
                print(f"    Theo phương pháp trượt hàm mục tiêu, bài toán có nghiệm duy nhất tại "
                      f"{best_v['name']} (x₁ = {format_fraction(best_v['x1'])}, x₂ = {format_fraction(best_v['x2'])}) "
                      f"và giá trị tối ưu {z_display} = {opt_val_text}")
                      
    elif res == "Unbounded":
        # TH3: Không giới nội
        sign = "+∞" if is_max else "-∞"
        print("Kết luận:")
        print(f"    Theo phương pháp trượt hàm mục tiêu, bài toán không giới nội và {z_display} = {sign}")
        
    else:
        # TH4: Vô nghiệm (Miền chấp nhận rỗng)
        sign = "-∞" if is_max else "+∞"
        print("Kết luận:")
        print(f"    Theo phương pháp trượt hàm mục tiêu, miền chấp nhận được là rỗng và giá trị tối ưu là {z_display} = {sign}")

    # 7. Tính khoảng hiển thị (bounding box) cho đồ thị Canvas
    global LAST_PLOT_DATA
    LAST_PLOT_DATA = {
        'vertices': vertices,
        'parsed_constraints': parsed_constraints,
        'num_consts': num_consts,
        'signs': signs,
        'c1': c1,
        'c2': c2,
        'lcm_val': lcm_val,
        'is_max': is_max,
        'res': res,
        'solver': solver
    }
    
    box_points = []
    if vertices:
        for v in vertices:
            box_points.append((float(v['x1']), float(v['x2'])))
            
    for ck in parsed_constraints:
        a_val = float(ck['a'])
        b_val = float(ck['b'])
        c_val = float(ck['c'])
        if ck['str'].replace(" ", "") in ["x1>=0", "x2>=0", "x1<=0", "x2<=0"]:
            continue
        if abs(a_val) > 1e-7:
            x_intercept = c_val / a_val
            if -15 <= x_intercept <= 15:
                box_points.append((x_intercept, 0.0))
        if abs(b_val) > 1e-7:
            y_intercept = c_val / b_val
            if -15 <= y_intercept <= 15:
                box_points.append((0.0, y_intercept))
                
    if not box_points:
        box_points = [(0.0, 0.0), (5.0, 5.0)]
        
    x_coords = [p[0] for p in box_points]
    y_coords = [p[1] for p in box_points]
    
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    
    x_pad = max(3.5, 0.45 * (x_max - x_min))
    y_pad = max(3.5, 0.45 * (y_max - y_min))
    xlim = (x_min - x_pad, x_max + x_pad)
    ylim = (y_min - y_pad, y_max + y_pad)
    
    print("="*60 + "\n")
    return xlim, ylim


