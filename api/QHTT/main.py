import sys
from fractions import Fraction
from tien_ich import parse_problem, print_standard_form, visualize_geometric, format_fraction, to_subscript
from phuong_phap_hai_pha import giai_hai_pha

def main():
    print("="*60)
    print(" CHƯƠNG TRÌNH GIẢI BÀI TOÁN QUY HOẠCH TUYẾN TÍNH ")
    print("="*60)
    print("Nhập đề bài (Ví dụ: max x1 - x2, kết thúc bằng dòng trắng): ")
    
    problem_lines = []
    while True:
        try:
            line = input()
            if not line.strip(): break
            problem_lines.append(line)
        except EOFError:
            break
            
    if not problem_lines:
        print("\n[!] Sử dụng bài toán mẫu trong ảnh:")
        # min -x1 + x2; -x1 - 2x2 <= 6; x1 - 2x2 <= 4; -x1 + x2 <= 1; x1 <= 0; x2 <= 0
        problem_input = "min -x1 + x2\n-x1 - 2x2 <= 6\nx1 - 2x2 <= 4\n-x1 + x2 <= 1\nx1 <= 0\nx2 <= 0"
        print(problem_input)
    else:
        problem_input = "\n".join(problem_lines)
    
    try:
        c, A, b, var_names, var_mapping, is_max, actual_vars, var_consts, zeta_offset, orig_obj_terms, parsed_constraints = parse_problem(problem_input)
        
        
        # Hiển thị bước đặt biến nếu có biến đổi
        has_substitution = False
        substitution_lines = []
        for v in var_names:
            mapping = var_mapping.get(v, [])
            if len(mapping) == 1:
                new_v, mult = mapping[0]
                if mult == -1:
                    has_substitution = True
                    substitution_lines.append(f"{to_subscript(new_v)} = -{to_subscript(v)}, {to_subscript(new_v)} >= 0")
            elif len(mapping) == 2:
                has_substitution = True
                new_v1, mult1 = mapping[0]
                new_v2, mult2 = mapping[1]
                substitution_lines.append(f"{to_subscript(v)} = {to_subscript(new_v1)} - {to_subscript(new_v2)} với {to_subscript(new_v1)}, {to_subscript(new_v2)} >= 0")

        if is_max:
            orig_c_terms = []
            new_c_terms = []
            for j, coeff in enumerate(c):
                if coeff != 0:
                    orig_coeff = -coeff
                    term_str_orig = to_subscript(actual_vars[j]) if abs(orig_coeff) == 1 else f"{format_fraction(abs(orig_coeff))}{to_subscript(actual_vars[j])}"
                    if not orig_c_terms:
                        orig_c_terms.append(f"-{term_str_orig}" if orig_coeff < 0 else term_str_orig)
                    else:
                        sign = " - " if orig_coeff < 0 else " + "
                        orig_c_terms.append(f"{sign}{term_str_orig}")
                        
                    term_str_new = to_subscript(actual_vars[j]) if abs(coeff) == 1 else f"{format_fraction(abs(coeff))}{to_subscript(actual_vars[j])}"
                    if not new_c_terms:
                        new_c_terms.append(f"-{term_str_new}" if coeff < 0 else term_str_new)
                    else:
                        sign = " - " if coeff < 0 else " + "
                        new_c_terms.append(f"{sign}{term_str_new}")
                        
            orig_obj = "".join(orig_c_terms)
            new_obj = "".join(new_c_terms)
            print(f"+) max {orig_obj} <=> -min({new_obj})")
            print()

        if has_substitution:
            for idx, line in enumerate(substitution_lines):
                if idx == 0:
                    print(f"Đặt {line}")
                else:
                    print(f"    {line}")
            
        has_ge = any(">=" in line and "x" in line and not line.strip().endswith(">= 0") for line in problem_lines)
        print("\nTa chuyển bài toán ban đầu về dạng chuẩn:")
        print_standard_form(c, A, b, actual_vars)
        
        has_negative_b = any(val < 0 for val in b)
        has_zero_b = any(val == 0 for val in b)
        
        if has_zero_b:
            # Bài toán có b_i = 0 từ đầu, rất dễ suy biến nên dùng Bland
            res, solver = giai_hai_pha(c, A, b, actual_vars, var_mapping, verbose=True, method='bland', is_max=is_max, original_vars=var_names)
            if res != "Infeasible":
                solver.in_ket_luan(is_max)
                
            ans = input("\n[?] Bạn có muốn giải lại bài toán này bằng Phương pháp đơn hình không? (y/n): ").strip().lower()
            if ans == 'y':
                print("\n")
                res_loop, solver_loop = giai_hai_pha(c, A, b, actual_vars, var_mapping, verbose=True, method='simplex', is_max=is_max, original_vars=var_names)
                if res_loop not in ["Cycling", "Infeasible"]:
                    solver_loop.in_ket_luan(is_max)
                    res, solver = res_loop, solver_loop
        else:
            res, solver = giai_hai_pha(c, A, b, actual_vars, var_mapping, verbose=True, method='simplex', is_max=is_max, original_vars=var_names)
            if res == "Cycling":
                ans = input("\n[?] Bạn có muốn giải lại bài toán này bằng Phương pháp xoay Bland không? (y/n): ").strip().lower()
                if ans == 'y':
                    print("\n")
                    res_bland, solver_bland = giai_hai_pha(c, A, b, actual_vars, var_mapping, verbose=True, method='bland', is_max=is_max, original_vars=var_names)
                    if res_bland != "Infeasible":
                        solver_bland.in_ket_luan(is_max)
                        res, solver = res_bland, solver_bland
            elif res != "Infeasible":
                solver.in_ket_luan(is_max)
                
        # Gọi phương pháp hình học nếu là bài toán 2 biến
        if len(var_names) == 2:
            ans_geom = input("\n[?] Bạn có muốn giải bài toán này bằng Phương pháp hình học không? (y/n): ").strip().lower()
            if ans_geom == 'y':
                from phuong_phap_hinh_hoc import giai_phuong_phap_hinh_hoc
                giai_phuong_phap_hinh_hoc(problem_input, res, solver, is_max)
    except Exception as e:
        print(f"\n[!] Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
