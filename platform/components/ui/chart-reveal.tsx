'use client'

import { cn } from './cn'
import { usePrefersReducedMotion } from '@/lib/usePrefersReducedMotion'

export function ChartReveal({
  children,
  className,
  active = true,
}: {
  children: React.ReactNode
  className?: string
  /** When false, skip enter animation (e.g. no data yet) */
  active?: boolean
}) {
  const reduceMotion = usePrefersReducedMotion()
  if (!active || reduceMotion) return <div className={className}>{children}</div>
  return <div className={cn('chart-reveal', className)}>{children}</div>
}
