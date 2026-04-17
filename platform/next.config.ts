import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'devapi.fustog.app' },
      { protocol: 'https', hostname: 'api.fustog.app' },
    ],
  },
}

export default nextConfig
