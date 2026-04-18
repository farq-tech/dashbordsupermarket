'use client'

import Image from 'next/image'
import type { Retailer } from '@/lib/types'
import { cn } from '@/components/ui/cn'

type Props = {
  retailer: Retailer
  /** Accessible label (e.g. brand name) */
  label?: string
  size?: number
  className?: string
  rounded?: 'md' | 'lg' | 'xl' | '2xl'
}

const roundedClass = {
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  '2xl': 'rounded-2xl',
} as const

export function RetailerLogo({ retailer, label, size = 24, className, rounded = 'md' }: Props) {
  const url = retailer.logo_url
  const alt = label ? `${label} logo` : ''
  if (url) {
    return (
      <span
        className={cn(
          'relative inline-flex shrink-0 overflow-hidden bg-white ring-1 ring-black/[0.06]',
          roundedClass[rounded],
          className,
        )}
        style={{ width: size, height: size }}
      >
        <Image
          src={url}
          alt={alt}
          title={label}
          width={size}
          height={size}
          className="object-contain p-[2px]"
          sizes={`${size}px`}
        />
      </span>
    )
  }
  return (
    <span
      className={cn(
        'inline-flex shrink-0 items-center justify-center font-bold text-white',
        roundedClass[rounded],
        className,
      )}
      style={{
        width: size,
        height: size,
        backgroundColor: retailer.color,
        fontSize: Math.max(10, Math.round(size * 0.38)),
      }}
    >
      {retailer.logo_letter}
    </span>
  )
}
