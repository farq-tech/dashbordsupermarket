import { cn } from './cn'

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-[var(--color-border)]/80',
        className,
      )}
      {...props}
    />
  )
}

export function KpiCardSkeleton() {
  return (
    <div
      className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-[var(--density-card-padding)] shadow-[var(--shadow-tile)]"
    >
      <Skeleton className="mb-2 h-3 w-24" />
      <Skeleton className="h-8 w-20" />
      <Skeleton className="mt-2 h-3 w-full max-w-[180px]" />
    </div>
  )
}

export function ChartCardSkeleton({ height = 220 }: { height?: number }) {
  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-[var(--density-card-padding)] shadow-[var(--shadow-tile)]">
      <Skeleton className="mb-4 h-5 w-40" />
      <Skeleton className="w-full rounded-lg" style={{ height }} />
    </div>
  )
}
