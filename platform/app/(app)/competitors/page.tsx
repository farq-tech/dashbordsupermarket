'use client'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingOverlay } from '@/components/ui/spinner'
import { MultiBarChart } from '@/components/charts/BarChartComponent'
import { SimplePieChart } from '@/components/charts/PieChartComponent'
import { RetailerLogo } from '@/components/ui/RetailerLogo'

export default function CompetitorsPage() {
  const { lang, dashboardData, loading, selectedRetailer } = useAppStore()
  const isAr = lang === 'ar'

  const allKpis = dashboardData?.all_kpis ?? []
  const myKpis = allKpis.find(k => k.retailer.store_key === selectedRetailer?.store_key)
  const competitors = allKpis.filter(k => k.retailer.store_key !== selectedRetailer?.store_key)

  // Comparison table data
  const comparisonData = allKpis.map(k => ({
    name: isAr ? k.retailer.brand_ar : k.retailer.brand_en,
    [isAr ? 'نقاط الأداء' : 'Performance']: Math.round(k.performance_score),
    [isAr ? 'مؤشر التنافسية' : 'Competitive Index']: Math.round(k.competitive_index),
    [isAr ? 'التغطية %' : 'Coverage %']: Math.round(k.coverage_index),
  }))

  const chartKeys = [
    { dataKey: isAr ? 'نقاط الأداء' : 'Performance', name: isAr ? 'الأداء' : 'Performance', color: '#1b59f8' },
    { dataKey: isAr ? 'مؤشر التنافسية' : 'Competitive Index', name: isAr ? 'التنافسية' : 'Competitive', color: '#1fe08f' },
    { dataKey: isAr ? 'التغطية %' : 'Coverage %', name: isAr ? 'التغطية' : 'Coverage', color: '#f59e0b' },
  ]

  // Category dominance: who is cheapest most often per category
  const comparisons = dashboardData?.comparisons ?? []
  const catDominance = (() => {
    const catMap = new Map<string, { name_ar: string; name_en: string; cheapestBy: Record<number, number> }>()
    comparisons.forEach(c => {
      if (!catMap.has(c.category_en)) {
        catMap.set(c.category_en, { name_ar: c.category_ar, name_en: c.category_en, cheapestBy: {} })
      }
      const entry = catMap.get(c.category_en)!
      const cheapestSK = Object.entries(c.prices_by_store)
        .sort(([, a], [, b]) => a - b)[0]?.[0]
      if (cheapestSK) {
        const sk = parseInt(cheapestSK)
        entry.cheapestBy[sk] = (entry.cheapestBy[sk] ?? 0) + 1
      }
    })
    return Array.from(catMap.values())
      .map(c => {
        const winner = Object.entries(c.cheapestBy).sort(([, a], [, b]) => b - a)[0]
        const winnerKpis = allKpis.find(k => k.retailer.store_key === parseInt(winner?.[0] ?? '0'))
        return {
          name_ar: c.name_ar,
          name_en: c.name_en,
          dominant_store_key: parseInt(winner?.[0] ?? '0'),
          dominant_brand: winnerKpis ? (isAr ? winnerKpis.retailer.brand_ar : winnerKpis.retailer.brand_en) : '—',
          dominant_color: winnerKpis?.retailer.color ?? '#9ca3af',
          count: winner?.[1] ?? 0,
        }
      })
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
  })()

  // Price positioning pie per competitor
  const pricePie = allKpis.map(k => ({
    name: isAr ? k.retailer.brand_ar : k.retailer.brand_en,
    value: Math.round(k.avg_price * 100) / 100,
    color: k.retailer.color,
  }))

  if (loading || !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/competitors'].ar} title_en={PAGE_TITLES['/competitors'].en} /><LoadingOverlay /></div>
  }

  return (
    <div className="animate-fade-in">
      <Topbar title_ar={PAGE_TITLES['/competitors'].ar} title_en={PAGE_TITLES['/competitors'].en} />
      <div className="space-y-4 p-4 sm:space-y-6 sm:p-6">

        {/* Competitor Cards */}
        <div className="grid grid-cols-1 gap-3 sm:gap-4 md:grid-cols-2">
          {competitors.map(comp => {
            const myScore = myKpis?.performance_score ?? 0
            const compScore = comp.performance_score
            const iAhead = myScore >= compScore
            return (
              <Card key={comp.retailer.store_key} className="card-hover">
                <div className="flex items-start gap-4">
                  <RetailerLogo
                    retailer={comp.retailer}
                    label={isAr ? comp.retailer.brand_ar : comp.retailer.brand_en}
                    size={48}
                    rounded="xl"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-bold text-neutral-900">
                        {isAr ? comp.retailer.brand_ar : comp.retailer.brand_en}
                      </h3>
                      <Badge variant={iAhead ? 'success' : 'danger'}>
                        {iAhead ? (isAr ? 'أنت متقدم' : 'You Lead') : (isAr ? 'متأخر' : 'Behind')}
                      </Badge>
                    </div>
                    <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3 sm:gap-3">
                      {[
                        { label: isAr ? 'الأداء' : 'Performance', val: comp.performance_score.toFixed(0), unit: '' },
                        { label: isAr ? 'متوسط سعر' : 'Avg Price', val: comp.avg_price.toFixed(1), unit: ' SAR' },
                        { label: isAr ? 'التغطية' : 'Coverage', val: comp.coverage_index.toFixed(0), unit: '%' },
                      ].map((item, i) => (
                        <div key={i} className="text-center p-2 bg-neutral-50 rounded-lg">
                          <p className="text-lg font-bold tabular-nums" style={{ color: comp.retailer.color }}>
                            {item.val}{item.unit}
                          </p>
                          <p className="text-xs text-neutral-400">{item.label}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>

        {/* Multi-metric comparison */}
        <Card>
          <CardHeader>
            <CardTitle>{isAr ? 'مقارنة شاملة للمنافسين' : 'Comprehensive Competitor Comparison'}</CardTitle>
          </CardHeader>
          <CardContent>
            <MultiBarChart data={comparisonData} keys={chartKeys} height={280} />
          </CardContent>
        </Card>

        {/* Price positioning + Category dominance */}
        <div className="grid grid-cols-1 gap-4 sm:gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'تموضع الأسعار في السوق' : 'Market Price Positioning'}</CardTitle>
              <p className="text-xs text-neutral-400 mt-0.5">{isAr ? 'متوسط سعر كل سلسلة' : 'Average price per chain'}</p>
            </CardHeader>
            <CardContent>
              <SimplePieChart data={pricePie} height={240} innerRadius={50} outerRadius={85} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'هيمنة الأصناف' : 'Category Dominance'}</CardTitle>
              <p className="text-xs text-neutral-400 mt-0.5">{isAr ? 'من الأرخص في كل صنف' : 'Who is cheapest per category'}</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 mt-1">
                {catDominance.map((cat, i) => (
                  <div key={i} className="flex items-center gap-3 py-2 border-b border-neutral-50 last:border-0">
                    <span className="text-xs text-neutral-400 w-5 shrink-0">{i + 1}</span>
                    <span className="flex-1 text-sm text-neutral-700 truncate">
                      {isAr ? cat.name_ar : cat.name_en}
                    </span>
                    <span
                      className="text-xs font-semibold px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: `${cat.dominant_color}20`, color: cat.dominant_color }}
                    >
                      {cat.dominant_brand}
                    </span>
                    <span className="text-xs text-neutral-400 w-12 text-end">{cat.count} {isAr ? 'منتج' : 'prods'}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  )
}
