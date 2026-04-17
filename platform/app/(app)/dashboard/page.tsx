'use client'
import { useEffect } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { KpiCard } from '@/components/ui/kpi-card'
import { Badge } from '@/components/ui/badge'
import { LoadingOverlay } from '@/components/ui/spinner'
import { SimpleBarChart, MultiBarChart } from '@/components/charts/BarChartComponent'
import { SimplePieChart } from '@/components/charts/PieChartComponent'
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Lightbulb, Target } from 'lucide-react'
import Link from 'next/link'

export default function DashboardPage() {
  const { lang, dashboardData, loading, selectedRetailer, fetchData } = useAppStore()

  useEffect(() => {
    if (!dashboardData && !loading) fetchData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (loading || !dashboardData) {
    return (
      <div>
        <Topbar title_ar="لوحة الأداء" title_en="Performance Dashboard" />
        <LoadingOverlay />
      </div>
    )
  }

  const { kpis, recommendations, alerts, market, all_kpis } = dashboardData
  const isAr = lang === 'ar'

  // Market comparison chart data
  const marketChartData = market.map(m => ({
    name: isAr ? m.retailer.brand_ar : m.retailer.brand_en,
    [isAr ? 'متوسط السعر' : 'Avg Price']: m.avg_price,
    color: m.retailer.color,
  }))

  // Category performance (top 6)
  const topCats = kpis.categories.slice(0, 6)
  const catChartData = topCats.map(c => ({
    name: isAr ? c.name_ar.slice(0, 14) : c.name_en.slice(0, 14),
    [isAr ? 'عدد المنتجات' : 'Products']: c.product_count,
    [isAr ? 'مؤشر السعر' : 'Price Index']: Math.round(c.pricing_index),
  }))

  // Pricing distribution pie
  const pieData = [
    { name: isAr ? 'تنافسي' : 'Competitive', value: kpis.competitive_count, color: '#2563eb' },
    { name: isAr ? 'مرتفع السعر' : 'Overpriced', value: kpis.overpriced_count, color: '#dc2626' },
    { name: isAr ? 'منخفض' : 'Underpriced', value: kpis.underpriced_count, color: '#16a34a' },
    { name: isAr ? 'الأرخص' : 'Cheapest', value: kpis.cheapest_count, color: '#1a5c3a' },
  ].filter(d => d.value > 0)

  // Coverage comparison
  const coverageData = market.map(m => ({
    name: isAr ? m.retailer.brand_ar : m.retailer.brand_en,
    value: m.coverage_pct,
    color: m.retailer.color,
  }))

  const getPricingIndexLabel = (idx: number) => {
    if (idx < 95) return { label: isAr ? 'أقل من السوق' : 'Below Market', color: '#16a34a' }
    if (idx <= 105) return { label: isAr ? 'متوسط السوق' : 'At Market', color: '#2563eb' }
    return { label: isAr ? 'أعلى من السوق' : 'Above Market', color: '#dc2626' }
  }
  const piLabel = getPricingIndexLabel(kpis.pricing_index)

  const myKpis = all_kpis.find(k => k.retailer.store_key === selectedRetailer?.store_key) ?? kpis
  const marketRank = [...all_kpis].sort((a, b) => b.performance_score - a.performance_score)
    .findIndex(k => k.retailer.store_key === selectedRetailer?.store_key) + 1

  return (
    <div className="animate-fade-in">
      <Topbar
        title_ar="لوحة الأداء"
        title_en="Performance Dashboard"
        subtitle_ar={`${isAr ? 'السلسلة:' : 'Chain:'} ${isAr ? selectedRetailer?.brand_ar : selectedRetailer?.brand_en}`}
      />

      <div className="p-6 space-y-6">
        {/* Alerts banner */}
        {alerts.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-800 text-sm">
                {alerts.length} {isAr ? 'تنبيه يتطلب انتباهك' : 'alerts require attention'}
              </p>
              <p className="text-amber-600 text-xs mt-0.5">
                {alerts[0]?.[isAr ? 'title_ar' : 'title_en']}
              </p>
            </div>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard
            title_ar="درجة الأداء"
            title_en="Performance Score"
            value={myKpis.performance_score.toFixed(0)}
            unit="/100"
            subtitle={isAr ? `ترتيبك: #${marketRank} بين السلاسل` : `Rank: #${marketRank} among chains`}
            color="#043434"
            icon={<Target className="h-5 w-5" />}
            lang={lang}
          />
          <KpiCard
            title_ar="نسبة الأسعار التنافسية"
            title_en="Competitive Price Share"
            value={myKpis.competitive_index.toFixed(0)}
            unit="%"
            subtitle={isAr ? 'نسبة المنتجات ضمن نطاق السعر التنافسي' : '% products priced competitively'}
            color="#2563eb"
            icon={<TrendingUp className="h-5 w-5" />}
            lang={lang}
          />
          <KpiCard
            title_ar="مؤشر السعر مقابل السوق"
            title_en="Pricing Index"
            value={myKpis.pricing_index.toFixed(0)}
            unit="%"
            subtitle={piLabel.label}
            color={piLabel.color}
            icon={<TrendingDown className="h-5 w-5" />}
            lang={lang}
          />
          <KpiCard
            title_ar="تغطية المنتجات (مقارنة بالسوق)"
            title_en="Product Coverage (vs Market)"
            value={myKpis.coverage_index.toFixed(0)}
            unit="%"
            subtitle={`${myKpis.covered_products} / ${myKpis.total_products} ${isAr ? 'منتج' : 'products'}`}
            color="#ca8a04"
            icon={<CheckCircle className="h-5 w-5" />}
            lang={lang}
          />
        </div>

        {/* Secondary KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-[var(--radius-lg)] border p-4" style={{ borderColor: 'var(--color-border)' }}>
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{isAr ? 'متوسط سعرك' : 'Your Avg Price'}</p>
            <p className="text-xl font-bold mt-1 tabular-nums" style={{ color: 'var(--color-text-primary)' }}>
              {myKpis.avg_price.toFixed(2)} <span className="text-sm" style={{ color: '#889DB4' }}>{isAr ? 'ريال' : 'SAR'}</span>
            </p>
          </div>
          <div className="bg-white rounded-[var(--radius-lg)] border p-4" style={{ borderColor: 'var(--color-border)' }}>
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{isAr ? 'متوسط السوق' : 'Market Avg Price'}</p>
            <p className="text-xl font-bold mt-1 tabular-nums" style={{ color: 'var(--color-text-primary)' }}>
              {myKpis.market_avg_price.toFixed(2)} <span className="text-sm" style={{ color: '#889DB4' }}>{isAr ? 'ريال' : 'SAR'}</span>
            </p>
          </div>
          <div className="bg-white rounded-[var(--radius-lg)] border p-4" style={{ borderColor: 'var(--color-border)' }}>
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{isAr ? 'منتجات أعلى من المنافسين' : 'Higher Than Competitors'}</p>
            <p className="text-xl font-bold text-red-600 mt-1 tabular-nums">{myKpis.overpriced_count}</p>
          </div>
          <div className="bg-white rounded-[var(--radius-lg)] border p-4" style={{ borderColor: 'var(--color-border)' }}>
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{isAr ? 'منتجات ضمن الأرخص' : 'Among the Cheapest'}</p>
            <p className="text-xl font-bold text-green-600 mt-1 tabular-nums">{myKpis.cheapest_count}</p>
          </div>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'مقارنة متوسط الأسعار' : 'Avg Price Comparison'}</CardTitle>
            </CardHeader>
            <CardContent>
              <SimpleBarChart
                data={marketChartData}
                dataKey={isAr ? 'متوسط السعر' : 'Avg Price'}
                colors={market.map(m => m.retailer.color)}
                unit=" SAR"
                height={220}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'توزيع التسعير' : 'Pricing Distribution'}</CardTitle>
            </CardHeader>
            <CardContent>
              <SimplePieChart data={pieData} height={220} />
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>{isAr ? 'أداء الأصناف الرئيسية' : 'Top Category Performance'}</CardTitle>
              </CardHeader>
              <CardContent>
                <MultiBarChart
                  data={catChartData}
                  keys={[
                    { dataKey: isAr ? 'عدد المنتجات' : 'Products', name: isAr ? 'المنتجات' : 'Products', color: '#1a5c3a' },
                    { dataKey: isAr ? 'مؤشر السعر' : 'Price Index', name: isAr ? 'مؤشر السعر' : 'Price Index', color: '#2ecc71' },
                  ]}
                  height={240}
                />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'تغطية السوق' : 'Market Coverage'}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 mt-2">
                {coverageData.map((d, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium text-neutral-700">{d.name}</span>
                      <span className="text-neutral-500">{d.value}%</span>
                    </div>
                    <div className="h-2 bg-neutral-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${d.value}%`, backgroundColor: d.color }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* AI Recommendations */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                <CardTitle>{isAr ? 'توصيات الذكاء الاصطناعي — أهم الإجراءات هذا الأسبوع' : 'AI Recommendations — Top Actions This Week'}</CardTitle>
              </div>
              <Link href="/recommendations" className="text-xs text-[#1a5c3a] hover:underline font-medium">
                {isAr ? 'عرض الكل ←' : '→ View All'}
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recommendations.slice(0, 5).map(rec => (
                <div key={rec.id} className="flex items-start gap-3 p-3 rounded-lg bg-neutral-50 hover:bg-neutral-100 transition-colors">
                  <Badge
                    variant={rec.impact === 'high' ? 'danger' : rec.impact === 'medium' ? 'warning' : 'neutral'}
                    size="sm"
                    className="mt-0.5 shrink-0"
                  >
                    {isAr
                      ? rec.impact === 'high' ? 'عالي' : rec.impact === 'medium' ? 'متوسط' : 'منخفض'
                      : rec.impact}
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-neutral-800 leading-snug">
                      {isAr ? rec.title_ar : rec.title_en}
                    </p>
                    <p className="text-xs text-neutral-400 mt-0.5">
                      {isAr ? rec.reason_ar : rec.reason_en}
                    </p>
                  </div>
                  <Badge variant="neutral" size="sm" className="shrink-0">
                    {isAr ? rec.category_ar : rec.category_en}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
