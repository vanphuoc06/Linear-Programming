# Hướng Dẫn Chạy Dự Án Linear Programming

Dự án này bao gồm hai phần chính: 
- **Backend (API)**: Xây dựng bằng FastAPI (Python).
- **Frontend**: Xây dựng bằng Next.js (Node.js).

Để chạy toàn bộ dự án, bạn cần mở hai terminal (cửa sổ dòng lệnh) riêng biệt, một cho Backend và một cho Frontend.

---

## Yêu cầu hệ thống
- [Python 3.8+](https://www.python.org/downloads/) đã được cài đặt.
- [Node.js (phiên bản 18+ khuyến nghị)](https://nodejs.org/) đã được cài đặt.

---

## Bước 1: Chạy Backend (FastAPI)

Mở **Terminal 1** và thực hiện các lệnh sau:

1. Đi tới thư mục gốc của dự án:
   ```bash
   cd "c:\Users\ADMIN\Downloads\Linear Programming"
   ```

2. (Tùy chọn nhưng khuyến nghị) Tạo môi trường ảo và kích hoạt nó:
   - Trên Windows:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

3. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```

4. Khởi chạy server Backend:
   ```bash
   uvicorn api.main:app --reload
   ```
   *Lúc này, Backend sẽ chạy tại: `http://localhost:8000`*
   *Bạn có thể truy cập `http://localhost:8000/docs` để xem giao diện Swagger UI của API.*

---

## Bước 2: Chạy Frontend (Next.js)

Mở **Terminal 2** và thực hiện các lệnh sau:

1. Đi tới thư mục `frontend` của dự án:
   ```bash
   cd "c:\Users\ADMIN\Downloads\Linear Programming\frontend"
   ```

2. Cài đặt các thư viện (chỉ cần chạy lần đầu hoặc khi có cập nhật):
   ```bash
   npm install
   ```

3. Khởi chạy server Frontend:
   ```bash
   npm run dev
   ```
   *Lúc này, Frontend sẽ chạy tại: `http://localhost:3000`*

---

## Bước 3: Sử dụng Ứng dụng
Mở trình duyệt web của bạn và truy cập vào địa chỉ: **[http://localhost:3000](http://localhost:3000)** để sử dụng ứng dụng Linear Programming.

---
**Lưu ý:**
- Cả hai server cần được chạy song song để Frontend có thể giao tiếp được với Backend.
- Nếu bạn gặp lỗi CORS hoặc không thể kết nối tới API, hãy chắc chắn rằng Backend đang thực sự chạy ở cổng `8000`.
