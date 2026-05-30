import sys
import socket
import threading
import time
import multiprocessing
import uvicorn
import webview

import traceback

# Biến toàn cục để lưu lỗi (nếu có)
backend_error = None

def start_backend():
    """
    Khởi động FastAPI server chạy ngầm ở cổng 8000.
    """
    global backend_error
    try:
        from gui_server import app as fastapi_app
        uvicorn.run(
            fastapi_app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="warning"
        )
    except Exception as e:
        backend_error = traceback.format_exc()
        print(f"Lỗi khởi động Backend: {backend_error}")

def wait_for_server(host="127.0.0.1", port=8000, timeout=60):
    """
    Poll cho đến khi server chấp nhận kết nối TCP.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.2)
    return False

def main():
    # QUAN TRỌNG: Bắt buộc với PyInstaller frozen exe
    multiprocessing.freeze_support()

    # 1. Khởi động API Server ngầm trong daemon thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # 2. Chờ server thực sự sẵn sàng
    server_ready = wait_for_server()

    if not server_ready:
        global backend_error
        error_msg = backend_error if backend_error else "Timeout khi chờ server khởi động."
        # Thay thế ký tự ngắt dòng thành thẻ <br> để hiển thị trên HTML
        error_msg_html = error_msg.replace('\n', '<br>')
        
        error_html = f"""<html><body style="background:#1a1a2e;color:#e74c3c;
            font-family:sans-serif;display:flex;align-items:center;
            justify-content:center;height:100vh;margin:0;flex-direction:column;padding:20px;">
            <h1>❌ Lỗi khởi động</h1>
            <p>Không thể kết nối đến máy chủ tính toán cục bộ.</p>
            <div style="background:#2d2d44; color:#fff; padding:15px; border-radius:8px; 
                        max-width:90%; max-height:50%; overflow:auto; text-align:left; font-size:12px;">
                <code>{error_msg_html}</code>
            </div>
        </body></html>"""
        window = webview.create_window(
            title="QHTT_KM197 - Lỗi",
            html=error_html,
            width=800, height=400,
        )
    else:
        # Chờ nhẹ một chút để đảm bảo HTTP router đã được map
        time.sleep(0.3)
        url = "http://127.0.0.1:8000"
        window = webview.create_window(
            title="QHTT_KM197",
            url=url,
            width=1280,
            height=800,
            min_size=(1024, 768),
            resizable=True,
            text_select=True,
        )

    # Khởi chạy cửa sổ ứng dụng (debug=False cho bản release)
    webview.start(debug=False)

if __name__ == "__main__":
    main()
