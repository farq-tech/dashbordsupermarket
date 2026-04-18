'use client'

import { useEffect, useRef, useState } from 'react'
import { usePrefersReducedMotion } from '@/lib/usePrefersReducedMotion'

interface CountUpProps {
  end: number
  durationMs?: number
  decimals?: number
  className?: string
  style?: React.CSSProperties
}

export function CountUp({ end, durationMs = 900, decimals = 0, className, style }: CountUpProps) {
  const reduceMotion = usePrefersReducedMotion()
  const [val, setVal] = useState(reduceMotion ? end : 0)
  const startRef = useRef<number | null>(null)
  const frameRef = useRef<number>(0)

  useEffect(() => {
    if (reduceMotion) {
      setVal(end)
      return
    }
    startRef.current = null
    const tick = (now: number) => {
      if (startRef.current === null) startRef.current = now
      const t = Math.min(1, (now - startRef.current) / durationMs)
      const eased = 1 - (1 - t) ** 3
      setVal(end * eased)
      if (t < 1) frameRef.current = requestAnimationFrame(tick)
    }
    frameRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frameRef.current)
  }, [end, durationMs, reduceMotion])

  const formatted = decimals > 0 ? val.toFixed(decimals) : Math.round(val).toString()

  return (
    <span className={className} style={style}>
      {formatted}
    </span>
  )
}
