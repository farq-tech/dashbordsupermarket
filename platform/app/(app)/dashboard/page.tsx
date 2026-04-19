'use client'
import { Suspense, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { KpiCard } from '@/components/ui/kpi-card'
import { InsightCard } from '@/components/ui/insight-card'
import { Badge } from '@/components/ui/badge'
import { SimpleBarChart, CategoryPerformanceComboChart } from '@/components/charts/BarChartComponent'
import { SimplePieChart } from '@/components/charts/PieChartComponent'
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Lightbulb, Target } from 'lucide-react'
import Link from 'next/link'
import { PAGE_TITLES } from '@/lib/navConfig'
import { getPreviousSnapshot, type KpiSnapshot } from '@/lib/kpiSnapshotHistory'
import { ChartReveal } from '@/components/ui/chart-reveal'
import { EmptyState } from '@/components/ui/empty-state'
import { ChartCardSkeleton, KpiCardSkeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { fareeqChart, fareeqHex } from '@/lib/design-system'

function DashboardPageInner() {
  const searchParams = useSearchParams()
  const focusKpi = searchParams.get('kpi')
  const { lang, dashboardData, loading, selectedRetailer, fetchData, dataSource, forceRefresh } = useAppStore()

  useEffect(() => {
    if (!dashboardData && !loading) fetchData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!focusKpi || !dashboardData) return
    const id = `kpi-${focusKpi}`
    requestAnimationFrame(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
  }, [focusKpi, dashboardData])

  if (loading || !dashboardData) {
    const t = PAGE_TITLES['/dashboard']
    return (
      <div>
        <Topbar
          title_ar={t.ar}
          title_en={t.en}
          description_ar="ملخص تنفيذي لأداء السلسلة مقارنة بالسوق."
          description_en="Executive view of your chain’s performance vs the market."
        />
        <div className="page-shell">
          <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] sm:grid-cols-2 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <KpiCardSkeleton key={i} />
            ))}
          </div>
          <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-2">
            <ChartCardSkeleton height={220} />
            <ChartCardSkeleton height={220} />
          </div>
          <ChartCardSkeleton height={260} />
        </div>
      </div>
    )
  }

  const { kpis, recommendations, alerts, market, all_kpis } = dashboardData
  const isAr = lang === 'ar'
  const hasCriticalAlerts = alerts.some(a => a.severity === 'high')

  // Market comparison chart data
  const marketChartData = market.map(m => ({
    name: isAr ? m.retailer.brand_ar : m.retailer.brand_en,
    [isAr ? 'متوسط السعر' : 'Avg Price']: m.avg_price,
    color: m.retailer.color,
  }))

  // Category performance (top 6) + prior-period price index (from last KPI snapshot)
  const topCats = kpis.categories.slice(0, 6)
  const productsKey = isAr ? 'عدد المنتجات' : 'Products'
  const priceKey = isAr ? 'مؤشر السعر' : 'Price Index'
  const pricePrevKey = isAr ? 'مؤشر سعر (سابق)' : 'Price idx (prior sync)'

  const currentSnapshot: KpiSnapshot | null =
    selectedRetailer && dashboardData
      ? {
          at: dashboardData.last_updated,
          store_key: selectedRetailer.store_key,
          source: dataSource,
          performance_score: kpis.performance_score,
          competitive_index: kpis.competitive_index,
          coverage_index: kpis.coverage_index,
          pricing_index: kpis.pricing_index,
        }
      : null
  const prevSnapshot = currentSnapshot ? getPreviousSnapshot(currentSnapshot) : null
  const priceDriftRatio =
    prevSnapshot && kpis.pricing_index ? prevSnapshot.pricing_index / kpis.pricing_index : 1

  const catChartData = topCats.map(c => ({
    name: isAr ? c.name_ar.slice(0, 14) : c.name_en.slice(0, 14),
    [productsKey]: c.product_count,
    [priceKey]: Math.round(c.pricing_index),
    [pricePrevKey]: prevSnapshot ? Math.round(c.pricing_index * priceDriftRatio) : null,
  }))

  // Pricing distribution pie
  const pieData = [
    { name: isAr ? 'تنافسي' : 'Competitive', value: kpis.competitive_count, color: fareeqChart.blue },
    { name: isAr ? 'مرتفع السعر' : 'Overpriced', value: kpis.overpriced_count, color: fareeqChart.coral },
    { name: isAr ? 'منخفض' : 'Underpriced', value: kpis.underpriced_count, color: fareeqChart.green },
    { name: isAr ? 'الأرخص' : 'Cheapest', value: kpis.cheapest_count, color: fareeqChart.deepBlue },
  ].filter(d => d.value > 0)

  // Coverage comparison
  const coverageData = market.map(m => ({
    name: isAr ? m.retailer.brand_ar : m.retailer.brand_en,
    value: m.coverage_pct,
    color: m.retailer.color,
  }))

  const getPricingIndexLabel = (idx: number) => {
    if (idx < 95) return { label: isAr ? 'أقل من السوق' : 'Below Market', color: fareeqChart.green }
    if (idx <= 105) return { label: isAr ? 'متوسط السوق' : 'At Market', color: fareeqChart.blue }
    return { label: isAr ? 'أعلى من السوق' : 'Above Market', color: fareeqChart.coral }
  }
  const piLabel = getPricingIndexLabel(kpis.pricing_index)

  const myKpis = all_kpis.find(k => k.retailer.store_key === selectedRetailer?.store_key) ?? kpis
  const marketRank = [...all_kpis].sort((a, b) => b.performance_score - a.performance_score)
    .findIndex(k => k.retailer.store_key === selectedRetailer?.store_key) + 1

  const pageTitle = PAGE_TITLES['/dashboard']
  let insightBlock: {
    tone: 'attention' | 'positive'
    title_ar: string
    title_en: string
    body_ar: string
    body_en: string
  }
  if (alerts.length > 0) {
    insightBlock = {
      tone: 'attention',
      title_ar: 'مخاطر وتنبيهات تحتاج متابعة',
      title_en: 'Risks and alerts to address',
      body_ar: `يوجد ${alerts.length} تنبيه نشط. راجع التفاصيل في التوصيات التشغيلية أو أضف البنود إلى مركز اتخاذ القرار.`,
      body_en: `You have ${alerts.length} active alert(s). Review Action Recommendations or add items to the Decision Hub.`,
    }
  } else if (myKpis.overpriced_count > 80) {
    insightBlock = {
      tone: 'attention',
      title_ar: 'ضغط تسعير مقابل السوق',
      title_en: 'Pricing pressure vs market',
      body_ar: `عدد كبير من المنتجات بأسعار أعلى من السوق (${myKpis.overpriced_count}). يُنصح بمراجعة استراتيجية التسعير والتوصيات.`,
      body_en: `Many SKUs are priced above market (${myKpis.overpriced_count}). Consider reviewing Pricing Strategy and recommendations.`,
    }
  } else {
    insightBlock = {
      tone: 'positive',
      title_ar: 'قراءة سريعة للوضع التنافسي',
      title_en: 'Competitive snapshot',
      body_ar: `أداء السلسلة ضمن نطاق يمكن التنبؤ به. تغطية السوق ${myKpis.coverage_index.toFixed(0)}٪ ومؤشر السعر ${myKpis.pricing_index.toFixed(0)}٪ مقارنة بالمتوسط.`,
      body_en: `Your chain shows a stable position: ${myKpis.coverage_index.toFixed(0)}% coverage and ${myKpis.pricing_index.toFixed(0)}% pricing index vs market average.`,
    }
  }

  return (
    <div className="animate-fade-in">
      <Topbar
        title_ar={pageTitle.ar}
        title_en={pageTitle.en}
        subtitle_ar={selectedRetailer ? `الشركة: ${selectedRetailer.brand_ar}` : undefined}
        subtitle_en={selectedRetailer ? `Business: ${selectedRetailer.brand_en}` : undefined}
        description_ar="ماذا يحدث، لماذا يهم، وما الخطوة التالية — في نظرة واحدة."
        description_en="What is happening, why it matters, and what to do next — in one view."
      />

      <div className="page-shell">
        <InsightCard
          lang={lang}
          tone={insightBlock.tone}
          title_ar={insightBlock.title_ar}
          title_en={insightBlock.title_en}
          body_ar={insightBlock.body_ar}
          body_en={insightBlock.body_en}
        />

        {alerts.length > 0 && (
          <div
            className="rounded-[var(--radius-lg)] border p-4 flex items-start gap-3"
            style={
              hasCriticalAlerts
                ? {
                    borderColor: 'var(--color-alert-critical-border)',
                    background: 'var(--color-alert-critical-bg)',
                  }
                : {
                    borderColor: 'var(--color-alert-attention-border)',
                    background: 'var(--color-alert-attention-bg)',
                  }
            }
          >
            <AlertTriangle
              className="h-5 w-5 shrink-0 mt-0.5"
              style={{ color: hasCriticalAlerts ? 'var(--color-alert-critical-muted)' : 'var(--color-alert-attention-muted)' }}
            />
            <div>
              <p
                className="font-semibold text-sm"
                style={{ color: hasCriticalAlerts ? 'var(--color-alert-critical-text)' : 'var(--color-alert-attention-text)' }}
              >
                {alerts.length}{' '}
                {hasCriticalAlerts
                  ? isAr
                    ? 'تنبيه حرج'
                    : 'critical alert(s)'
                  : isAr
                    ? 'تنبيه يتطلب انتباهك'
                    : 'alerts require attention'}
              </p>
              <p
                className="text-xs mt-0.5"
                style={{ color: hasCriticalAlerts ? 'var(--color-alert-critical-muted)' : 'var(--color-alert-attention-muted)' }}
              >
                {alerts[0]?.[isAr ? 'title_ar' : 'title_en']}
              </p>
            </div>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] sm:grid-cols-2 md:grid-cols-4">
          <KpiCard
            kpiId="performance"
            focused={focusKpi === 'performance'}
            countUp
            countDecimals={0}
            title_ar="درجة الأداء"
            title_en="Performance Score"
            value={myKpis.performance_score}
            unit="/100"
            subtitle={isAr ? `ترتيبك: #${marketRank} بين السلاسل` : `Rank: #${marketRank} among chains`}
            color="var(--color-interactive-pressed)"
            icon={<Target className="h-5 w-5" />}
            lang={lang}
          />
          <KpiCard
            kpiId="competitive"
            focused={focusKpi === 'competitive'}
            countUp
            countDecimals={0}
            title_ar="نسبة الأسعار التنافسية"
            title_en="Competitive Price Share"
            value={myKpis.competitive_index}
            unit="%"
            subtitle={isAr ? 'نسبة المنتجات ضمن نطاق السعر التنافسي' : '% products priced competitively'}
            color="var(--color-interactive)"
            icon={<TrendingUp className="h-5 w-5" />}
            lang={lang}
          />
          <KpiCard
            kpiId="pricing"
            focused={focusKpi === 'pricing'}
            countUp
            countDecimals={0}
            title_ar="مؤشر السعر مقابل السوق"
            title_en="Pricing Index"
            value={myKpis.pricing_index}
            unit="%"
            subtitle={piLabel.label}
            color={piLabel.color}
            icon={<TrendingDown className="h-5 w-5" />}
            lang={lang}
          />
          <KpiCard
            kpiId="coverage"
            focused={focusKpi === 'coverage'}
            countUp
            countDecimals={0}
            title_ar="تغطية المنتجات (مقارنة بالسوق)"
            title_en="Product Coverage (vs Market)"
            value={myKpis.coverage_index}
            unit="%"
            subtitle={`${myKpis.covered_products} / ${myKpis.total_products} ${isAr ? 'منتج' : 'products'}`}
            color={fareeqHex.amber}
            icon={<CheckCircle className="h-5 w-5" />}
            lang={lang}
          />
        </div>

        {/* Secondary KPI Cards */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] sm:grid-cols-2 md:grid-cols-4">
          <Card elevation="nested">
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{isAr ? 'متوسط سعرك' : 'Your Avg Price'}</p>
            <p className="text-xl font-bold mt-1 tabular-nums" style={{ color: 'var(--color-text-primary)' }}>
              {myKpis.avg_price.toFixed(2)}{' '}
              <span className="text-sm font-medium" style={{ color: 'var(--color-text-subtle)' }}>
                {isAr ? 'ريال' : 'SAR'}
              </span>
            </p>
          </Card>
          <Card elevation="nested">
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{isAr ? 'متوسط السوق' : 'Market Avg Price'}</p>
            <p className="text-xl font-bold mt-1 tabular-nums" style={{ color: 'var(--color-text-primary)' }}>
              {myKpis.market_avg_price.toFixed(2)}{' '}
              <span className="text-sm font-medium" style={{ color: 'var(--color-text-subtle)' }}>
                {isAr ? 'ريال' : 'SAR'}
              </span>
            </p>
          </Card>
          <Card elevation="nested">
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{isAr ? 'منتجات أعلى من المنافسين' : 'Higher Than Competitors'}</p>
            <p className="text-xl font-bold mt-1 tabular-nums" style={{ color: 'var(--color-trend-down)' }}>{myKpis.overpriced_count}</p>
          </Card>
          <Card elevation="nested">
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{isAr ? 'منتجات ضمن الأرخص' : 'Among the Cheapest'}</p>
            <p className="text-xl font-bold mt-1 tabular-nums" style={{ color: 'var(--color-trend-up)' }}>{myKpis.cheapest_count}</p>
          </Card>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'مقارنة متوسط الأسعار' : 'Avg Price Comparison'}</CardTitle>
            </CardHeader>
            <CardContent>
              {marketChartData.length === 0 ? (
                <EmptyState
                  title={isAr ? 'لا بيانات سوق للمقارنة' : 'No market data to compare'}
                  description={isAr ? 'غيّر مصدر البيانات أو حدّث لاحقاً.' : 'Try another data source or refresh.'}
                  action={
                    <Button variant="outline" size="sm" onClick={() => forceRefresh()}>
                      {isAr ? 'تحديث' : 'Refresh'}
                    </Button>
                  }
                />
              ) : (
                <ChartReveal>
                  <SimpleBarChart
                    data={marketChartData}
                    dataKey={isAr ? 'متوسط السعر' : 'Avg Price'}
                    colors={market.map(m => m.retailer.color)}
                    unit=" SAR"
                    height={220}
                  />
                </ChartReveal>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'توزيع التسعير' : 'Pricing Distribution'}</CardTitle>
            </CardHeader>
            <CardContent>
              {pieData.length === 0 ? (
                <EmptyState
                  title={isAr ? 'لا توجد فئات تسعير بعد' : 'No pricing buckets yet'}
                  description={isAr ? 'أضف منتجات أو راجع التغطية.' : 'Add products or review coverage.'}
                  action={
                    <Link
                      href="/products"
                      className="inline-flex items-center rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors"
                      style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-primary)' }}
                    >
                      {isAr ? 'المنتجات' : 'Products'}
                    </Link>
                  }
                />
              ) : (
                <ChartReveal>
                  <SimplePieChart data={pieData} height={220} />
                </ChartReveal>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-3">
          <div className="md:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>{isAr ? 'أداء الأصناف الرئيسية' : 'Top Category Performance'}</CardTitle>
                <p className="text-xs mt-1" style={{ color: 'var(--color-text-subtle)' }}>
                  {prevSnapshot
                    ? isAr
                      ? 'الخط المنقط يقدّر مؤشر السعر حسب آخر مزامنة محفوظة على هذا الجهاز.'
                      : 'Dashed line estimates price index from the last saved sync on this device.'
                    : isAr
                      ? 'بعد مزامنتين أو أكثر سيظهر خط المقارنة تلقائياً.'
                      : 'After two or more syncs, the comparison line appears automatically.'}
                </p>
              </CardHeader>
              <CardContent>
                {catChartData.length === 0 ? (
                  <EmptyState
                    title={isAr ? 'لا أصناف لعرضها' : 'No categories to show'}
                    description={isAr ? 'غيّر المرشحات أو راجع التغطية.' : 'Adjust filters or review coverage.'}
                  action={
                    <Link
                      href="/categories"
                      className="inline-flex items-center rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors"
                      style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-primary)' }}
                    >
                      {isAr ? 'الأصناف' : 'Categories'}
                    </Link>
                  }
                  />
                ) : (
                  <ChartReveal>
                    <CategoryPerformanceComboChart
                      data={catChartData}
                      productsKey={productsKey}
                      priceKey={priceKey}
                      pricePrevKey={pricePrevKey}
                      productsLabel={isAr ? 'المنتجات' : 'Products'}
                      priceLabel={priceKey}
                      prevLineLabel={pricePrevKey}
                      height={260}
                    />
                  </ChartReveal>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'تغطية السوق' : 'Market Coverage'}</CardTitle>
            </CardHeader>
            <CardContent>
              {coverageData.length === 0 ? (
                <EmptyState
                  className="py-6"
                  title={isAr ? 'لا بيانات تغطية' : 'No coverage data'}
                  description={isAr ? 'حدّث البيانات أو راجع المتاجر.' : 'Refresh or review retailers.'}
                />
              ) : (
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
              )}
            </CardContent>
          </Card>
        </div>

        {/* AI Recommendations */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                <CardTitle>{isAr ? 'توصيات مبنية على البيانات — أهم الإجراءات' : 'Data-driven recommendations — top actions'}</CardTitle>
              </div>
              <Link
                href="/recommendations"
                className="text-xs font-semibold hover:underline"
                style={{ color: 'var(--color-interactive)' }}
              >
                {isAr ? 'عرض الكل ←' : '→ View All'}
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {recommendations.length === 0 ? (
              <EmptyState
                title={isAr ? 'لا توصيات بعد' : 'No recommendations yet'}
                description={isAr ? 'راجع التنبيهات أو المنتجات لإنتاج إجراءات.' : 'Review alerts or products to surface actions.'}
                action={
                  <Link
                    href="/recommendations"
                    className="inline-flex items-center rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors"
                    style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-primary)' }}
                  >
                    {isAr ? 'مركز التوصيات' : 'Recommendations'}
                  </Link>
                }
              />
            ) : (
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
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function DashboardPageFallback() {
  const t = PAGE_TITLES['/dashboard']
  return (
    <div>
      <Topbar
        title_ar={t.ar}
        title_en={t.en}
        description_ar="ملخص تنفيذي لأداء السلسلة مقارنة بالسوق."
        description_en="Executive view of your chain’s performance vs the market."
      />
      <div className="page-shell">
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] sm:grid-cols-2 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <KpiCardSkeleton key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-2">
          <ChartCardSkeleton height={220} />
          <ChartCardSkeleton height={220} />
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardPageFallback />}>
      <DashboardPageInner />
    </Suspense>
  )
}
