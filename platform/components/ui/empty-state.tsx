import { cn } from './cn'

interface EmptyStateProps {
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-[var(--radius-lg)] border border-dashed border-[var(--color-border)] bg-[var(--color-surface-muted)]/50 px-6 py-10 text-center',
        className,
      )}
    >
      <p className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
        {title}
      </p>
      {description && (
        <p className="mt-1 max-w-md text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
