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
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
