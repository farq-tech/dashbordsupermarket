import { cn } from './cn'

interface CardRootProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  /** Lighter shadow for sections inside another card */
  elevation?: 'default' | 'nested'
}

type CardSectionProps = React.HTMLAttributes<HTMLDivElement> & { children: React.ReactNode }

export function Card({ className, children, elevation = 'default', ...props }: CardRootProps) {
  return (
    <div
      className={cn(
        'bg-[var(--color-surface)] rounded-[var(--radius-lg)] border p-[var(--density-card-padding)]',
        'border-[var(--color-border)]',
        elevation === 'nested' ? 'shadow-[var(--shadow-tile-nested)]' : 'shadow-[var(--shadow-tile)]',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ className, children, ...props }: CardSectionProps) {
  return (
    <div className={cn('mb-[var(--density-card-header-mb)]', className)} {...props}>
      {children}
    </div>
  )
}

export function CardTitle({ className, children, ...props }: CardSectionProps) {
  return (
    <h3
      className={cn('text-base font-semibold', className)}
      style={{ color: 'var(--color-text-primary)' }}
      {...props}
    >
      {children}
    </h3>
  )
}

export function CardContent({ className, children, ...props }: CardSectionProps) {
  return (
    <div className={cn('', className)} {...props}>
      {children}
    </div>
  )
}
