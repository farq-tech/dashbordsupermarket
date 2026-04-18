import { cn } from './cn'

export function Spinner({ className }: { className?: string }) {
  return (
    <div className={cn('h-8 w-8 border-3 border-neutral-200 border-t-[#1a5c3a] rounded-full animate-spin', className)} />
  )
}

export function LoadingOverlay({ text_ar = 'جارٍ التحميل...', text_en = 'Loading...' }: { text_ar?: string; text_en?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4" aria-busy="true" aria-label={text_en}>
      <Spinner className="h-10 w-10" />
      <p className="text-neutral-400 text-sm">{text_ar}</p>
    </div>
  )
}
