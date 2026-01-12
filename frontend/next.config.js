/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          // In Docker, 'core-kernel' will be the service name for the backend on port 8000
          // But wait, the user wants 'automation' and we are going to add 'core-kernel' to docker-compose.
          // However, for local dev (npm run dev), we want localhost:8000.
          // We can use an env var API_URL
          destination: process.env.API_URL
            ? `${process.env.API_URL}/:path*`
            : 'http://core-kernel:8000/:path*',
        },
        {
            source: '/health',
            destination: process.env.API_URL
            ? `${process.env.API_URL}/health`
            : 'http://core-kernel:8000/health',
        },
        // The admin api routes seem to start with /admin/api based on the legacy code
        {
            source: '/admin/api/:path*',
            destination: process.env.API_URL
            ? `${process.env.API_URL}/admin/api/:path*`
            : 'http://core-kernel:8000/admin/api/:path*',
        }
      ]
    },
    // We need to allow the legacy CSS if possible, but importing it in layout is better.
    // The legacy app loaded CSS from /public/css. This works fine in Next.js public folder.
};

module.exports = nextConfig;
