import { cn } from './cn'

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'h-8 w-8 border-2 border-neutral-200 rounded-full animate-spin border-t-[color:var(--color-interactive)]',
        className,
      )}
    />
  )
}

export function LoadingOverlay({
  text_ar = 'جارٍ التحميل...',
  text_en = 'Loading...',
  lang = 'ar',
}: {
  text_ar?: string
  text_en?: string
  lang?: 'ar' | 'en'
}) {
  const text = lang === 'ar' ? text_ar : text_en
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4" aria-busy="true" aria-label={text}>
      <Spinner className="h-10 w-10" />
      <p className="text-neutral-400 text-sm">{text}</p>
    </div>
  )
}
