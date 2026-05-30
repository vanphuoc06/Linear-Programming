/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Chỉ proxy /api/* → localhost:8000 khi chạy local development.
    // Khi deploy lên Vercel, /api/* tự động được Vercel route tới
    // Python Serverless Function (api/main.py) nên KHÔNG cần rewrite.
    if (process.env.NODE_ENV === "development") {
      return [
        {
          source: "/api/:path*",
          destination: "http://localhost:8000/api/:path*",
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
