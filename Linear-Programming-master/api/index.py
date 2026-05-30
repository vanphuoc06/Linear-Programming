# index.py — Entry point cho Vercel Python Serverless Function.
# Vercel yêu cầu file này (hoặc tên trùng với thư mục) để nhận HTTP request.
# Tất cả logic thực sự nằm trong main.py.
from main import handler  # noqa: F401
