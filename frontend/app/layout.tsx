import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LP Solver — Giải Quy Hoạch Tuyến Tính",
  description: "Ứng dụng giải bài toán Quy hoạch tuyến tính với 3 phương pháp: Đơn hình cơ bản, Quy tắc Bland, và Đơn hình 2 pha. Hiển thị từng bước tính toán dạng phân số.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased" suppressHydrationWarning>{children}</body>
    </html>
  );
}
