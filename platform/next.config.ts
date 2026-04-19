import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { NextConfig } from 'next'

/** App lives in /platform; parent repo has its own package.json — lockfile discovery otherwise resolves from the wrong tree (breaks `next dev` + Playwright). */
const platformRoot = path.dirname(fileURLToPath(import.meta.url))

const nextConfig: NextConfig = {
  turbopack: {
    root: platformRoot,
    resolveAlias: {
      tailwindcss: path.join(platformRoot, 'node_modules', 'tailwindcss'),
    },
  },
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
