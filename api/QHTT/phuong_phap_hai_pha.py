import numpy as np
from fractions import Fraction
from phuong_phap_don_hinh import BoGiaiDonHinh
from tien_ich import format_fraction, to_subscript

def format_coeff_term(coeff, var_name):
    if coeff == 1:
        return var_name
    if coeff == -1:
        return f"-{var_name}"
    return f"{format_fraction(coeff)}{var_name}"

def giai_hai_pha(c, A, b, standard_vars, substitutions, verbose=True, method='simplex', is_max=False, original_vars=None, force_two_phase=False, var_consts=None, zeta_offset=Fraction(0)):
    if original_vars is None:
        original_vars = standard_vars.copy()
        
    m = len(A)
    n = len(c)
    
    # Kiểm tra xem có cần Phase 1 không (nếu b_i < 0)
    if all(val >= 0 for val in b) and not force_two_phase:
        solver = BoGiaiDonHinh(c, A, b, non_basic_vars=standard_vars.copy(), original_vars=original_vars, substitutions=substitutions, var_consts=var_consts, zeta_offset=zeta_offset)
        return solver.giai(verbose=verbose, method=method), solver

    if verbose:
        print("\nPha 1:")
        
        # In bài toán bổ trợ
        print("Bài toán bổ trợ:")
        lines = []
        lines.append("min x₀")
        
        col_widths = [0] * n
        for j in range(n):
            for i in range(m):
                if A[i][j] != 0:
                    term = to_subscript(standard_vars[j]) if abs(A[i][j]) == 1 else f"{format_fraction(abs(A[i][j]))}{to_subscript(standard_vars[j])}"
                    col_widths[j] = max(col_widths[j], len(term) + 3)
                    
        for i in range(m):
            row_str = ""
            first = True
            for j in range(n):
                if A[i][j] != 0:
                    term = to_subscript(standard_vars[j]) if abs(A[i][j]) == 1 else f"{format_fraction(abs(A[i][j]))}{to_subscript(standard_vars[j])}"
                    if first:
                        sign = "-" if A[i][j] < 0 else " "
                        first = False
                    else:
                        sign = " - " if A[i][j] < 0 else " + "
                    row_str += f"{sign}{term:>{col_widths[j]-3}}"
                else:
                    row_str += " " * col_widths[j]
            lines.append(f"{row_str} - x₀ <= {format_fraction(b[i])}")
        
        lines.append(", ".join([to_subscript(v) for v in standard_vars]) + ", x₀ >= 0")
        
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
            
        print()
    
    # A_aux = A + cột x0
    A_aux = [row + [Fraction(-1)] for row in A]
    c_aux = [Fraction(0)] * n + [Fraction(1)] # x0
    
    non_basic_aux = standard_vars.copy() + ["x0"]
    solver = BoGiaiDonHinh(c_aux, A_aux, b, non_basic_vars=non_basic_aux, original_vars=original_vars, substitutions=substitutions, obj_name="k", var_consts=var_consts, zeta_offset=Fraction(0))
    
    has_negative_b = any(val < 0 for val in b)
    
    if has_negative_b:
        # Pivot đầu tiên để đạt tính khả thi
        l_idx = 0
        min_b = b[0]
        for i in range(1, m):
            if b[i] < min_b:
                min_b = b[i]
                l_idx = i
                
        e_idx = n # x0
        
        if verbose:
            solver.hien_thi_tu_vung(iteration=0, entering_var="x0", leaving_var=solver.basic_vars[l_idx])
        solver.pivot(e_idx, l_idx)
        res = solver.giai(method=method, verbose=verbose, iteration_start=1)
    else:
        # Nếu b_i >= 0, từ vựng xuất phát đã khả thi và tối ưu cho bài toán bổ trợ Pha 1
        if verbose:
            solver.hien_thi_tu_vung(iteration=0)
            print("\n=> Từ vựng tối ưu.")
            print()
        res = "Optimal"
    
    if solver.zeta != 0:
        if verbose:
            in_ket_luan_vo_nghiem(solver, is_max)
        return "Infeasible", None
    
    # Loại bỏ x0
    if "x0" in solver.basic_vars:
        l_idx = solver.basic_vars.index("x0")
        pivoted_out = False
        for e_idx in range(len(solver.non_basic_vars)):
            if solver.A[l_idx][e_idx] != 0:
                solver.pivot(e_idx, l_idx)
                pivoted_out = True
                break
        if not pivoted_out:
            solver.basic_vars.pop(l_idx)
            solver.A.pop(l_idx)
            solver.b.pop(l_idx)
            solver.m -= 1
    
    if verbose:
        print("Cho x₀ = 0, ta được:")
        lines_x0 = []
        for i, b_var in enumerate(solver.basic_vars):
            term_parts = []
            if solver.b[i] != 0:
                term_parts.append(format_fraction(solver.b[i]))
            for j in range(solver.n):
                if solver.non_basic_vars[j] == "x0": continue
                val = solver.A[i][j]
                if val != 0:
                    sign = " - " if val > 0 else " + "
                    abs_val = abs(val)
                    t = to_subscript(solver.non_basic_vars[j]) if abs_val == 1 else f"{format_fraction(abs_val)}{to_subscript(solver.non_basic_vars[j])}"
                    if not term_parts:
                        term_parts.append(f"-{t}" if sign == " - " else t)
                    else:
                        term_parts.append(f"{sign}{t}")
            if not term_parts: term_parts.append("0")
            lines_x0.append(f"{to_subscript(b_var)} = " + "".join(term_parts))
            
        num_lines = len(lines_x0)
        for idx, line in enumerate(lines_x0):
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
            
    if "x0" in solver.non_basic_vars:
        x0_idx = solver.non_basic_vars.index("x0")
        solver.non_basic_vars.pop(x0_idx)
        for row in solver.A:
            row.pop(x0_idx)
        solver.n -= 1
    
    new_c = [Fraction(0)] * solver.n
    new_zeta = Fraction(zeta_offset)
    
    for i, coeff in enumerate(c):
        var_name = standard_vars[i]
        if var_name in solver.non_basic_vars:
            idx = solver.non_basic_vars.index(var_name)
            new_c[idx] += coeff
        elif var_name in solver.basic_vars:
            idx = solver.basic_vars.index(var_name)
            new_zeta += coeff * solver.b[idx]
            for j in range(solver.n):
                new_c[j] -= coeff * solver.A[idx][j]
            
    solver.c = new_c
    solver.zeta = new_zeta
    
    # Chuyển sang Pha 2
    
    if verbose:
        print("\nPha 2:")
        lines_z = []
        
        # 1. Dòng 1: z ban đầu
        c_terms = []
        for j, coeff in enumerate(c):
            if coeff != 0:
                c_terms.append(format_coeff_term(coeff, to_subscript(standard_vars[j])))
        z_expr = " + ".join(c_terms).replace("+ -", "- ")
        lines_z.append(f"  zₘᵢₙ = {z_expr}")
        
        # 2. Dòng 2: z sau thế biến cơ sở (nếu có)
        subst_parts = []
        for j, coeff in enumerate(c):
            if coeff == 0: continue
            var_name = standard_vars[j]
            expr = ""
            if var_name in solver.non_basic_vars:
                expr = to_subscript(var_name)
            elif var_name in solver.basic_vars:
                idx = solver.basic_vars.index(var_name)
                term_p = []
                if solver.b[idx] != 0:
                    term_p.append(format_fraction(solver.b[idx]))
                for k in range(solver.n):
                    if solver.non_basic_vars[k] == "x0": continue
                    val = solver.A[idx][k]
                    if val != 0:
                        sign = " - " if val > 0 else " + "
                        abs_val = abs(val)
                        t = to_subscript(solver.non_basic_vars[k]) if abs_val == 1 else f"{format_fraction(abs_val)}{to_subscript(solver.non_basic_vars[k])}"
                        if not term_p:
                            term_p.append(f"-{t}" if sign == " - " else t)
                        else:
                            term_p.append(f"{sign}{t}")
                if not term_p: term_p.append("0")
                expr = "".join(term_p)
                if len(term_p) > 1 or (len(term_p) == 1 and term_p[0].startswith("-")):
                    expr = f"({expr})"
            
            if not subst_parts:
                c_str = "-" if coeff == -1 else ("" if coeff == 1 else format_fraction(coeff))
                subst_parts.append(f"{c_str}{expr}")
            else:
                sign = " - " if coeff < 0 else " + "
                c_str = "" if abs(coeff) == 1 else format_fraction(abs(coeff))
                subst_parts.append(f"{sign}{c_str}{expr}")
        z_subst = "".join(subst_parts)
        lines_z.append(f"       = {z_subst}")
        
        # 3. Dòng 3: z sau rút gọn
        new_c_terms = []
        if new_zeta != 0:
            new_c_terms.append(format_fraction(new_zeta))
        for j, coeff in enumerate(new_c):
            if coeff != 0:
                new_c_terms.append(format_coeff_term(coeff, to_subscript(solver.non_basic_vars[j])))
                
        if not new_c_terms:
            z_new_expr = "0"
        else:
            z_new_expr = " + ".join(new_c_terms).replace("+ -", "- ")
        lines_z.append(f"       = {z_new_expr}")
        
        # In các dòng z không bị trùng lặp
        printed_lines = []
        for line in lines_z:
            parts = line.split("=")
            expr_part = parts[1].strip() if len(parts) > 1 else line.strip()
            if printed_lines and printed_lines[-1] == expr_part:
                continue
            print(line)
            printed_lines.append(expr_part)
        print()
        
    solver.obj_name = "z"
    res = solver.giai(verbose=verbose, method=method)
    return res, solver

def in_ket_luan_vo_nghiem(solver, is_max):
    nb_vars_str = " = ".join([to_subscript(v) for v in solver.non_basic_vars])
    if nb_vars_str:
        print(f"Cho {nb_vars_str} = 0, ta được:")
    else:
        print("Ta được:")
        
    lines_dict = []
    for i, b_var in enumerate(solver.basic_vars):
        lines_dict.append(f"{to_subscript(b_var)} = {format_fraction(solver.b[i])}")
    
    num_lines = len(lines_dict)
    for idx, line in enumerate(lines_dict):
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
        print(f"   {brace} {line}")
    print()
    
    print("Kết luận:")
    x0_val = format_fraction(solver.zeta)
    z_display = "zₘₐₓ" if is_max else "zₘᵢₙ"
    sign = "-∞" if is_max else "+∞"
    print(f"    Do x₀ = {x0_val} ≠ 0 nên miền chấp nhận được là ∅. Suy ra bài toán vô nghiệm và giá trị tối ưu là {z_display} = {sign}")
