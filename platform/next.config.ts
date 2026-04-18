import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Playwright / automated UI tests use 127.0.0.1; dev HMR otherwise logs cross-origin warnings.
  allowedDevOrigins: ['127.0.0.1'],
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'devapi.fustog.app' },
      { protocol: 'https', hostname: 'api.fustog.app' },
    ],
  },
}

export default nextConfig
