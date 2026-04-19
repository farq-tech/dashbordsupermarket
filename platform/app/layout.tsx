import type { Metadata } from 'next'
import localFont from 'next/font/local'
import { Inter, Poppins } from 'next/font/google'
import './globals.css'

/** ITF Huwiya Arabic — primary UI Arabic/Latin stack (see `fonts/itfHuwiyaArabic/*.otf`). */
const huwiyaArabic = localFont({
  src: [
    { path: '../fonts/itfHuwiyaArabic/itfHuwiyaArabic-Light.otf', weight: '300', style: 'normal' },
    { path: '../fonts/itfHuwiyaArabic/itfHuwiyaArabic-Regular.otf', weight: '400', style: 'normal' },
    { path: '../fonts/itfHuwiyaArabic/itfHuwiyaArabic-Medium.otf', weight: '500', style: 'normal' },
    { path: '../fonts/itfHuwiyaArabic/itfHuwiyaArabic-Bold.otf', weight: '700', style: 'normal' },
    { path: '../fonts/itfHuwiyaArabic/itfHuwiyaArabic-Black.otf', weight: '900', style: 'normal' },
  ],
  variable: '--font-huwiya-arabic',
  display: 'swap',
})

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
    <html lang="ar" dir="rtl" className={`${huwiyaArabic.variable} ${inter.variable} ${poppins.variable}`}>
      <body>{children}</body>
    </html>
  )
}
