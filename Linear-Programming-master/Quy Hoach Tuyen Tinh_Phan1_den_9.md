# Bài Giảng Quy Hoạch Tuyến Tính (Phần 1 - 9)

**THÔNG TIN MÔN HỌC**
- **Email:** thanh@hcmus.edu.vn
- **Tài liệu:** Quy Hoạch Tuyến Tính (6 chương) - Tác giả: Q. Khánh, T. H. Vương
- **Bảng điểm:**
  - Giữa kỳ (GK): 20% (60' - 90')
  - Bài tập (BT): 10%
  - Bài tập code: 10%
  - Điểm thưởng (Bonus): 10% (3 lần)
  - Kiểm tra đột xuất (KTDX): 10%
  - Cuối kỳ (CK): 60% (90' - 120')
- **Nội dung môn học:** 
  Bài toán thực tế $\rightarrow$ Mô hình toán học $\rightarrow$ Thuật giải $\rightarrow$ Đưa kết quả $\rightarrow$ Giải quyết cho bài toán thực tế.

---

## 1. Định nghĩa bài toán Quy hoạch tuyến tính (Linear Programming)

Hàm mục tiêu:
$$ \min/\max f(x) = c^T x = c_1 x_1 + c_2 x_2 + ... + c_n x_n $$

Ràng buộc (Hệ phương trình/bất phương trình):
$$ Ax \le b \quad \text{(hoặc } \ge, = \text{)} $$
(Với $A = [a_{ij}]_{m \times n}$ là ma trận hệ số ràng buộc)

Ràng buộc dấu:
- $x_j \ge 0, \quad j \in N_1$
- $x_j \le 0, \quad j \in N_2$
- $x_j$ tự do, $\quad j \in N_3$
*(Tổng số biến: $|N_1| + |N_2| + |N_3| = n$)*

---

## 2. Chuyển bài toán thực tế thành mô hình QHTT

Các bước thiết lập mô hình:
1. Đặt biến chính (đại diện cho các quyết định cần tìm).
2. Đặt các biến phụ (nếu có, tính dựa vào biến chính).
3. Xác định các tham số.
4. Xây dựng hàm mục tiêu (cần tối ưu).
5. Xây dựng các ràng buộc.

### Ví dụ 1: Bài toán Vitamin
**Đề bài:** Một người mỗi ngày cần tiếp nhận không quá 600 đơn vị vitamin A và không quá 500 đơn vị vitamin B. Mỗi ngày cần từ 400 đến 1000 đơn vị cả A và B. Lượng vitamin B không ít hơn $1/2$ lượng vitamin A nhưng không nhiều hơn 3 lần vitamin A. Giá 1 đv vitamin A là 9 tiền, 1 đv vitamin B là 7.5 tiền. Cần chi ít nhất bao nhiêu tiền để dùng đủ 2 loại vitamin trên?

**Mô hình:**
- Gọi $x$ là số đv vitamin A ($x \ge 0$)
- Gọi $y$ là số đv vitamin B ($y \ge 0$)

Hệ ràng buộc:
- $x \le 600$
- $y \le 500$
- $400 \le x + y \le 1000$
- $y \ge 0.5x$
- $y \le 3x$

Hàm mục tiêu:
$$ \min z = 9x + 7.5y $$

### Ví dụ 2: Bài toán thuê xe chở người và hàng
**Mô hình:**
- Gọi $x_A$ là số xe loại A cần thuê ($x_A \ge 0, x_A \in \mathbb{Z}$)
- Gọi $x_B$ là số xe loại B cần thuê ($x_B \ge 0, x_B \in \mathbb{Z}$)

Hệ ràng buộc:
- Xe A có 10 chiếc $\Rightarrow x_A \le 10$
- Xe B có 9 chiếc $\Rightarrow x_B \le 9$
- Yêu cầu chở 140 người (xe A chở 20 người, xe B chở 10 người) $\Rightarrow 20x_A + 10x_B \ge 140 \Rightarrow 2x_A + x_B \ge 14$
- Yêu cầu chở 9 tấn hàng (xe A chở 0.6 tấn, xe B chở 0.5 tấn) $\Rightarrow 0.6x_A + 0.5x_B \ge 9 \Rightarrow 6x_A + 5x_B \ge 90$

Hàm mục tiêu (Giả sử xe A giá 4 triệu, xe B giá 3 triệu):
$$ \min z = 4x_A + 3x_B $$

---

## 3. Phân loại bài toán QHTT

Có hai dạng cơ bản của bài toán QHTT:

**1. Dạng chính tắc:**
- Mục tiêu: $\min$ hoặc $\max \ c^T x$
- Ràng buộc: $Ax = b$
- Dấu: $x \ge 0$

**2. Dạng chuẩn:**
- Mục tiêu: $\min$ hoặc $\max \ c^T x$
- Ràng buộc: $Ax \ge b$ (nếu min) hoặc $Ax \le b$ (nếu max)
- Dấu: $x \ge 0$

---

## 4. Chuyển đổi bài toán QHTT tổng quát

Các quy tắc chuyển đổi về Dạng chuẩn / Dạng chính tắc:
- $\max c^T x \Rightarrow -\min(-c^T x)$
- Bất phương trình $\ge$ thành $\le$: $a_i x \ge b_i \Rightarrow -a_i x \le -b_i$
- Đưa về phương trình (thêm biến phụ $s_i \ge 0$):
  - $a_i x \le b_i \Rightarrow a_i x + s_i = b_i$
  - $a_i x \ge b_i \Rightarrow a_i x - s_i = b_i$
- Đổi biến âm thành biến dương: $x_j \le 0 \Rightarrow y_j = -x_j \ge 0$
- Đổi biến tự do: $x_j$ tự do $\Rightarrow x_j = x_j' - x_j''$ (với $x_j' \ge 0, x_j'' \ge 0$)

---

## 5. Phân loại tập nghiệm

Một bài toán QHTT có thể rơi vào các trường hợp nghiệm sau:
1. **Duy nhất nghiệm:** Có 1 nghiệm tối ưu duy nhất $x^*$ và giá trị tối ưu $z^*$.
2. **Vô số nghiệm:** Bài toán có nhiều phương án cùng đạt giá trị tối ưu $z^*$.
3. **Vô nghiệm (Không có phương án):** Tập ràng buộc rỗng, bài toán không thể thỏa mãn tất cả các ràng buộc. Quy ước $\min z = +\infty, \max z = -\infty$.
4. **Không giới nội (Không bị chặn):** Bài toán có nghiệm hợp lệ nhưng giá trị hàm mục tiêu có thể tiến tới vô cực ($\min \rightarrow -\infty$ hoặc $\max \rightarrow +\infty$).

---

## 6. Giải bài toán QHTT 2 biến bằng phương pháp hình học

Đối với QHTT 2 biến, có thể biểu diễn trên hệ trục tọa độ 2D.
**Ví dụ:**
$$ \max z = 3x_1 + 2x_2 $$
Ràng buộc:
- $x_1 + 2x_2 \le 6$
- $x_1 - x_2 \le 1$
- $x_1, x_2 \ge 0$

**Cách giải:**
1. Vẽ miền nghiệm (đa giác tạo bởi các đường thẳng $x_1 + 2x_2 = 6, x_1 - x_2 = 1, x_1=0, x_2=0$).
2. Tìm tọa độ các đỉnh của đa giác miền nghiệm.
3. Thay tọa độ các đỉnh vào hàm mục tiêu $z$ để tìm GTLN (hoặc có thể dùng phương pháp đường mức, trượt đường thẳng $3x_1 + 2x_2 = c$).

---

## 7. Phương pháp Đơn hình (Simplex Method)

Dùng để giải các bài toán QHTT tổng quát. 
**Các bước cơ bản:**
1. **Xây dựng từ vựng xuất phát:** Biểu diễn các biến cơ sở (variables cơ bản) theo các biến phi cơ sở (non-basic variables). Đặt các biến phi cơ sở bằng 0 để lấy giá trị biến cơ sở.
2. **Chọn biến vào:** Chọn biến phi cơ sở làm tăng (hoặc giảm) hàm mục tiêu tốt nhất (dựa trên hệ số trong hàm mục tiêu).
3. **Chọn biến ra:** Trong các phương trình, giới hạn biến vào bằng cách chọn biến cơ sở có tỷ số $\frac{b_i}{a_{ij}}$ nhỏ nhất (với $a_{ij} > 0$).
4. **Xoay (Pivot):** Đưa biến vào thành biến cơ sở, biến ra thành biến phi cơ sở. Giải hệ phương trình lại.
5. **Dừng:** Nếu mọi hệ số của biến phi cơ sở trong hàm mục tiêu không thể tối ưu thêm (ví dụ tất cả đều $\le 0$ trong bài toán max), thì đó là từ vựng tối ưu.

---

## 8. Dạng bảng của phương pháp đơn hình

Thay vì dùng từ vựng phương trình, biểu diễn thuật toán Đơn hình qua cấu trúc bảng (Tableau). Cập nhật bảng sau mỗi lần xoay (Pivot) bằng các phép biến đổi hàng sơ cấp (nhân chia hàng, cộng trừ hàng) để tiết kiệm thời gian viết lại biến.

---

## 9. Phương pháp Bland (Chống xoay vòng)

Khi gặp hiện tượng **thoái hóa** (có biến cơ sở bằng 0, hay $b_i = 0$), thuật toán đơn hình có thể lặp lại trạng thái cũ mãi mãi (gọi là xoay vòng - cycling).
**Quy tắc Bland (Bland's Rule):**
1. **Biến vào:** Trong số các ứng viên hợp lệ, chọn biến có chỉ số nhỏ nhất.
2. **Biến ra:** Nếu có nhiều ứng viên (tỷ số min bằng nhau), chọn biến có chỉ số nhỏ nhất rời cơ sở.
Áp dụng quy tắc này đảm bảo thuật toán sẽ không bị xoay vòng và kết thúc sau hữu hạn bước.

---

## 10. Thuật toán 2 Pha (Two-Phase Simplex)

Áp dụng khi bài toán Dạng chuẩn không có sẵn hệ biến cơ sở xuất phát khả thi (ví dụ $b_i < 0$ hoặc ràng buộc $\ge$, $=$).
- **Pha 1 (Xây dựng từ vựng xuất phát khả thi):**
  - Thêm các biến giả (artificial variables) $w \ge 0$ vào hệ phương trình.
  - Lập bài toán bổ trợ với hàm mục tiêu: $\min z' = \sum w_i$.
  - Giải bằng Đơn hình. 
  - Nếu kết thúc $\min z' > 0$ $\Rightarrow$ Bài toán gốc vô nghiệm.
  - Nếu kết thúc $\min z' = 0$ $\Rightarrow$ Chuyển sang Pha 2.
- **Pha 2 (Giải bài toán gốc):**
  - Bỏ đi các biến giả, lấy từ vựng tối ưu của Pha 1 làm xuất phát.
  - Phục hồi lại hàm mục tiêu $z$ ban đầu và tiếp tục chạy thuật toán Đơn hình để tìm nghiệm tối ưu cuối cùng.

---
*(Ghi chú: Các phần tiếp theo như Xây dựng bài toán đối ngẫu (Phần 10 trở đi) đã được bỏ qua theo yêu cầu).*
