'use client'

import { useMemo, useState } from 'react'
import { type FareeqV10Key, fareeqV10Assets } from '@/lib/design-system/fareeqV10'

export function DevDesignGallery() {
  const keys = useMemo(() => Object.keys(fareeqV10Assets) as FareeqV10Key[], [])
  const [broken, setBroken] = useState<Partial<Record<FareeqV10Key, true>>>({})

  return (
    <div className="min-h-screen bg-background px-4 py-8 text-foreground sm:px-8">
      <div className="mx-auto max-w-6xl space-y-14">
        <header className="border-b border-border pb-8">
          <h1 className="text-ds-2xl font-bold text-ink">Design review — Farq</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Tokens, typography (Inter + ITF Huwiya Arabic), and Fareeq v10 SVG reference. Dev server: open{' '}
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">/dev/design</code> . Aligns with the
            consumer app gallery.
          </p>
        </header>

        <section>
          <h2 className="mb-4 text-ds-lg font-semibold text-ink">Brand &amp; accent</h2>
          <div className="flex flex-wrap gap-3">
            {(
              [
                ['brand-900', 'bg-brand-900'],
                ['brand-700', 'bg-brand-700'],
                ['mint-500', 'bg-mint-500'],
                ['mint-600', 'bg-mint-600'],
                ['coral-500', 'bg-coral-500'],
                ['amber-500', 'bg-amber-500'],
              ] as const
            ).map(([label, cls]) => (
              <div
                key={label}
                className={`flex h-14 min-w-[7rem] items-center justify-center rounded-ds-md px-3 text-xs font-medium text-white shadow-soft ${cls}`}
              >
                {label}
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-ds-lg font-semibold text-ink">Semantic / UI (shadcn bridge)</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-ds-lg border border-border bg-card p-4 text-card-foreground shadow-soft">
              <p className="text-xs font-medium text-muted-foreground">card</p>
              <p className="mt-1 text-sm">Card surface</p>
            </div>
            <div className="rounded-ds-lg border border-border bg-muted p-4 text-muted-foreground">
              <p className="text-xs font-medium">muted</p>
              <p className="mt-1 text-sm text-foreground">Muted block</p>
            </div>
            <div className="rounded-ds-lg bg-primary p-4 text-primary-foreground">
              <p className="text-xs font-medium opacity-90">primary</p>
              <p className="mt-1 text-sm">CTA semantic</p>
            </div>
            <div className="rounded-ds-lg border border-destructive/40 bg-destructive/10 p-4 text-destructive">
              <p className="text-xs font-medium">destructive</p>
              <p className="mt-1 text-sm">Alert tone</p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-ds-lg font-semibold text-ink">Typography (Latin)</h2>
          <div className="space-y-2 rounded-ds-lg border border-line bg-surface p-6">
            <p className="text-ds-2xl font-bold">Display ds-2xl bold</p>
            <p className="text-ds-xl font-semibold">Title ds-xl semibold</p>
            <p className="text-ds-lg font-medium">Heading ds-lg medium</p>
            <p className="text-ds-md text-ink/90">Body ds-md — The quick brown fox jumps over the lazy dog.</p>
            <p className="text-ds-sm text-ink-muted">Caption ds-sm muted</p>
            <p className="text-ds-xs text-ink-muted">Label ds-xs</p>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-ds-lg font-semibold text-ink">Typography (Arabic — ITF Huwiya)</h2>
          <div className="space-y-3 rounded-ds-lg border border-line bg-surface p-6 font-arabic" dir="rtl">
            <p className="text-ds-2xl font-black">فرق — وفر فلوسك</p>
            <p className="text-ds-lg font-bold">قارن أسعار التوصيل والمقاضي في السعودية</p>
            <p className="text-ds-md font-medium">اختر أرخص خيار بسرعة من بين التطبيقات.</p>
            <p className="text-ds-sm font-normal text-ink-muted">نص ثانوي أصغر للواجهات العربية.</p>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-ds-lg font-semibold text-ink">Spacing &amp; radius</h2>
          <div className="flex flex-wrap items-end gap-6">
            {(
              [
                ['p-ds-xs', 'ds-xs'],
                ['p-ds-sm', 'ds-sm'],
                ['p-ds-md', 'ds-md'],
                ['p-ds-lg', 'ds-lg'],
                ['p-ds-xl', 'ds-xl'],
              ] as const
            ).map(([pad, label]) => (
              <div key={label} className="flex flex-col items-center gap-2">
                <div className={`inline-block rounded-ds-sm bg-brand-900 ${pad}`}>
                  <div className="h-6 w-6 bg-mint-200/90" />
                </div>
                <span className="font-mono text-[10px] text-ink-muted">{label}</span>
              </div>
            ))}
          </div>
          <div className="mt-6 flex flex-wrap gap-4">
            {(['rounded-ds-sm', 'rounded-ds-md', 'rounded-ds-lg', 'rounded-ds-xl'] as const).map((r) => (
              <div
                key={r}
                className={`flex h-16 w-24 items-center justify-center border border-line bg-mint-100/50 text-[10px] font-medium text-ink ${r}`}
              >
                {r.replace('rounded-', '')}
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-ds-lg font-semibold text-ink">Glass</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="glass-light rounded-ds-xl px-6 py-8 text-sm text-ink shadow-card">
              <code className="text-xs">.glass-light</code>
              <p className="mt-2">Frosted panel on light canvas.</p>
            </div>
            <div className="rounded-ds-xl bg-neutral-900 p-4 shadow-card">
              <div className="glass-dark rounded-ds-lg px-6 py-8 text-sm text-white">
                <code className="text-xs text-white/80">.glass-dark</code>
                <p className="mt-2 text-white/95">On dark surfaces / imagery.</p>
              </div>
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-ds-lg font-semibold text-ink">Fareeq v10 — reference SVGs</h2>
          <p className="mb-6 max-w-2xl text-sm text-ink/70">
            Files live in{' '}
            <code className="rounded-md bg-surface-3 px-1.5 py-0.5 text-xs text-ink">public/design/fareeq-v10/</code>
            . Missing files show a placeholder until added.
          </p>

          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {keys.map((key) => {
              const src = fareeqV10Assets[key]
              const missing = broken[key]
              return (
                <li
                  key={key}
                  className="overflow-hidden rounded-2xl border border-line bg-surface shadow-soft"
                >
                  <div className="border-b border-line bg-surface-3 px-3 py-2">
                    <span className="font-mono text-[11px] font-semibold text-ink/80">{key}</span>
                  </div>
                  <div className="relative flex min-h-[200px] items-center justify-center bg-surface-2 p-2">
                    {missing ? (
                      <p className="px-3 text-center text-xs text-ink/55">
                        Asset not found — add{' '}
                        <span className="font-mono text-[10px]">{decodeURIComponent(src.split('/').pop() ?? '')}</span>{' '}
                        to <span className="font-mono text-[10px]">public/design/fareeq-v10/</span>
                      </p>
                    ) : (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={src}
                        alt={key}
                        className="max-h-[min(480px,70vh)] w-full object-contain object-top"
                        loading="lazy"
                        onError={() => setBroken((prev) => ({ ...prev, [key]: true }))}
                      />
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      </div>
    </div>
  )
}
