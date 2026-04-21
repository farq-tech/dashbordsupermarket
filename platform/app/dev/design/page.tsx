import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { DevDesignGallery } from './DevDesignGallery'

export const metadata: Metadata = {
  title: 'Fareeq design reference',
  description: 'Internal design review: tokens, typography, Fareeq v10 assets.',
  robots: { index: false, follow: false },
}

function isDesignGalleryAllowed(): boolean {
  if (process.env.NODE_ENV === 'development') return true
  return process.env.NEXT_PUBLIC_SHOW_DESIGN_GALLERY === '1'
}

export default function DevDesignPage() {
  if (!isDesignGalleryAllowed()) {
    notFound()
  }
  return <DevDesignGallery />
}
