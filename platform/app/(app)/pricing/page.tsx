'use client'
import { useMemo } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingOverlay } from '@/components/ui/spinner'
import { SimpleBarChart } from '@/components/charts/BarChartComponent'
import { PriceScatterChart } from '@/components/charts/ScatterChartComponent'

export default function PricingPage() {
  const { lang, dashboardData, loading } = useAppStore()
  const isAr = lang === 'ar'

  const comparisons = useMemo(
    () => dashboardData?.comparisons ?? [],
    [dashboardData?.comparisons],
  )
  const kpis = dashboardData?.kpis

  const scatterData = useMemo(() =>
    comparisons
      .filter(c => c.your_price !== null)
      .slice(0, 300)
      .map(c => ({
        x: Math.round(c.market_avg * 100) / 100,
        y: c.your_price!,
        name: isAr ? c.title_ar : c.title_en,
        tag: c.tag,
      })),
    [comparisons, isAr],
  )

  const segments = useMemo(() => ({
    overpriced: comparisons.filter(c => c.tag === 'overpriced'),
    risk: comparisons.filter(c => c.tag === 'risk'),
    competitive: comparisons.filter(c => c.tag === 'competitive'),
    underpriced: comparisons.filter(c => c.tag === 'underpriced'),
    cheapest: comparisons.filter(c => c.price_rank === 1),
  }), [comparisons])

  // Gap distribution
  const gapBuckets = useMemo(() => {
    const stocked = comparisons.filter(c => c.your_price !== null)
    const buckets = [
      { name: isAr ? '< -10%' : '< -10%', count: 0, color: '#1fe08f' },
      { name: isAr ? '-10% إلى -5%' : '-10% to -5%', count: 0, color: '#5eead4' },
      { name: isAr ? '-5% إلى 0%' : '-5% to 0%', count: 0, color: '#93c5fd' },
      { name: isAr ? '0% إلى 5%' : '0% to 5%', count: 0, color: '#1b59f8' },
      { name: isAr ? '5% إلى 10%' : '5% to 10%', count: 0, color: '#f59e0b' },
      { name: isAr ? '10% إلى 20%' : '10% to 20%', count: 0, color: '#f97316' },
      { name: isAr ? '> 20%' : '> 20%', count: 0, color: '#ff3e13' },
    ]
    stocked.forEach(c => {
      const g = c.price_gap_pct
      if (g < -10) buckets[0].count++
      else if (g < -5) buckets[1].count++
      else if (g < 0) buckets[2].count++
      else if (g < 5) buckets[3].count++
      else if (g < 10) buckets[4].count++
      else if (g < 20) buckets[5].count++
      else buckets[6].count++
    })
    return buckets.map(b => ({ name: b.name, value: b.count, color: b.color }))
  }, [comparisons, isAr])

  // Category pricing index
  const catPricingData = useMemo(() =>
    (kpis?.categories ?? []).slice(0, 8).map(c => ({
      name: isAr ? c.name_ar.slice(0, 12) : c.name_en.slice(0, 12),
      [isAr ? 'مؤشر التسعير' : 'Pricing Index']: Math.round(c.pricing_index),
    })),
    [kpis, isAr],
  )

  // Recommendations for pricing
  const pricingRecs = dashboardData?.recommendations.filter(r => r.type === 'pricing') ?? []

  if (loading || !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/pricing'].ar} title_en={PAGE_TITLES['/pricing'].en} /><LoadingOverlay /></div>
  }

  const stocked = comparisons.filter(c => c.your_price !== null)
  const avgGap = stocked.length > 0
    ? stocked.reduce((s, c) => s + c.price_gap_pct, 0) / stocked.length
    : 0

  return (
    <div className="animate-fade-in">
      <Topbar title_ar={PAGE_TITLES['/pricing'].ar} title_en={PAGE_TITLES['/pricing'].en} />
      <div className="space-y-4 p-4 sm:space-y-6 sm:p-6">

        {/* Summary KPI row */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 md:grid-cols-3 lg:grid-cols-5">
          {[
            { label: isAr ? 'مرتفع السعر' : 'Overpriced', value: segments.overpriced.length, color: '#ff3e13' },
            { label: isAr ? 'خطر' : 'At Risk', value: segments.risk.length, color: '#f97316' },
            { label: isAr ? 'تنافسي' : 'Competitive', value: segments.competitive.length, color: '#1b59f8' },
            { label: isAr ? 'منخفض' : 'Underpriced', value: segments.underpriced.length, color: '#1fe08f' },
            { label: isAr ? 'الأرخص' : 'Cheapest', value: segments.cheapest.length, color: '#0f2552' },
          ].map(item => (
            <div key={item.label} className="bg-white rounded-xl border border-neutral-100 p-4 text-center">
              <p className="text-2xl font-bold tabular-nums" style={{ color: item.color }}>{item.value}</p>
              <p className="text-xs text-neutral-500 mt-1">{item.label}</p>
            </div>
          ))}
        </div>

        {/* Scatter + Distribution */}
        <div className="grid grid-cols-1 gap-4 sm:gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'سعرك مقابل متوسط السوق' : 'Your Price vs Market Avg'}</CardTitle>
              <p className="text-xs text-neutral-400 mt-0.5">
                {isAr ? 'كل نقطة = منتج. فوق الخط = أغلى، تحته = أرخص' : 'Each dot = product. Above line = costlier, below = cheaper'}
              </p>
            </CardHeader>
            <CardContent>
              <PriceScatterChart
                data={scatterData}
                height={280}
                xLabel={isAr ? 'متوسط السوق' : 'Market Avg'}
                yLabel={isAr ? 'سعرك' : 'Your Price'}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'توزيع فجوة الأسعار' : 'Price Gap Distribution'}</CardTitle>
              <p className="text-xs text-neutral-400 mt-0.5">
                {isAr ? `متوسط الفجوة: ${avgGap > 0 ? '+' : ''}${avgGap.toFixed(1)}%` : `Avg gap: ${avgGap > 0 ? '+' : ''}${avgGap.toFixed(1)}%`}
              </p>
            </CardHeader>
            <CardContent>
              <SimpleBarChart
                data={gapBuckets}
                dataKey="value"
                nameKey="name"
                colors={gapBuckets.map(b => b.color)}
                height={280}
              />
            </CardContent>
          </Card>
        </div>

        {/* Category Pricing Index */}
        <Card>
          <CardHeader>
            <CardTitle>{isAr ? 'مؤشر التسعير حسب الصنف (100 = متوسط السوق)' : 'Pricing Index by Category (100 = Market Avg)'}</CardTitle>
          </CardHeader>
          <CardContent>
            <SimpleBarChart
              data={catPricingData}
              dataKey={isAr ? 'مؤشر التسعير' : 'Pricing Index'}
              colors={catPricingData.map(d => {
                const v = d[isAr ? 'مؤشر التسعير' : 'Pricing Index'] as number
                return v > 108 ? '#ff3e13' : v > 103 ? '#f97316' : v < 95 ? '#1fe08f' : '#1b59f8'
              })}
              height={260}
            />
          </CardContent>
        </Card>

        {/* Pricing Recommendations Engine */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{isAr ? 'محرك توصيات التسعير' : 'Pricing Recommendations Engine'}</CardTitle>
              <Badge variant="info">{pricingRecs.length} {isAr ? 'توصية' : 'recommendations'}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {pricingRecs.length === 0 ? (
              <p className="text-neutral-400 text-sm">{isAr ? 'لا توجد توصيات تسعير حالياً' : 'No pricing recommendations currently'}</p>
            ) : (
              <div className="space-y-3">
                {pricingRecs.slice(0, 6).map(rec => (
                  <div key={rec.id} className="flex items-start gap-3 p-4 rounded-xl bg-neutral-50 hover:bg-neutral-100 transition-colors">
                    <div
                      className="h-8 w-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5"
                      style={{ backgroundColor: rec.impact === 'high' ? '#dc2626' : rec.impact === 'medium' ? '#f59e0b' : '#9ca3af' }}
                    >
                      {rec.priority}
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-neutral-800 text-sm">
                        {isAr ? rec.title_ar : rec.title_en}
                      </p>
                      <p className="text-xs text-neutral-500 mt-0.5">
                        {isAr ? rec.reason_ar : rec.reason_en}
                      </p>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-xs text-neutral-400">
                          {isAr ? 'الإجراء:' : 'Action:'}{' '}
                          <span className="font-medium text-neutral-700">
                            {isAr ? rec.action_ar : rec.action_en}
                          </span>
                        </span>
                        {rec.value_estimate != null && rec.value_estimate > 0 && (
                          <span className="text-xs font-medium text-[color:var(--color-trend-up)]">
                            {rec.value_estimate.toLocaleString()} {isAr ? 'ريال (من البيانات)' : 'SAR (from data)'}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

      </div>
    </div>
  )
}
