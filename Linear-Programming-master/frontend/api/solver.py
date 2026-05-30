"""
solver.py — Đơn hình (Từ vựng / Dictionary) với số học phân số chính xác.

Theo đặc tả PDF:
  · Dạng chuẩn: chuyển tất cả sang <=, biến bù w_i = b_i - sum(a_ij*x_j)
  · Biến vào: hệ số âm nhất trong dòng z (Standard) / chỉ số nhỏ nhất (Bland)
  · Biến ra:  min-ratio b_i/a_ij với a_ij > 0 (dương trong bảng TV)
  · Two-Phase: Pha 1 dùng biến nhân tạo a_i để tìm nghiệm cơ sở; Pha 2 tối ưu bài gốc
  · Kết luận:  duy nhất (mọi h/số nb > 0), vô số (có h/số nb = 0), vô nghiệm, không  giới nội
"""
from fractions import Fraction

MAX_ITER = 500
_EPS = Fraction(1, 10 ** 9)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _frac(x):
    if isinstance(x, Fraction):
        return x
    return Fraction(x).limit_denominator(10 ** 9)


def _fmt(f: Fraction) -> str:
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def _var_name(idx: int, n: int, n_slack: int = 0) -> str:
    """x1..xn = biến quyết định, w1..wm = biến bù, a1..ak = biến nhân tạo."""
    if idx < n:
        return f"x{idx + 1}"
    if idx < n + n_slack:
        return f"w{idx - n + 1}"
    return f"a{idx - n - n_slack + 1}"


def _snap(tableau, basic_vars, n, n_slack=0, pivot_col=None, pivot_row=None, note="", step_idx=0, obj_name="z"):
    """Tạo snapshot một bước TV để trả về API."""
    basic_names = [_var_name(bv, n, n_slack) for bv in basic_vars]
    rows = [[_fmt(v) for v in row] for row in tableau]
    
    n_cols = len(tableau[0]) - 1
    non_basic_vars = [j for j in range(n_cols) if j not in basic_vars]
    
    def format_term(val, var_name):
        abs_val = abs(val)
        if abs_val == Fraction(1): return var_name
        return f"{_fmt(abs_val)}{var_name}"
    
    cols_order = non_basic_vars
    all_consts = []
    if tableau[-1][-1] != Fraction(0): all_consts.append(_fmt(tableau[-1][-1]))
    for i in range(len(tableau)-1):
        if tableau[i][-1] != Fraction(0): all_consts.append(_fmt(tableau[i][-1]))
    const_w = max((len(s) for s in all_consts), default=0)
    if const_w == 0: const_w = 1
    
    col_widths = {}
    for j in cols_order:
        terms_in_col = []
        val_z = tableau[-1][j]
        if val_z != Fraction(0): terms_in_col.append(format_term(val_z, _var_name(j, n, n_slack)))
        for i in range(len(tableau)-1):
            val_a = tableau[i][j]
            if val_a != Fraction(0): terms_in_col.append(format_term(val_a, _var_name(j, n, n_slack)))
        
        if not terms_in_col:
            col_widths[j] = 8
        else:
            col_widths[j] = max(len(t) for t in terms_in_col) + 3
            
    z_prefix = f"  {obj_name} = "
    dict_lines = []
    
    # Mũi tên ↓ cho biến vào
    if pivot_col is not None:
        offset = len(z_prefix) + const_w
        for j in cols_order:
            if j == pivot_col:
                offset += col_widths[j] - 2
                break
            offset += col_widths[j]
        dict_lines.append(" " * offset + "↓")
        
    # Dòng hàm mục tiêu z
    const_z = "" if tableau[-1][-1] == Fraction(0) else _fmt(tableau[-1][-1])
    if not const_z and all(tableau[-1][j] == Fraction(0) for j in cols_order): const_z = "0"
    z_line = f"{z_prefix}{const_z:>{const_w}}"
    
    for j in cols_order:
        val = tableau[-1][j]
        if val == Fraction(0):
            z_line += " " * col_widths[j]
        else:
            sign = " - " if val > Fraction(0) else " + "
            term = format_term(val, _var_name(j, n, n_slack))
            z_line += f"{sign}{term:>{col_widths[j]-3}}"
            
    dict_lines.append(z_line)
    
    line_len = const_w + sum(col_widths.values()) + 5
    dict_lines.append("  " + "─" * max(20, line_len))
    
    # Các dòng ràng buộc
    for i in range(len(tableau) - 1):
        bv_name = basic_names[i]
        prefix = "← " if i == pivot_row else "  "
        row_prefix = f"{prefix}{bv_name:<2} = "
        
        const_b = "" if tableau[i][-1] == Fraction(0) else _fmt(tableau[i][-1])
        if not const_b and all(tableau[i][j] == Fraction(0) for j in cols_order): const_b = "0"
        line = f"{row_prefix}{const_b:>{const_w}}"
        
        for j in cols_order:
            val = tableau[i][j]
            if val == Fraction(0):
                line += " " * col_widths[j]
            else:
                sign = " - " if val > Fraction(0) else " + "
                term = format_term(val, _var_name(j, n, n_slack))
                line += f"{sign}{term:>{col_widths[j]-3}}"
                
        dict_lines.append(line)
        
    coords = []
    point_coords = []
    for j in range(n):
        if j in basic_vars:
            row_idx = basic_vars.index(j)
            coords.append(_fmt(tableau[row_idx][-1]))
            point_coords.append(float(tableau[row_idx][-1]))
        else:
            coords.append("0")
            point_coords.append(0.0)
            
    pt_name = chr(ord('A') + step_idx - 1) if step_idx > 0 else 'O'
    if step_idx > 26: pt_name = f"P{step_idx}"
    point_str = f"{pt_name}({', '.join(coords)})"

    return {
        "basic_vars": basic_names,
        "rows": rows,
        "pivot_col": pivot_col,
        "pivot_row": pivot_row,
        "note": note,
        "dictionary_str": "\n".join(dict_lines),
        "point_str": point_str,
        "point_coords": point_coords
    }


def _pivot(tableau, row, col):
    """Phép xoay (pivot) tại (row, col) — in-place."""
    p = tableau[row][col]
    tableau[row] = [x / p for x in tableau[row]]
    for i in range(len(tableau)):
        if i != row:
            f = tableau[i][col]
            if f != Fraction(0):
                tableau[i] = [tableau[i][j] - f * tableau[row][j]
                              for j in range(len(tableau[i]))]


def _detect_multiple_optima(tableau, basic_vars, n_total):
    """Vô số nghiệm: biến không-cơ-sở có hệ số = 0 trong dòng z."""
    obj = tableau[-1]
    basic_set = set(basic_vars)
    for j in range(n_total):
        if j not in basic_set and abs(obj[j]) <= _EPS:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────

class SimplexSolver:
    """
    Giải QHT bằng phương pháp Đơn hình (3 biến thể):
      standard  — Đơn hình gốc (b_i >= 0, chỉ <=)
      bland     — Quy tắc Bland  (tránh lặp vòng)
      two-phase — Đơn hình 2 Pha (mọi loại ràng buộc)
    """

    def __init__(self, c, constraints, objective="max", bounds=None, method="standard"):
        self.n           = len(c)
        self.objective   = objective
        self.method      = method
        self.bounds      = bounds
        self.steps       = []
        self.status      = None
        self.optimal_value = None
        self.solution    = {}

        self.c_orig = [_frac(ci) for ci in c]
        # Nội bộ luôn MAXIMIZE: nếu min thì đảo dấu c
        if objective == "min":
            self.c_max = [-_frac(ci) for ci in c]
        else:
            self.c_max = [_frac(ci) for ci in c]

        self.constraints = constraints

    # ── Public ───────────────────────────────────────────────────────────────

    def solve(self):
        if self.method == "two-phase":
            return self._two_phase()
        return self._standard_bland(bland=(self.method == "bland"))

    # ─────────────────────────────────────────────────────────────────────────
    # A/B. Đơn hình gốc / Bland
    # Yêu cầu: tất cả ràng buộc dạng <=, b_i >= 0
    # TV xuất phát: w_i = b_i - sum(a_ij * x_j),  z = sum(c_j * x_j)
    # ─────────────────────────────────────────────────────────────────────────

    def get_next_step_idx(self):
        return len([s for s in self.steps if "rows" in s])

    def _standard_bland(self, bland=False):
        n = self.n
        cons = self.constraints
        m = len(cons)

        # Kiểm tra ràng buộc >= hoặc = → tự động chuyển sang Two-Phase (giống QHTT)
        for con in cons:
            if con["type"] in (">=", "="):
                self.steps.append({
                    "note": (
                        "⚠️ Bài toán chứa ràng buộc ≥ hoặc =. "
                        "Tự động chuyển sang Đơn hình 2 Pha (giống QHTT)."
                    )
                })
                return self._two_phase()

        # Xây TV xuất phát:
        # Biến: x_1..x_n (cột 0..n-1), w_1..w_m (cột n..n+m-1), RHS
        # Hàng i: [a_i, I_col_i, b_i]  →  w_i = b_i - a_i^T x
        # Dòng z: [-c, 0..0, 0]        →  z = c^T x (maximize nội bộ)

        n_slack = m
        n_total = n + n_slack
        tableau = []
        basic_vars = []

        for i, con in enumerate(cons):
            a = [_frac(x) for x in con["coeffs"]]
            b = _frac(con["rhs"])
            if b < Fraction(0):
                # b_i < 0 → tự động chuyển sang Two-Phase (giống QHTT gui_server.py dòng 456-459)
                self.steps.append({
                    "note": (
                        f"⚠️ Ràng buộc {i+1} có vế phải âm (b = {_fmt(b)}). "
                        "Tự động chuyển sang Đơn hình 2 Pha."
                    )
                })
                return self._two_phase()
            row = a + [Fraction(0)] * n_slack + [b]
            row[n + i] = Fraction(1)   # biến bù w_{i+1}
            tableau.append(row)
            basic_vars.append(n + i)

        obj = [-ci for ci in self.c_max] + [Fraction(0)] * n_slack + [Fraction(0)]
        tableau.append(obj)

        self.steps.append(_snap(
            tableau, basic_vars, n, n_slack,
            note="📋 Từ vựng (TV) xuất phát: w_i = b_i − Σa_ij·x_j, z = Σc_j·x_j.",
            step_idx=self.get_next_step_idx()
        ))

        status = self._simplex(tableau, basic_vars, n, n_slack, bland=bland)
        return self._finish(status, tableau, basic_vars, n, n_slack, n_total)

    # ─────────────────────────────────────────────────────────────────────────
    # C. Đơn hình 2 Pha
    # Pha 1: tìm nghiệm cơ sở ban đầu (dùng biến nhân tạo a_i)
    # Pha 2: tối ưu bài toán gốc
    # ─────────────────────────────────────────────────────────────────────────

    def _two_phase(self):
        n = self.n
        cons = self.constraints
        m = len(cons)

        # ── Bước 1: Chuẩn bị các ràng buộc với b >= 0 ──────
        std = []
        n_slack = 0
        n_art = 0
        
        for con in cons:
            a = [_frac(x) for x in con["coeffs"]]
            b = _frac(con["rhs"])
            t = con["type"]
            
            if b < Fraction(0):
                b = -b
                a = [-x for x in a]
                if t == "<=":
                    t = ">="
                elif t == ">=":
                    t = "<="
            
            if t == "<=":
                std.append({"a": a, "b": b, "slack_idx": n_slack, "slack_sign": 1, "art_idx": -1})
                n_slack += 1
            elif t == ">=":
                std.append({"a": a, "b": b, "slack_idx": n_slack, "slack_sign": -1, "art_idx": n_art})
                n_slack += 1
                n_art += 1
            elif t == "=":
                std.append({"a": a, "b": b, "slack_idx": -1, "slack_sign": 0, "art_idx": n_art})
                n_art += 1

        n_total_1 = n + n_slack + n_art
        art_cols = list(range(n + n_slack, n + n_slack + n_art))
        art_set = set(art_cols)

        # ── Bước 2: Xây tableau Pha 1 ────────────────────────────────────
        tableau_p1 = []
        basic_vars = []

        for item in std:
            row = item["a"] + [Fraction(0)] * n_slack + [Fraction(0)] * n_art + [item["b"]]
            if item["slack_idx"] != -1:
                row[n + item["slack_idx"]] = Fraction(item["slack_sign"])
            
            if item["art_idx"] != -1:
                col = n + n_slack + item["art_idx"]
                row[col] = Fraction(1)
                basic_vars.append(col)
            else:
                col = n + item["slack_idx"]
                basic_vars.append(col)
                
            tableau_p1.append(row)

        if n_art > 0:
            obj_p1 = [Fraction(0)] * n_total_1 + [Fraction(0)]
            for ac in art_cols:
                obj_p1[ac] = Fraction(1)
            tableau_p1.append(obj_p1)

            for i, bv in enumerate(basic_vars):
                if bv in art_set:
                    f = tableau_p1[-1][bv]
                    tableau_p1[-1] = [
                        tableau_p1[-1][j] - f * tableau_p1[i][j]
                        for j in range(len(tableau_p1[-1]))
                    ]

            self.steps.append({"phase": 1, "note": "═══ PHA 1: Tìm nghiệm cơ sở ban đầu (minimize Σ biến nhân tạo) ═══"})
            self.steps.append(_snap(
                tableau_p1, basic_vars, n, n_slack,
                note="📋 TV Pha 1 — mục tiêu: đưa tất cả biến nhân tạo ra khỏi cơ sở.",
                step_idx=self.get_next_step_idx(),
                obj_name="w"
            ))

            status1 = self._simplex(tableau_p1, basic_vars, n, n_slack=n_slack, bland=False, n_total_override=n_total_1, obj_name="w")
            
            phase1_val = tableau_p1[-1][-1]
            if phase1_val < -_EPS:
                self.status = "infeasible"
                return self._result("Vô nghiệm — Pha 1 kết thúc với min ξ > 0: tập phương án chấp nhận được là rỗng.")
                
            for i, bv in enumerate(basic_vars):
                if bv in art_set and tableau_p1[i][-1] > _EPS:
                    self.status = "infeasible"
                    return self._result("Vô nghiệm — biến nhân tạo không thể = 0.")

        else:
            self.steps.append({"phase": 1, "note": "═══ PHA 1: Bỏ qua (không cần biến nhân tạo) ═══"})

        # ── Bước 3: Pha 2 — loại cột artificial, khôi phục mục tiêu gốc ──
        self.steps.append({"phase": 2, "note": "═══ PHA 2: Tối ưu hoá bài toán gốc ═══"})

        keep = [j for j in range(n_total_1) if j not in art_set]
        n_total_2 = n + n_slack

        tableau_p2 = []
        if n_art > 0:
            for row in tableau_p1[:-1]:
                tableau_p2.append([row[j] for j in keep] + [row[-1]])
        else:
            tableau_p2 = tableau_p1

        new_basic = []
        for bv in basic_vars:
            if bv in art_set:
                new_basic.append(-1)
            else:
                shift = sum(1 for ac in art_cols if ac < bv)
                new_basic.append(bv - shift)

        rows_to_keep = []
        final_basic = []
        for i, bv in enumerate(new_basic):
            if bv == -1:
                row_i = tableau_p2[i]
                pivoted = False
                for j in range(n_total_2):
                    if abs(row_i[j]) > _EPS and j not in new_basic and j not in final_basic:
                        _pivot(tableau_p2, i, j)
                        pivoted = True
                        final_basic.append(j)
                        rows_to_keep.append(i)
                        break
                if not pivoted:
                    pass
            else:
                final_basic.append(bv)
                rows_to_keep.append(i)

        tableau_p2_clean = [tableau_p2[i] for i in rows_to_keep]

        obj_p2 = [-ci for ci in self.c_max] + [Fraction(0)] * n_slack + [Fraction(0)]
        tableau_p2_clean.append(obj_p2)

        for i, bv in enumerate(final_basic):
            if 0 <= bv < n_total_2:
                f = tableau_p2_clean[-1][bv]
                if f != Fraction(0):
                    tableau_p2_clean[-1] = [
                        tableau_p2_clean[-1][j] - f * tableau_p2_clean[i][j]
                        for j in range(len(tableau_p2_clean[-1]))
                    ]

        self.steps.append(_snap(
            tableau_p2_clean, final_basic, n, n_slack,
            note="📋 TV Pha 2 ban đầu — nghiệm cơ sở từ Pha 1, hàm mục tiêu gốc.",
            step_idx=self.get_next_step_idx()
        ))

        status2 = self._simplex(tableau_p2_clean, final_basic, n, n_slack=n_slack, bland=False, n_total_override=n_total_2, obj_name="z")
        return self._finish(status2, tableau_p2_clean, final_basic, n, n_slack, n_total_2)

    # ─────────────────────────────────────────────────────────────────────────
    # Lõi Simplex (dùng chung cho cả 3 phương pháp)
    # ─────────────────────────────────────────────────────────────────────────

    def _simplex(self, tableau, basic_vars, n_vars, n_slack, bland=False,
                 n_total_override=None, obj_name="z"):
        """
        Vòng lặp pivot đơn hình.
        Biến vào: hệ số âm nhất (Standard) / chỉ số nhỏ nhất (Bland) trong dòng z.
        Biến ra:  min-ratio b_i / a_ij  với a_ij > 0.
        """
        n_total = n_total_override if n_total_override is not None else n_vars + n_slack
        seen  = set()
        iters = 0

        while True:
            iters += 1
            if iters > MAX_ITER:
                return "cycling"

            obj = tableau[-1]

            # ── Chọn biến vào ──────────────────────────────────────────────
            if bland:
                pivot_col = next(
                    (j for j in range(n_total) if obj[j] < -_EPS), None
                )
            else:
                pivot_col = None
                min_val   = -_EPS
                for j in range(n_total):
                    if obj[j] < min_val:
                        min_val   = obj[j]
                        pivot_col = j

            if pivot_col is None:
                return "optimal"   # Điều kiện dừng: mọi h/số >= 0

            # Anti-cycling cho Standard
            if not bland:
                key = tuple(sorted(basic_vars))
                if key in seen:
                    return "cycling"
                seen.add(key)

            # ── Chọn biến ra — min-ratio test ─────────────────────────────
            # Xét dòng có a_ij > 0 (dương trong bảng TV):
            # tỉ số b_i / a_ij → chọn min để w_i không âm
            pivot_row = None
            min_ratio = None
            for i in range(len(tableau) - 1):
                aij = tableau[i][pivot_col]
                if aij > _EPS:
                    ratio = tableau[i][-1] / aij
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio
                        pivot_row = i
                    elif bland and abs(ratio - min_ratio) <= _EPS:
                        # Bland tie-break: biến cơ sở chỉ số nhỏ nhất
                        if basic_vars[i] < basic_vars[pivot_row]:
                            pivot_row = i

            if pivot_row is None:
                return "unbounded"   # Cột dương không tồn tại → vô giới nội

            entering = _var_name(pivot_col, n_vars, n_slack)
            leaving  = _var_name(basic_vars[pivot_row], n_vars, n_slack)
            rule     = "Bland — chỉ số nhỏ nhất" if bland else "hệ số âm nhất"
            note = (
                f"→ Biến vào: {entering} (cột {pivot_col}, {rule} trong dòng z). "
                f"Biến ra: {leaving} (dòng {pivot_row}, "
                f"min-ratio = {_fmt(min_ratio)})."
            )

            # Vẽ mũi tên trên bảng TV hiện tại (trước khi pivot)
            dict_with_arrows = _snap(
                tableau, basic_vars, n_vars, n_slack,
                pivot_col=pivot_col, pivot_row=pivot_row, obj_name=obj_name
            )
            if len(self.steps) > 0:
                self.steps[-1]["dictionary_str"] = dict_with_arrows["dictionary_str"]

            _pivot(tableau, pivot_row, pivot_col)
            basic_vars[pivot_row] = pivot_col

            self.steps.append(_snap(
                tableau, basic_vars, n_vars, n_slack,
                note=note,
                step_idx=self.get_next_step_idx(),
                obj_name=obj_name
            ))

        return "optimal"

    # ─────────────────────────────────────────────────────────────────────────
    # Trích nghiệm & xây response
    # ─────────────────────────────────────────────────────────────────────────

    def _finish(self, status, tableau, basic_vars, n_vars, n_slack, n_total):
        if status == "cycling":
            self.status = "cycling"
            return self._result(
                "Bài toán bị lặp vòng (Cycling Detected). "
                "Vui lòng chuyển sang Quy tắc Bland."
            )
        if status == "unbounded":
            self.status = "unbounded"
            return self._result(
                "Bài toán không giới nội (Unbounded) — "
                "hàm mục tiêu tiến tới ±∞ (có biến vào nhưng không có biến ra)."
            )

        self._extract(tableau, basic_vars, n_vars, n_slack, n_total)

        if _detect_multiple_optima(tableau, basic_vars, n_total):
            self.status = "multiple"
            return self._result(
                "Vô số nghiệm tối ưu — tồn tại biến không-cơ-sở "
                "có hệ số = 0 trong dòng z."
            )

        self.status = "optimal"
        return self._result(
            "Nghiệm tối ưu duy nhất — "
            "mọi hệ số biến không-cơ-sở trong dòng z đều > 0."
        )

    def _extract(self, tableau, basic_vars, n_vars, n_slack, n_total):
        """Đọc nghiệm từ TV tối ưu."""
        vals = [Fraction(0)] * n_total
        for i, bv in enumerate(basic_vars):
            if 0 <= bv < n_total:
                vals[bv] = tableau[i][-1]

        raw_z = tableau[-1][-1]   # giá trị maximize nội bộ
        # Nếu objective là min: ta đã maximize (-c), raw_z = -z_min
        if self.objective == "min":
            opt = -raw_z
        else:
            opt = raw_z
        self.optimal_value = _fmt(opt)

        for j in range(n_vars):
            self.solution[f"x{j+1}"] = _fmt(vals[j])
        for j in range(n_slack):
            if n_vars + j < n_total:
                self.solution[f"s{j+1}"] = _fmt(vals[n_vars + j])

    def _result(self, message):
        return {
            "status":        self.status,
            "message":       message,
            "optimal_value": self.optimal_value,
            "solution":      self.solution,
            "steps":         self.steps,
        }

    def get_standard_form(self):
        """
        Trả về biểu diễn bài toán ở dạng chuẩn theo lý thuyết:
        - Mục tiêu: luôn luôn min
        - Ràng buộc: luôn luôn <=
        - Biến: luôn luôn >= 0
        """
        bounds = self.bounds if self.bounds else [[0, None] for _ in range(self.n)]
        
        # 1. Đổi mục tiêu thành min
        if self.objective == "max":
            obj = "min"
            c_std = [-float(ci) for ci in self.c_orig]
        else:
            obj = "min"
            c_std = [float(ci) for ci in self.c_orig]
            
        # 2. Ràng buộc thành <=
        std_constraints = []
        for con in self.constraints:
            a = [float(x) for x in con["coeffs"]]
            b = float(con["rhs"])
            t = con["type"]
            
            if t == ">=":
                std_constraints.append({
                    "coeffs": [-x for x in a],
                    "type": "<=",
                    "rhs": -b
                })
            elif t == "<=":
                std_constraints.append({
                    "coeffs": list(a),
                    "type": "<=",
                    "rhs": b
                })
            elif t == "=":
                std_constraints.append({
                    "coeffs": list(a),
                    "type": "<=",
                    "rhs": b
                })
                std_constraints.append({
                    "coeffs": [-x for x in a],
                    "type": "<=",
                    "rhs": -b
                })

        # 3. Chuyển đổi biến
        final_c = []
        final_constraints = [{"coeffs": [], "type": "<=", "rhs": con["rhs"]} for con in std_constraints]
        var_names = []
        
        for j in range(self.n):
            bnd = bounds[j]
            is_nonneg = (bnd[0] is not None and bnd[0] >= 0)
            is_nonpos = (bnd[1] is not None and bnd[1] <= 0)
            
            if is_nonpos and not is_nonneg:
                # x_j <= 0 -> y_j = -x_j >= 0
                final_c.append(-c_std[j])
                for i, con in enumerate(std_constraints):
                    final_constraints[i]["coeffs"].append(-con["coeffs"][j])
                var_names.append(f"y{j+1} (=-x{j+1})")
            elif not is_nonneg and not is_nonpos:
                # tự do -> x_j' - x_j''
                final_c.append(c_std[j])
                final_c.append(-c_std[j])
                for i, con in enumerate(std_constraints):
                    final_constraints[i]["coeffs"].append(con["coeffs"][j])
                    final_constraints[i]["coeffs"].append(-con["coeffs"][j])
                var_names.append(f"x{j+1}'")
                var_names.append(f"x{j+1}''")
            else:
                # x_j >= 0
                final_c.append(c_std[j])
                for i, con in enumerate(std_constraints):
                    final_constraints[i]["coeffs"].append(con["coeffs"][j])
                var_names.append(f"x{j+1}")
                
        return {
            "objective": obj,
            "c": final_c,
            "constraints": final_constraints,
            "variables": var_names
        }
