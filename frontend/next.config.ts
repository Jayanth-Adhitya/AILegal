import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Enable standalone output for Docker deployment
  output: 'standalone',
  // Disable ESLint during production build (already checked in dev)
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Disable TypeScript errors during build (already checked in dev)
  typescript: {
    ignoreBuildErrors: false, // Keep TypeScript checks
  },
  // Allow connections to FastAPI backend
  // Use environment variable for backend URL, fallback to backend container name
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8080';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
