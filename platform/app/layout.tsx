import type { Metadata } from 'next'
import { Inter, Poppins } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

const poppins = Poppins({
  weight: ['400', '500', '600'],
  subsets: ['latin'],
  variable: '--font-poppins',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'منصة ذكاء الأعمال للتجزئة | Retail Business Intelligence',
  description:
    'منصة قرار لأداء التجزئة: رؤى السوق، المخاطر، والتوصيات. Decision platform for retail performance.',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover' as const,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl" className={`${inter.variable} ${poppins.variable}`}>
      <body>{children}</body>
    </html>
  )
}
