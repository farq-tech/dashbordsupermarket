import { cn } from './cn'

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  size?: 'sm' | 'md'
}

const variants: Record<BadgeVariant, string> = {
  default: 'bg-[var(--color-brand)]/10 text-[var(--color-brand)]',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-amber-100 text-amber-700',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
  neutral: 'bg-gray-100 text-gray-600',
}

export function Badge({ variant = 'default', size = 'sm', className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  )
}

export function TagBadge({ tag, lang = 'ar' }: { tag: string; lang?: 'ar' | 'en' }) {
  const map: Record<string, { label_ar: string; label_en: string; cls: string }> = {
    overpriced: { label_ar: 'سعر أعلى من السوق', label_en: 'Overpriced', cls: 'tag-overpriced' },
    underpriced: { label_ar: 'سعر أقل من السوق', label_en: 'Underpriced', cls: 'tag-underpriced' },
    competitive: { label_ar: 'سعر تنافسي', label_en: 'Competitive', cls: 'tag-competitive' },
    opportunity: { label_ar: 'فرصة تحسين', label_en: 'Opportunity', cls: 'tag-opportunity' },
    risk: { label_ar: 'مخاطر محتملة', label_en: 'Risk', cls: 'tag-risk' },
    not_stocked: { label_ar: 'غير متوفر', label_en: 'Not Available', cls: 'tag-not_stocked' },
  }
  const info = map[tag] ?? map.not_stocked
  const label = lang === 'ar' ? info.label_ar : info.label_en
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${info.cls}`}>
      {label}
    </span>
  )
}
