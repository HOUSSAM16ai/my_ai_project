/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          destination: process.env.API_URL
            ? `${process.env.API_URL}/api/:path*`
            : 'http://core-kernel:8000/api/:path*',
        },
        {
            source: '/health',
            destination: process.env.API_URL
            ? `${process.env.API_URL}/health`
            : 'http://core-kernel:8000/health',
        },
        {
            source: '/admin/api/:path*',
            destination: process.env.API_URL
            ? `${process.env.API_URL}/admin/api/:path*`
            : 'http://core-kernel:8000/admin/api/:path*',
        }
      ]
    },
};

module.exports = nextConfig;
