import { Slot } from '@radix-ui/react-slot'
import { cn } from './cn'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  children: React.ReactNode
  /** When true, renders the child element directly via Radix Slot (e.g. for <Link> wrappers). */
  asChild?: boolean
}

const variants: Record<ButtonVariant, string> = {
  primary:
    'bg-[var(--color-interactive)] text-white hover:bg-[var(--color-interactive-hover)] shadow-[var(--shadow-tile)]',
  secondary: 'bg-[var(--color-surface-muted)] text-[var(--color-text-primary)] hover:bg-[var(--color-surface-hover)]',
  ghost: 'text-[var(--color-text-primary)] hover:bg-[var(--color-surface-muted)]',
  danger: 'bg-[var(--color-destructive,#dc2626)] text-white hover:opacity-90',
  outline: 'border border-[var(--color-border)] text-[var(--color-text-primary)] hover:bg-[var(--color-surface-muted)]',
}

const sizes: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs rounded-lg',
  md: 'px-4 py-2 text-sm rounded-lg',
  lg: 'px-6 py-3 text-base rounded-xl',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  asChild = false,
  className,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : 'button'
  return (
    <Comp
      className={cn(
        'inline-flex items-center gap-2 font-medium transition-colors cursor-pointer',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className,
      )}
      disabled={disabled || loading}
      {...(props as React.HTMLAttributes<HTMLElement>)}
    >
      {loading && (
        <span className="h-3.5 w-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      )}
      {children}
    </Comp>
  )
}
