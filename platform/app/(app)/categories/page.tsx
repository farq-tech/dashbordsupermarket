'use client'
import { useState, useMemo } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingOverlay } from '@/components/ui/spinner'
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
  const { lang, dashboardData, loading } = useAppStore()
  const isAr = lang === 'ar'
  const [sortBy, setSortBy] = useState<'product_count' | 'pricing_index' | 'competitive_count'>('product_count')
  const [selected, setSelected] = useState<CategoryKPI | null>(null)

  const categories = useMemo(
    () => dashboardData?.kpis.categories ?? [],
    [dashboardData?.kpis.categories],
  )

  const sorted = useMemo(() =>
    [...categories].sort((a, b) => {
      if (sortBy === 'product_count') return b.product_count - a.product_count
      if (sortBy === 'pricing_index') return a.pricing_index - b.pricing_index
      return b.competitive_count - a.competitive_count
    }),
    [categories, sortBy],
  )

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

  if (loading || !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/categories'].ar} title_en={PAGE_TITLES['/categories'].en} /><LoadingOverlay /></div>
  }

  return (
    <div className="animate-fade-in">
      <Topbar title_ar={PAGE_TITLES['/categories'].ar} title_en={PAGE_TITLES['/categories'].en} />
      <div className="page-shell">

        {/* Highlight chips */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-3">
          <div className="rounded-xl border border-[color:color-mix(in_srgb,var(--color-trend-up)_32%,#ffffff)] bg-[color:color-mix(in_srgb,var(--color-trend-up)_10%,#ffffff)] p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-semibold text-[color:#0a8f5a]">{isAr ? 'فرص عالية' : 'High Opportunities'}</p>
              <Badge variant="success">{highOpportunity.length}</Badge>
            </div>
            <p className="text-xs text-[color:var(--color-trend-up)]">{isAr ? 'أصناف بسعر أقل من السوق — رفع للهامش' : 'Categories priced below market — margin uplift'}</p>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-semibold text-red-800">{isAr ? 'أصناف خطرة' : 'At-Risk Categories'}</p>
              <Badge variant="danger">{highRisk.length}</Badge>
            </div>
            <p className="text-xs text-red-600">{isAr ? 'أسعار أعلى من السوق — خطر فقدان عملاء' : 'Prices above market — risk of losing customers'}</p>
          </div>
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-semibold text-amber-800">{isAr ? 'حساسة للسعر' : 'Price Sensitive'}</p>
              <Badge variant="warning">{priceSensitive.length}</Badge>
            </div>
            <p className="text-xs text-amber-600">{isAr ? 'أصناف بفجوات سعرية كبيرة' : 'Categories with large price gaps'}</p>
          </div>
        </div>

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
                    <th className="text-start px-4 py-[var(--density-table-cell-y)] text-xs font-semibold text-neutral-600">{isAr ? 'الصنف' : 'Category'}</th>
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
    </div>
  )
}
