import numpy as np
from fractions import Fraction
from tien_ich import format_fraction, to_subscript

class BoGiaiDonHinh:
    def __init__(self, c, A, b, non_basic_vars=None, basic_vars=None, original_vars=None, substitutions=None, obj_name="z", var_consts=None, zeta_offset=Fraction(0)):
        # Chuyển đổi sang Fraction
        self.c = [Fraction(val) for val in c]
        self.A = [[Fraction(val) for val in row] for row in A]
        self.b = [Fraction(val) for val in b]
        self.zeta = Fraction(zeta_offset)
        
        self.m = len(self.A)
        self.n = len(self.c)
        self.original_vars = original_vars 
        self.substitutions = substitutions 
        self.var_consts = var_consts if var_consts else {}
        self.obj_name = obj_name
        
        if non_basic_vars is None:
            self.non_basic_vars = [f"y{i+1}" for i in range(self.n)]
        else:
            self.non_basic_vars = non_basic_vars
            
        if basic_vars is None:
            self.basic_vars = [f"w{i+1}" for i in range(self.m)]
        else:
            self.basic_vars = basic_vars

    def pivot(self, entering_idx, leaving_idx):
        b_L = self.b[leaving_idx]
        a_LE = self.A[leaving_idx][entering_idx]
        
        new_b_L = b_L / a_LE
        new_A_LE = Fraction(1) / a_LE
        
        # Cập nhật dòng xoay
        new_row_A = [val / a_LE for val in self.A[leaving_idx]]
        new_row_A[entering_idx] = new_A_LE
        
        # Cập nhật các dòng khác
        for i in range(self.m):
            if i == leaving_idx: continue
            multiplier = self.A[i][entering_idx]
            self.b[i] -= multiplier * new_b_L
            for j in range(self.n):
                if j == entering_idx: continue
                self.A[i][j] -= multiplier * new_row_A[j]
            self.A[i][entering_idx] = -multiplier * new_A_LE
        
        self.b[leaving_idx] = new_b_L
        self.A[leaving_idx] = new_row_A
        
        # Cập nhật hàm mục tiêu
        c_E = self.c[entering_idx]
        self.zeta += c_E * new_b_L
        for j in range(self.n):
            if j == entering_idx: continue
            self.c[j] -= c_E * new_row_A[j]
        self.c[entering_idx] = -c_E * new_A_LE
        
        e_var = self.non_basic_vars[entering_idx]
        l_var = self.basic_vars[leaving_idx]
        self.non_basic_vars[entering_idx] = l_var
        self.basic_vars[leaving_idx] = e_var

    def hien_thi_tu_vung(self, iteration, entering_var=None, leaving_var=None, ratios=None):
        if iteration == 0:
            print("Từ vựng xuất phát:")
        else:
            print()
        
        nb_display = [to_subscript(v) for v in self.non_basic_vars]
        b_display = [to_subscript(v) for v in self.basic_vars]
        
        # Helper format hệ số để bỏ số 1 (ví dụ 1x1 -> x1)
        def format_term(val, var_name):
            abs_val = abs(val)
            if abs_val == 1:
                return var_name
            return f"{format_fraction(abs_val)}{var_name}"
        
        # 1. Tính toán độ rộng động cho từng cột
        cols_order = list(range(self.n))
        if "x0" in self.non_basic_vars:
            x0_idx = self.non_basic_vars.index("x0")
            cols_order.remove(x0_idx)
            cols_order.append(x0_idx)
            
        # Cột hằng số
        all_consts = []
        if self.zeta != 0: all_consts.append(format_fraction(self.zeta))
        for val in self.b:
            if val != 0: all_consts.append(format_fraction(val))
        const_w = max((len(s) for s in all_consts), default=0)
        
        # Các cột biến không cơ sở
        col_widths = {}
        for j in cols_order:
            terms_in_col = []
            val_z = self.c[j]
            if val_z != 0:
                terms_in_col.append(format_term(val_z, nb_display[j]))
            for i in range(self.m):
                val_a = self.A[i][j]
                if val_a != 0:
                    terms_in_col.append(format_term(val_a, nb_display[j]))
            
            if not terms_in_col:
                col_widths[j] = 8
            else:
                col_widths[j] = max(len(t) for t in terms_in_col) + 3 # +3 cho dấu " + " hoặc " - "

        z_prefix = f"  {self.obj_name}  = "
        
        # 2. Mũi tên ↓
        entering_col_idx = -1
        if entering_var:
            try:
                entering_col_idx = self.non_basic_vars.index(entering_var)
            except ValueError: pass

        if entering_col_idx != -1:
            offset = len(z_prefix) + const_w
            for j in cols_order:
                if j == entering_col_idx:
                    offset += col_widths[j] - 2
                    break
                offset += col_widths[j]
            print(" " * offset + "↓")
            
        # 3. Dòng hàm mục tiêu z
        const_z = "" if self.zeta == 0 else format_fraction(self.zeta)
        print(f"{z_prefix}{const_z:>{const_w}}", end="")
        for j in cols_order:
            val = self.c[j]
            if val == 0:
                print(" " * col_widths[j], end="")
            else:
                sign = " + " if val > 0 else " - "
                term = format_term(val, nb_display[j])
                print(f"{sign}{term:>{col_widths[j]-3}}", end="")
        print()
        
        # 4. Đường kẻ phân cách z
        line_len = const_w + sum(col_widths.values()) + 5
        print("  " + "─" * line_len)
        
        # 5. Các dòng ràng buộc
        for i in range(self.m):
            prefix = "← " if self.basic_vars[i] == leaving_var else "  "
            row_prefix = f"{prefix}{b_display[i]:<2} = "
            const_b = "" if self.b[i] == 0 else format_fraction(self.b[i])
            print(f"{row_prefix}{const_b:>{const_w}}", end="")
            
            for j in cols_order:
                val = self.A[i][j]
                if val == 0:
                    print(" " * col_widths[j], end="")
                else:
                    sign = " - " if val > 0 else " + "
                    term = format_term(val, nb_display[j])
                    print(f"{sign}{term:>{col_widths[j]-3}}", end="")
            
            if ratios and ratios[i] is not None:
                print(f"    ({format_fraction(ratios[i])})")
            else:
                print()

    def lay_chi_so_bien(self, ten_bien):
        digits_str = "".join([c for c in ten_bien if c.isdigit()])
        num = int(digits_str) if digits_str else 9999
        if ten_bien.startswith('x'): return num
        if ten_bien.startswith('y'): return num
        if ten_bien.startswith('w'): return 1000 + num
        return 9999

    def giai(self, method='simplex', verbose=True, iteration_start=0):
        iteration = iteration_start
        visited_bases = set()
        
        while True:
            current_basis = frozenset(self.basic_vars)
            if current_basis in visited_bases:
                if verbose:
                    self.hien_thi_tu_vung(iteration)
                    print("\nBài toán xoay vòng.")
                return "Cycling"
            visited_bases.add(current_basis)
            
            # 1. Chọn biến vào
            candidates = [i for i, val in enumerate(self.c) if val < 0]
            if not candidates:
                if verbose: 
                    self.hien_thi_tu_vung(iteration)
                    print("\n=> Từ vựng tối ưu.")
                return "Optimal"
            
            if method == 'bland':
                e_idx = candidates[0]
                for idx in candidates[1:]:
                    if self.lay_chi_so_bien(self.non_basic_vars[idx]) < self.lay_chi_so_bien(self.non_basic_vars[e_idx]):
                        e_idx = idx
            else:
                best_val = self.c[candidates[0]]
                e_idx = candidates[0]
                for idx in candidates[1:]:
                    if self.c[idx] < best_val:
                        best_val = self.c[idx]
                        e_idx = idx
            
            entering_var = self.non_basic_vars[e_idx]
            
            # 2. Chọn biến ra (Ratio Test)
            ratios = []
            for i in range(self.m):
                a_ie = self.A[i][e_idx]
                if a_ie > 0:
                    ratios.append(self.b[i] / a_ie)
                else:
                    ratios.append(None)
            
            valid_ratios = [r for r in ratios if r is not None]
            if not valid_ratios:
                if verbose: self.hien_thi_tu_vung(iteration, entering_var=entering_var)
                return "Unbounded"
            
            min_ratio = min(valid_ratios)
            l_candidates = [i for i, r in enumerate(ratios) if r is not None and r == min_ratio]
            
            if method == 'bland':
                l_idx = l_candidates[0]
                for idx in l_candidates[1:]:
                    if self.lay_chi_so_bien(self.basic_vars[idx]) < self.lay_chi_so_bien(self.basic_vars[l_idx]):
                        l_idx = idx
            else:
                l_idx = l_candidates[0]
            
            leaving_var = self.basic_vars[l_idx]
            
            # 3. Hiển thị từ vựng kèm mũi tên và tỉ số Ratio Test
            if verbose:
                self.hien_thi_tu_vung(iteration, entering_var=entering_var, leaving_var=leaving_var, ratios=ratios)
            
            # 4. Xoay (Pivot)
            self.pivot(e_idx, l_idx)
            iteration += 1
            if iteration > 100: return "LimitReached"

    def in_ket_luan(self, is_max):
        # Kiểm tra trạng thái tối ưu hiện tại
        candidates = [i for i, val in enumerate(self.c) if val < 0]
        if candidates:
            print("\nKết luận:")
            sign = "+∞" if is_max else "-∞"
            z_display = "zₘₐₓ" if is_max else "zₘᵢₙ"
            print(f"    Bài toán có biến vào nhưng không có biến ra nên bài toán không giới nội và giá trị tối ưu là {z_display} = {sign}")
            return

        # Tính toán giá trị x gốc
        final_values = {}
        for var in self.original_vars:
            mapping = self.substitutions.get(var, [])
            val = self.var_consts.get(var, Fraction(0))
            for new_v, mult in mapping:
                y_val = Fraction(0)
                if new_v in self.basic_vars:
                    y_val = self.b[self.basic_vars.index(new_v)]
                val += mult * y_val
            final_values[var] = val
        final_z = -self.zeta if is_max else self.zeta
        z_display = "zₘₐₓ" if is_max else "zₘᵢₙ"
        
        # Tập biến xuất phát từ original_vars (qua substitutions) - không tính biến bù w
        standard_derived_vars = set()
        for var in self.original_vars:
            for new_v, _ in self.substitutions.get(var, []):
                standard_derived_vars.add(new_v)
        # Nếu substitutions trống (biến trực tiếp), thì original_vars chính là biến chuẩn
        if not standard_derived_vars:
            standard_derived_vars = set(self.original_vars)

        free_nb_indices = []
        for j, val in enumerate(self.c):
            nb_var = self.non_basic_vars[j]
            # Chỉ xét biến gốc/chuẩn (không xét biến bù w)
            if nb_var not in standard_derived_vars:
                continue
            if val == 0:
                max_t = None
                for i in range(self.m):
                    if self.A[i][j] > 0:
                        ratio = self.b[i] / self.A[i][j]
                        if max_t is None or ratio < max_t:
                            max_t = ratio
                if max_t is None or max_t > 0:
                    free_nb_indices.append(j)
                    
        has_multiple = len(free_nb_indices) > 0
        if has_multiple:
            # 1. Tách các biến phi cơ sở
            free_nb_vars = [self.non_basic_vars[j] for j in free_nb_indices]
            
            zero_nb_indices = [j for j, val in enumerate(self.c) if val != 0 or j not in free_nb_indices]
            zero_nb_vars = [self.non_basic_vars[j] for j in zero_nb_indices]
            
            # Tính toán biểu thức cho các biến gốc
            def get_expr_dict(var_name):
                if var_name in free_nb_vars:
                    return (Fraction(0), {var_name: Fraction(1)})
                elif var_name in zero_nb_vars:
                    return (Fraction(0), {})
                elif var_name in self.basic_vars:
                    idx = self.basic_vars.index(var_name)
                    coeffs = {}
                    for k in range(len(free_nb_indices)):
                        p_var = free_nb_vars[k]
                        coeff = -self.A[idx][free_nb_indices[k]]
                        if coeff != 0:
                            coeffs[p_var] = coeff
                    return (self.b[idx], coeffs)
                return (Fraction(0), {})

            final_exprs = {}
            original_free_vars = []
            
            for var in self.original_vars:
                mapping = self.substitutions.get(var, [])
                total_const = self.var_consts.get(var, Fraction(0))
                total_coeffs = {}
                for new_v, mult in mapping:
                    const, coeffs = get_expr_dict(new_v)
                    total_const += mult * const
                    for p_var, coeff in coeffs.items():
                        total_coeffs[p_var] = total_coeffs.get(p_var, Fraction(0)) + mult * coeff
                
                # Lọc bỏ hệ số = 0 (do x = x⁺ - x⁻ có thể triệt tiêu nhau)
                total_coeffs = {k: v for k, v in total_coeffs.items() if v != 0}
                final_exprs[var] = (total_const, total_coeffs)
                
                if len(total_coeffs) == 1 and list(total_coeffs.values())[0] == 1 and total_const == 0:
                    p_name = list(total_coeffs.keys())[0]
                    if p_name == var:
                        original_free_vars.append(var)

            # Kiểm tra lại: nếu tất cả biến gốc không còn phụ thuộc vào tham số nào
            # (các tham số đã triệt tiêu nhau do phép đặt biến x = x⁺ - x⁻)
            # → đây thực ra là nghiệm DUY NHẤT, không phải vô số nghiệm
            truly_multiple = any(len(final_exprs[v][1]) > 0 for v in self.original_vars)
            if not truly_multiple:
                # Tính final_values từ final_exprs (hệ số hằng số)
                final_values_unique = {v: final_exprs[v][0] for v in self.original_vars}
                final_z = -self.zeta if is_max else self.zeta
                # In nghiệm duy nhất: bước 1 - cho phi cơ sở = 0
                nb_vars_str = " = ".join([to_subscript(v) for v in self.non_basic_vars])
                if nb_vars_str:
                    print(f"Cho {nb_vars_str} = 0, ta được:")
                else:
                    print("Ta được:")
                lines_dict = []
                for i, b_var in enumerate(self.basic_vars):
                    lines_dict.append(f"{to_subscript(b_var)} = {format_fraction(self.b[i])}")
                lines_dict.append(f"{z_display} = {format_fraction(self.zeta)}")
                num_lines = len(lines_dict)
                for idx, line in enumerate(lines_dict):
                    if num_lines == 1: brace = "{"
                    elif num_lines == 2: brace = "⎧" if idx == 0 else "⎩"
                    else:
                        if idx == 0: brace = "⎧"
                        elif idx == num_lines - 1: brace = "⎩"
                        elif idx == num_lines // 2: brace = "⎨"
                        else: brace = "⎪"
                    print(f"   {brace} {line}")
                print()
                # Bước 2 - suy ra
                lines_final = [f"{z_display} = {format_fraction(final_z)}"]
                for v in self.original_vars:
                    lines_final.append(f"{to_subscript(v)} = {format_fraction(final_values_unique[v])}")
                num_lines_final = len(lines_final)
                for idx, line in enumerate(lines_final):
                    if num_lines_final == 1: brace = "{"
                    elif num_lines_final == 2: brace = "⎧" if idx == 0 else "⎩"
                    else:
                        if idx == 0: brace = "⎧"
                        elif idx == num_lines_final - 1: brace = "⎩"
                        elif idx == num_lines_final // 2: brace = "⎨"
                        else: brace = "⎪"
                    prefix = "=> " if idx == num_lines_final // 2 else "   "
                    print(f"{prefix}{brace} {line}")
                # Kết luận
                print("\nKết luận:")
                final_vars_str = ", ".join([f"{to_subscript(v)} = {format_fraction(final_values_unique[v])}" for v in self.original_vars])
                print(f"    Vậy bài toán có nghiệm duy nhất tại {final_vars_str} và giá trị tối ưu là {z_display} = {format_fraction(final_z)}")
                return

            # Lọc bỏ các tham số không xuất hiện trong biểu thức nghiệm cuối cùng
            actual_params = set()
            for var in self.original_vars:
                const, coeffs = final_exprs[var]
                for p_var, coeff in coeffs.items():
                    if coeff != 0:
                        actual_params.add(p_var)
            
            filtered_free_nb_vars = []
            filtered_free_nb_indices = []
            for k, p in enumerate(free_nb_vars):
                if p in actual_params:
                    filtered_free_nb_vars.append(p)
                    filtered_free_nb_indices.append(free_nb_indices[k])
            free_nb_vars = filtered_free_nb_vars
            free_nb_indices = filtered_free_nb_indices

            # Xác định các biến được tách từ biến tự do ban đầu (ví dụ x₃⁺, x₃⁻)
            split_vars = set()
            for var, mapping in self.substitutions.items():
                if len(mapping) == 2:
                    split_vars.add(mapping[0][0])
                    split_vars.add(mapping[1][0])

            # Map free non-basic vars to their subscripts (never use parameter t)
            param_map = {p: to_subscript(p) for p in free_nb_vars}
                
            def format_expr_with_vars(const, var_coeffs):
                terms = []
                if const != 0 or not var_coeffs:
                    terms.append(format_fraction(const))
                for var, coeff in var_coeffs:
                    if coeff == 0: continue
                    sign = " - " if coeff < 0 else " + "
                    if not terms:
                        sign = "-" if coeff < 0 else ""
                    abs_coeff = abs(coeff)
                    coeff_str = "" if abs_coeff == 1 else format_fraction(abs_coeff)
                    terms.append(f"{sign}{coeff_str}{to_subscript(var)}")
                return "".join(terms).replace("+ -", "- ").replace("- -", "+ ")

            def format_expr_t(const, var_coeffs):
                terms = []
                if const != 0 or not var_coeffs:
                    terms.append(format_fraction(const))
                for var, coeff in var_coeffs:
                    if coeff == 0: continue
                    sign = " - " if coeff < 0 else " + "
                    if not terms:
                        sign = "-" if coeff < 0 else ""
                    abs_coeff = abs(coeff)
                    coeff_str = "" if abs_coeff == 1 else format_fraction(abs_coeff)
                    t_name = param_map.get(var, to_subscript(var))
                    terms.append(f"{sign}{coeff_str}{t_name}")
                return "".join(terms).replace("+ -", "- ").replace("- -", "+ ")

            # Bước 1: Cho các biến phi cơ sở khác = 0
            if zero_nb_vars:
                nb_vars_str = " = ".join([to_subscript(v) for v in zero_nb_vars])
                print(f"Cho {nb_vars_str} = 0, ta được:")
            else:
                print("Ta được:")
                
            # Bước 2: In giá trị các biến cơ sở và z_min từ từ vựng (ở dạng biểu thức)
            lines_dict = []
            for i, b_var in enumerate(self.basic_vars):
                var_coeffs = [(self.non_basic_vars[j], -self.A[i][j]) for j in free_nb_indices]
                expr_str = format_expr_with_vars(self.b[i], var_coeffs)
                lines_dict.append(f"{to_subscript(b_var)} = {expr_str} >= 0")
            lines_dict.append(f"zₘᵢₙ = {format_fraction(self.zeta)}")
            
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
            
            # Bước 3: Bước suy ra (dùng param_map để hiển thị t thay vì w1, w2...)
            lines_final = []
            for var in self.original_vars:
                const, coeffs = final_exprs[var]
                expr_str = format_expr_t(const, list(coeffs.items()))
                sub_var = to_subscript(var)
                if expr_str == sub_var:
                    lines_final.append(f"{sub_var} tự do")
                else:
                    lines_final.append(f"{sub_var} = {expr_str}")
            lines_final.append(f"{z_display} = {format_fraction(final_z)}")
            
            num_lines_final = len(lines_final)
            for idx, line in enumerate(lines_final):
                if num_lines_final == 1:
                    brace = "{"
                elif num_lines_final == 2:
                    brace = "⎧" if idx == 0 else "⎩"
                else:
                    if idx == 0:
                        brace = "⎧"
                    elif idx == num_lines_final - 1:
                        brace = "⎩"
                    elif idx == num_lines_final // 2:
                        brace = "⎨"
                    else:
                        brace = "⎪"
                mid_idx = num_lines_final // 2
                prefix = "=> " if idx == mid_idx else "   "
                print(f"{prefix}{brace} {line}")
                
            # Bước 4: Kết luận
            z_val_display = format_fraction(final_z)
            print(f"\nKết luận:")
            print(f"    Bài toán có vô số nghiệm, giá trị tối ưu là {z_display} = {z_val_display} và nghiệm tối ưu là:")
            
            lines_conclusion = []
            for var in self.original_vars:
                const, coeffs = final_exprs[var]
                expr_str = format_expr_t(const, list(coeffs.items()))
                sub_var = to_subscript(var)
                if expr_str == sub_var:
                    lines_conclusion.append(f"{sub_var} tự do")
                else:
                    lines_conclusion.append(f"{sub_var} = {expr_str}")
                
            num_conclusion = len(lines_conclusion)
            for idx, line in enumerate(lines_conclusion):
                if num_conclusion == 1:
                    brace = "{"
                elif num_conclusion == 2:
                    brace = "⎧" if idx == 0 else "⎩"
                else:
                    if idx == 0:
                        brace = "⎧"
                    elif idx == num_conclusion - 1:
                        brace = "⎩"
                    elif idx == num_conclusion // 2:
                        brace = "⎨"
                    else:
                        brace = "⎪"
                print(f"       {brace} {line}")
                
            params_str = ", ".join(param_map.values())
            
            # Calculate conditions for t
            simple_bounds = []
            complex_conds = []
            if len(free_nb_vars) == 1:
                p_var = free_nb_vars[0]
                t_name = param_map[p_var]
                L = Fraction(0)
                U = None
                p_idx = free_nb_indices[0]
                
                for i in range(len(self.basic_vars)):
                    if self.basic_vars[i] in split_vars:
                        continue
                    coeff_p = -self.A[i][p_idx]
                    if coeff_p > 0:
                        L = max(L, -self.b[i] / coeff_p)
                    elif coeff_p < 0:
                        val = -self.b[i] / coeff_p
                        if U is None or val < U:
                            U = val
                            
                L_str = format_fraction(L)
                if U is not None:
                    U_str = format_fraction(U)
                    simple_bounds.append(f"{L_str} <= {t_name} <= {U_str}")
                else:
                    simple_bounds.append(f"{t_name} >= {L_str}")
            else:
                lower_bounds = {param_map[p]: Fraction(0) for p in free_nb_vars}
                upper_bounds = {param_map[p]: None for p in free_nb_vars}
                complex_ineqs = []

                def format_ineq_t(const, non_zero_vars):
                    if not non_zero_vars: return ""
                    all_negative = all(c < 0 for v, c in non_zero_vars)
                    if all_negative:
                        flipped = [(v, -c) for v, c in non_zero_vars]
                        lhs = format_expr_t(0, flipped)
                        return f"{lhs} <= {format_fraction(const)}"
                    else:
                        lhs = format_expr_t(0, non_zero_vars)
                        return f"{lhs} >= {format_fraction(-const)}"
                
                for i, b_var in enumerate(self.basic_vars):
                    if b_var in split_vars:
                        continue
                    var_coeffs = [(free_nb_vars[k], -self.A[i][free_nb_indices[k]]) for k in range(len(free_nb_indices))]
                    non_zero = [(v, c) for v, c in var_coeffs if c != 0]
                    
                    if not non_zero: continue
                    
                    if len(non_zero) == 1:
                        v, c = non_zero[0]
                        t_name = param_map[v]
                        val = -self.b[i] / c
                        if c > 0:
                            lower_bounds[t_name] = max(lower_bounds[t_name], val)
                        else:
                            if upper_bounds[t_name] is None or val < upper_bounds[t_name]:
                                upper_bounds[t_name] = val
                    else:
                        ineq = format_ineq_t(self.b[i], non_zero)
                        if ineq:
                            complex_ineqs.append(ineq)
                            
                zero_lower_only = []
                for p in free_nb_vars:
                    t_name = param_map[p]
                    L = lower_bounds[t_name]
                    U = upper_bounds[t_name]
                    
                    if L == 0 and U is None:
                        zero_lower_only.append(t_name)
                    else:
                        L_str = format_fraction(L)
                        if U is not None:
                            U_str = format_fraction(U)
                            simple_bounds.append(f"{L_str} <= {t_name} <= {U_str}")
                        else:
                            simple_bounds.append(f"{t_name} >= {L_str}")
                            
                if zero_lower_only:
                    simple_bounds.append(f"{', '.join(zero_lower_only)} >= 0")
                    
                complex_conds.extend(complex_ineqs)
                    
            t_conds = complex_conds + simple_bounds
            print(f"    Trong đó, {params_str} thỏa:")
            num_conds = len(t_conds)
            for idx, line in enumerate(t_conds):
                if num_conds == 1:
                    print(f"      {line}")
                else:
                    if num_conds == 2:
                        brace = "⎧" if idx == 0 else "⎩"
                    else:
                        if idx == 0:
                            brace = "⎧"
                        elif idx == num_conds - 1:
                            brace = "⎩"
                        elif idx == num_conds // 2:
                            brace = "⎨"
                        else:
                            brace = "⎪"
                    print(f"       {brace} {line}")
            return
            
        # 1. Cho các biến phi cơ sở = 0
        nb_vars_str = " = ".join([to_subscript(v) for v in self.non_basic_vars])
        if nb_vars_str:
            print(f"Cho {nb_vars_str} = 0, ta được:")
        else:
            print("Ta được:")
            
        # 2. In giá trị các biến cơ sở và z_min từ từ vựng
        lines_dict = []
        for i, b_var in enumerate(self.basic_vars):
            lines_dict.append(f"{to_subscript(b_var)} = {format_fraction(self.b[i])}")
        lines_dict.append(f"zₘᵢₙ = {format_fraction(self.zeta)}")
        
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
            
        # 3. Bước suy ra
        lines_final = []
        lines_final.append(f"{z_display} = {format_fraction(final_z)}")
        for v in self.original_vars:
            lines_final.append(f"{to_subscript(v)} = {format_fraction(final_values[v])}")
            
        num_lines_final = len(lines_final)
        for idx, line in enumerate(lines_final):
            if num_lines_final == 1:
                brace = "{"
            elif num_lines_final == 2:
                brace = "⎧" if idx == 0 else "⎩"
            else:
                if idx == 0:
                    brace = "⎧"
                elif idx == num_lines_final - 1:
                    brace = "⎩"
                elif idx == num_lines_final // 2:
                    brace = "⎨"
                else:
                    brace = "⎪"
            mid_idx = num_lines_final // 2
            prefix = "=> " if idx == mid_idx else "   "
            print(f"{prefix}{brace} {line}")

        # 4. Kết luận
        print("\nKết luận:")
        final_vars_str = ", ".join([f"{to_subscript(v)} = {format_fraction(final_values[v])}" for v in self.original_vars])
        print(f"    Vậy bài toán có nghiệm duy nhất tại {final_vars_str} và giá trị tối ưu là {z_display} = {format_fraction(final_z)}")
