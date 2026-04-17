import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: {
    turbo: {
      resolveExtensions: ['.tsx', '.ts', '.jsx', '.js'],
    },
  },
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'devapi.fustog.app' },
      { protocol: 'https', hostname: 'api.fustog.app' },
    ],
  },
}

export default nextConfig
