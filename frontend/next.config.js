/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
      // NOTE: These rewrites are only for HTTP traffic.
      // Do NOT rely on Next.js rewrites for WebSockets (ws/wss) as they do not support Upgrade headers correctly.
      // Use NEXT_PUBLIC_WS_URL to connect directly to the WebSocket backend or a dedicated Reverse Proxy (Nginx/Caddy).
      return [
        {
          source: '/api/:path*',
          destination: process.env.API_URL
            ? `${process.env.API_URL}/api/:path*`
            : 'http://127.0.0.1:8000/api/:path*',
        },
        {
            source: '/health',
            destination: process.env.API_URL
            ? `${process.env.API_URL}/health`
            : 'http://127.0.0.1:8000/health',
        },
        {
            source: '/admin/api/:path*',
            destination: process.env.API_URL
            ? `${process.env.API_URL}/admin/api/:path*`
            : 'http://127.0.0.1:8000/admin/api/:path*',
        }
      ]
    },
};

module.exports = nextConfig;
