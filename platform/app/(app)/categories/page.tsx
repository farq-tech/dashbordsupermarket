'use client'
import { useState, useMemo, useRef } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingOverlay } from '@/components/ui/spinner'
import { ErrorState } from '@/components/ui/error-state'
import { SimpleBarChart } from '@/components/charts/BarChartComponent'
import type { CategoryKPI } from '@/lib/types'
import { fareeqChart } from '@/lib/design-system'

function CategoryStatus({ kpi, isAr }: { kpi: CategoryKPI; isAr: boolean }) {
  if (kpi.pricing_index > 110) return <Badge variant="danger">{isAr ? 'مرتفع السعر' : 'Overpriced'}</Badge>
  if (kpi.pricing_index > 103) return <Badge variant="warning">{isAr ? 'أعلى بقليل' : 'Slightly High'}</Badge>
  if (kpi.pricing_index < 93) return <Badge variant="success">{isAr ? 'أرخص' : 'Below Market'}</Badge>
  if (kpi.competitive_count + kpi.cheapest_count > kpi.product_count * 0.5) return <Badge variant="info">{isAr ? 'تنافسي' : 'Competitive'}</Badge>
  return <Badge variant="neutral">{isAr ? 'متوسط' : 'Average'}</Badge>
}

export default function CategoriesPage() {
  const { lang, dashboardData, loading, error, forceRefresh } = useAppStore()
  const isAr = lang === 'ar'
  const [sortBy, setSortBy] = useState<'product_count' | 'pricing_index' | 'competitive_count'>('product_count')
  const [selected, setSelected] = useState<CategoryKPI | null>(null)
  const [quickFilter, setQuickFilter] = useState<'opportunity' | 'risk' | 'sensitive' | null>(null)
  const tableRef = useRef<HTMLDivElement>(null)

  const categories = useMemo(
    () => dashboardData?.kpis.categories ?? [],
    [dashboardData?.kpis.categories],
  )

  const sorted = useMemo(() => {
    let list = [...categories]
    if (quickFilter === 'opportunity') list = list.filter(c => c.pricing_index < 95 && c.product_count > 10)
    else if (quickFilter === 'risk') list = list.filter(c => c.pricing_index > 108 && c.product_count > 5)
    else if (quickFilter === 'sensitive') list = list.filter(c => {
      const spreadPct = c.market_avg_price > 0 ? ((c.avg_price - c.market_avg_price) / c.market_avg_price) * 100 : 0
      return Math.abs(spreadPct) > 8
    })
    return list.sort((a, b) => {
      if (sortBy === 'product_count') return b.product_count - a.product_count
      if (sortBy === 'pricing_index') return a.pricing_index - b.pricing_index
      return b.competitive_count - a.competitive_count
    })
  }, [categories, sortBy, quickFilter])

  const chartData = sorted.slice(0, 10).map(c => ({
    name: isAr ? c.name_ar.slice(0, 14) : c.name_en.slice(0, 14),
    [isAr ? 'المنتجات' : 'Products']: c.product_count,
    [isAr ? 'تنافسي' : 'Competitive']: c.competitive_count + c.cheapest_count,
  }))

  const pricingIndexData = sorted.slice(0, 10).map(c => ({
    name: isAr ? c.name_ar.slice(0, 12) : c.name_en.slice(0, 12),
    [isAr ? 'مؤشر التسعير' : 'Pricing Index']: Math.round(c.pricing_index),
  }))

  const highOpportunity = sorted.filter(c => c.pricing_index < 95 && c.product_count > 10)
  const highRisk = sorted.filter(c => c.pricing_index > 108 && c.product_count > 5)
  const priceSensitive = sorted.filter(c => {
    const spreadPct = c.market_avg_price > 0 ? ((c.avg_price - c.market_avg_price) / c.market_avg_price) * 100 : 0
    return Math.abs(spreadPct) > 8
  })

  if (!loading && error && !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/categories'].ar} title_en={PAGE_TITLES['/categories'].en} /><div className="page-shell"><ErrorState lang={lang} onRetry={forceRefresh} /></div></div>
  }

  if (loading || !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/categories'].ar} title_en={PAGE_TITLES['/categories'].en} /><LoadingOverlay lang={lang} /></div>
  }

  return (
    <div className="animate-fade-in">
      <Topbar title_ar={PAGE_TITLES['/categories'].ar} title_en={PAGE_TITLES['/categories'].en} />
      <div className="page-shell">

        {/* Highlight chips — click to filter table */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-3">
          {[
            {
              key: 'opportunity' as const,
              count: highOpportunity.length,
              title_ar: 'فرص عالية', title_en: 'High Opportunities',
              desc_ar: 'أصناف بسعر أقل من السوق — رفع للهامش',
              desc_en: 'Categories priced below market — margin uplift',
              cls: 'rounded-xl border p-4 cursor-pointer transition-all',
              activeCls: 'ring-2 ring-green-500',
              style: { borderColor: 'color-mix(in srgb, var(--color-trend-up) 32%, #ffffff)', background: 'color-mix(in srgb, var(--color-trend-up) 10%, #ffffff)' },
              titleColor: '#0a8f5a', descColor: 'var(--color-trend-up)', badge: 'success' as const,
            },
            {
              key: 'risk' as const,
              count: highRisk.length,
              title_ar: 'أصناف خطرة', title_en: 'At-Risk Categories',
              desc_ar: 'أسعار أعلى من السوق — خطر فقدان عملاء',
              desc_en: 'Prices above market — risk of losing customers',
              cls: 'rounded-xl border border-red-200 bg-red-50 p-4 cursor-pointer transition-all',
              activeCls: 'ring-2 ring-red-500',
              style: {},
              titleColor: '#991b1b', descColor: '#dc2626', badge: 'danger' as const,
            },
            {
              key: 'sensitive' as const,
              count: priceSensitive.length,
              title_ar: 'حساسة للسعر', title_en: 'Price Sensitive',
              desc_ar: 'أصناف بفجوات سعرية كبيرة',
              desc_en: 'Categories with large price gaps',
              cls: 'rounded-xl border border-amber-200 bg-amber-50 p-4 cursor-pointer transition-all',
              activeCls: 'ring-2 ring-amber-500',
              style: {},
              titleColor: '#92400e', descColor: '#b45309', badge: 'warning' as const,
            },
          ].map(tile => (
            <button
              key={tile.key}
              type="button"
              className={`${tile.cls} text-start ${quickFilter === tile.key ? tile.activeCls : 'hover:opacity-90'}`}
              style={tile.style}
              onClick={() => {
                setQuickFilter(quickFilter === tile.key ? null : tile.key)
                setSelected(null)
                requestAnimationFrame(() => tableRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
              }}
            >
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-semibold" style={{ color: tile.titleColor }}>{isAr ? tile.title_ar : tile.title_en}</p>
                <Badge variant={tile.badge}>{tile.count}</Badge>
              </div>
              <p className="text-xs" style={{ color: tile.descColor }}>{isAr ? tile.desc_ar : tile.desc_en}</p>
              <p className="text-[10px] mt-1.5 font-medium opacity-60" style={{ color: tile.titleColor }}>
                {quickFilter === tile.key
                  ? (isAr ? '← انقر لإلغاء الفلتر' : '← Click to clear filter')
                  : (isAr ? 'انقر للعرض في الجدول ↓' : 'Click to filter table ↓')}
              </p>
            </button>
          ))}
        </div>
        {quickFilter && (
          <div className="flex items-center gap-2">
            <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              {isAr ? `فلتر نشط: ${quickFilter === 'opportunity' ? 'فرص عالية' : quickFilter === 'risk' ? 'أصناف خطرة' : 'حساسة للسعر'} — ${sorted.length} صنف` : `Active filter: ${quickFilter} — ${sorted.length} categories`}
            </span>
            <button
              type="button"
              className="text-xs underline"
              style={{ color: 'var(--color-interactive)' }}
              onClick={() => setQuickFilter(null)}
            >
              {isAr ? 'إلغاء' : 'Clear'}
            </button>
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'أعلى الأصناف بعدد المنتجات' : 'Top Categories by Products'}</CardTitle>
            </CardHeader>
            <CardContent>
              <SimpleBarChart
                data={chartData}
                dataKey={isAr ? 'المنتجات' : 'Products'}
                height={240}
                color={fareeqChart.blue}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'مؤشر التسعير (100 = السوق)' : 'Pricing Index (100 = Market)'}</CardTitle>
            </CardHeader>
            <CardContent>
              <SimpleBarChart
                data={pricingIndexData}
                dataKey={isAr ? 'مؤشر التسعير' : 'Pricing Index'}
                colors={pricingIndexData.map(d => {
                  const v = d[isAr ? 'مؤشر التسعير' : 'Pricing Index'] as number
                  return v > 108 ? fareeqChart.coral : v > 103 ? fareeqChart.orange : v < 95 ? fareeqChart.green : fareeqChart.blue
                })}
                height={240}
              />
            </CardContent>
          </Card>
        </div>

        {/* Full Category Table */}
        <div ref={tableRef} className="scroll-mt-24">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between flex-wrap gap-2">
              <CardTitle>{isAr ? 'جميع الأصناف' : 'All Categories'}</CardTitle>
              <div className="flex gap-2">
                {[
                  { key: 'product_count', ar: 'عدد المنتجات', en: 'Products' },
                  { key: 'pricing_index', ar: 'مؤشر السعر', en: 'Price Index' },
                  { key: 'competitive_count', ar: 'التنافسية', en: 'Competitive' },
                ].map(s => (
                  <button
                    key={s.key}
                    onClick={() => setSortBy(s.key as typeof sortBy)}
                    className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                      sortBy === s.key
                        ? 'bg-[var(--color-interactive)] text-white border-[var(--color-interactive)]'
                        : 'border-neutral-200 text-neutral-600 hover:bg-neutral-50'
                    }`}
                  >
                    {isAr ? s.ar : s.en}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-neutral-50 border-b border-neutral-100">
                    <th className="text-start px-4 py-[var(--density-table-cell-y)] text-xs font-semibold text-neutral-600">{isAr ? 'الصنف ↕' : 'Category ↕'}</th>
                    <th className="text-end px-4 py-[var(--density-table-cell-y)] text-xs font-semibold text-neutral-600">{isAr ? 'منتجات' : 'Products'}</th>
                    <th className="text-end px-4 py-[var(--density-table-cell-y)] text-xs font-semibold text-neutral-600">{isAr ? 'متوسط سعرك' : 'Avg Price'}</th>
                    <th className="text-end px-4 py-[var(--density-table-cell-y)] text-xs font-semibold text-neutral-600">{isAr ? 'متوسط السوق' : 'Market Avg'}</th>
                    <th className="text-end px-4 py-[var(--density-table-cell-y)] text-xs font-semibold text-neutral-600">{isAr ? 'مؤشر السعر' : 'Price Idx'}</th>
                    <th className="text-end px-4 py-[var(--density-table-cell-y)] text-xs font-semibold text-neutral-600">{isAr ? 'تنافسي' : 'Competitive'}</th>
                    <th className="text-center px-4 py-[var(--density-table-cell-y)] text-xs font-semibold text-neutral-600">{isAr ? 'الحالة' : 'Status'}</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((cat, i) => (
                    <tr
                      key={i}
                      className={`border-b border-neutral-50 cursor-pointer transition-colors ${selected?.name_en === cat.name_en ? 'bg-[var(--color-surface-hover)]' : 'hover:bg-neutral-50'}`}
                      onClick={() => setSelected(selected?.name_en === cat.name_en ? null : cat)}
                    >
                      <td className="px-4 py-[var(--density-table-cell-y)] font-medium text-neutral-800">
                        {isAr ? cat.name_ar : cat.name_en}
                      </td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-end tabular-nums text-neutral-600">{cat.product_count}</td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-end tabular-nums text-neutral-600">{cat.avg_price.toFixed(2)}</td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-end tabular-nums text-neutral-500">{cat.market_avg_price.toFixed(2)}</td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-end">
                        <span className={`font-semibold tabular-nums ${
                          cat.pricing_index > 108 ? 'text-red-600' :
                          cat.pricing_index < 95 ? 'text-[color:var(--color-trend-up)]' : 'text-[color:var(--color-interactive)]'
                        }`}>
                          {cat.pricing_index.toFixed(0)}
                        </span>
                      </td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-end tabular-nums text-neutral-600">
                        {cat.competitive_count + cat.cheapest_count}
                      </td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-center">
                        <CategoryStatus kpi={cat} isAr={isAr} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
        </div>

        {/* Category detail panel */}
        {selected && (
          <Card className="animate-fade-in border-[var(--color-interactive)] ring-1 ring-[var(--color-interactive)]/20">
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <CardTitle>{isAr ? selected.name_ar : selected.name_en}</CardTitle>
                  <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
                    {isAr ? selected.name_en : selected.name_ar}
                  </p>
                </div>
                <button
                  type="button"
                  className="text-xs px-3 py-1.5 rounded-lg border"
                  style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
                  onClick={() => setSelected(null)}
                >
                  {isAr ? 'إغلاق' : 'Close'}
                </button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                {[
                  { label: isAr ? 'عدد المنتجات' : 'Products', value: selected.product_count },
                  { label: isAr ? 'متوسط سعرك' : 'Your Avg Price', value: `${selected.avg_price.toFixed(2)} SAR` },
                  { label: isAr ? 'متوسط السوق' : 'Market Avg', value: `${selected.market_avg_price.toFixed(2)} SAR` },
                  { label: isAr ? 'مؤشر السعر' : 'Pricing Index', value: `${Math.round(selected.pricing_index)}%` },
                  { label: isAr ? 'تنافسي + الأرخص' : 'Competitive + Cheapest', value: selected.competitive_count + selected.cheapest_count },
                  { label: isAr ? 'مرتفع السعر' : 'Overpriced', value: selected.overpriced_count ?? '—' },
                  { label: isAr ? 'الأرخص في السوق' : 'Cheapest in Market', value: selected.cheapest_count ?? '—' },
                  { label: isAr ? 'الحالة' : 'Status', value: <CategoryStatus kpi={selected} isAr={isAr} /> },
                ].map((item, i) => (
                  <div key={i} className="rounded-lg p-3" style={{ background: 'var(--color-surface-muted)' }}>
                    <p className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>{item.label}</p>
                    <p className="text-sm font-semibold mt-0.5" style={{ color: 'var(--color-text-primary)' }}>{item.value}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

      </div>
    </div>
  )
}
