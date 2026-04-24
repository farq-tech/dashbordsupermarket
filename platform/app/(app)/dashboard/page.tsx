'use client'
import React, { Suspense, useEffect, useMemo } from 'react'
import { useSearchParams } from 'next/navigation'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { KpiCard } from '@/components/ui/kpi-card'
import { InsightCard } from '@/components/ui/insight-card'
import { Badge } from '@/components/ui/badge'
import { SimpleBarChart, CategoryPerformanceComboChart } from '@/components/charts/BarChartComponent'
import { SimplePieChart } from '@/components/charts/PieChartComponent'
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Lightbulb, Target, Trophy } from 'lucide-react'
import Link from 'next/link'
import { PAGE_TITLES } from '@/lib/navConfig'
import { getPreviousSnapshot, getKpiSnapshots, type KpiSnapshot } from '@/lib/kpiSnapshotHistory'
import { ChartReveal } from '@/components/ui/chart-reveal'
import { EmptyState } from '@/components/ui/empty-state'
import { ChartCardSkeleton, KpiCardSkeleton } from '@/components/ui/skeleton'
import { ErrorState } from '@/components/ui/error-state'
import { Button } from '@/components/ui/button'
import { fareeqChart, fareeqHex } from '@/lib/design-system'
import { RetailerLogo } from '@/components/ui/RetailerLogo'
import { CustomerJourneyCard } from '@/components/layout/CustomerJourneyCard'

function Sparkline({ values, color }: { values: number[]; color: string }) {
  if (values.length < 2) {
    return <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>—</span>
  }
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const w = 60, h = 24, pad = 2
  const points = values.map((v, i) => {
    const x = pad + (i / (values.length - 1)) * (w - pad * 2)
    const y = h - pad - ((v - min) / range) * (h - pad * 2)
    return `${x},${y}`
  }).join(' ')
  const lastX = pad + ((values.length - 1) / (values.length - 1)) * (w - pad * 2)
  const lastY = h - pad - ((values[values.length - 1] - min) / range) * (h - pad * 2)
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={lastX} cy={lastY} r="2.5" fill={color} />
    </svg>
  )
}

function DashboardPageInner() {
  const searchParams = useSearchParams()
  const focusKpi = searchParams.get('kpi')
  const { lang, dashboardData, loading, error, selectedRetailer, fetchData, dataSource, forceRefresh } = useAppStore()

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

  // These useMemo hooks MUST be declared before any early returns (Rules of Hooks).
  const kpiTrendSnapshots = useMemo(() => {
    try {
      if (typeof window === 'undefined') return []
      return getKpiSnapshots()
        .filter(s => s.store_key === selectedRetailer?.store_key && s.source === dataSource)
        .slice(-5)
    } catch {
      return []
    }
  }, [selectedRetailer?.store_key, dataSource])

  const kpiTrendIndicators = useMemo(() => [
    {
      key: 'performance_score',
      label_ar: 'درجة الأداء',
      label_en: 'Performance Score',
      values: kpiTrendSnapshots.map(s => s.performance_score),
    },
    {
      key: 'competitive_index',
      label_ar: 'تنافسية %',
      label_en: 'Competitive %',
      values: kpiTrendSnapshots.map(s => s.competitive_index),
    },
    {
      key: 'pricing_index',
      label_ar: 'مؤشر السعر',
      label_en: 'Pricing Index',
      values: kpiTrendSnapshots.map(s => s.pricing_index),
    },
    {
      key: 'coverage_index',
      label_ar: 'تغطية %',
      label_en: 'Coverage %',
      values: kpiTrendSnapshots.map(s => s.coverage_index),
    },
  ], [kpiTrendSnapshots])

  const dashTopbar = (
    <Topbar
      title_ar={PAGE_TITLES['/dashboard'].ar}
      title_en={PAGE_TITLES['/dashboard'].en}
      description_ar="ملخص تنفيذي لأداء السلسلة مقارنة بالسوق."
      description_en="Executive view of your chain's performance vs the market."
    />
  )

  if (!loading && error && !dashboardData) {
    return (
      <div>
        {dashTopbar}
        <div className="page-shell"><ErrorState lang={lang} onRetry={forceRefresh} /></div>
      </div>
    )
  }

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

  const { kpis, recommendations, alerts, market, all_kpis, decision_brief } = dashboardData
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
    prevSnapshot && kpis.pricing_index > 0
      ? Math.min(2, Math.max(0.5, prevSnapshot.pricing_index / kpis.pricing_index))
      : 1

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
  const _rankIdx = [...all_kpis].sort((a, b) => b.performance_score - a.performance_score)
    .findIndex(k => k.retailer.store_key === selectedRetailer?.store_key)
  const marketRank = _rankIdx === -1 ? null : _rankIdx + 1

  // Prefer authoritative server-computed rank; fall back to client-side derivation
  const effectiveRank = decision_brief?.market_rank ?? marketRank
  const effectiveParticipants = decision_brief?.market_participants ?? all_kpis.length

  const rankContextLine =
    effectiveRank == null
      ? ''
      : effectiveRank === 1
        ? (isAr ? 'أنت الأفضل أداءً في السوق 🎯' : 'You lead the market 🎯')
        : effectiveRank <= 3
          ? (isAr ? 'قريب من القمة — ركّز على التسعير' : 'Close to the top — focus on pricing')
          : (isAr ? 'فرصة للارتقاء — راجع التوصيات' : 'Opportunity to climb — review recommendations')

  const rankBadgeStyle: React.CSSProperties =
    effectiveRank === 1
      ? { background: 'linear-gradient(135deg, #fef9c3, #fde68a)', color: '#854d0e' }
      : effectiveRank != null && effectiveRank <= 3
        ? { background: 'var(--color-surface-muted)', color: 'var(--color-text-primary)' }
        : { background: 'var(--color-surface-muted)', color: 'var(--color-text-secondary)' }

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

        <CustomerJourneyCard lang={lang} dataSource={dataSource} />

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
            subtitle={marketRank != null
              ? (isAr ? `ترتيبك: #${marketRank} بين السلاسل` : `Rank: #${marketRank} among chains`)
              : (isAr ? 'الترتيب: غير متوفر' : 'Rank: —')
            }
            color="var(--color-interactive-pressed)"
            icon={<Target className="h-5 w-5" />}
            lang={lang}
            tooltip_ar="مؤشر مركّب يجمع التنافسية والتسعير والتغطية، يُحتسب من متوسط مرجّح للمؤشرات الثلاثة. 100 = أفضل أداء ممكن."
            tooltip_en="Composite index combining competitive pricing, pricing index, and coverage. Weighted average of three sub-scores. 100 = best possible."
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
            tooltip_ar="نسبة المنتجات التي سعرها لا يتجاوز السعر الأدنى في السوق بأكثر من 5%. المصدر: بيانات مقارنة المنتجات الداخلية."
            tooltip_en="% of your products priced within 5% of the market's lowest price. Source: internal product comparison data."
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
            tooltip_ar="متوسط سعرك مقارنةً بمتوسط السوق. 100% = مساوٍ للسوق. أقل من 100% = أرخص. أُحتسب من متوسط الفجوة السعرية لجميع المنتجات المتوفرة."
            tooltip_en="Your average price relative to market average. 100% = at market. Below 100% = cheaper. Calculated from average price gap across all stocked products."
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
            tooltip_ar="نسبة المنتجات الموجودة في السوق والمتوفرة في سلسلتك. المصدر: مقارنة كتالوج السوق بكتالوجك الخاص."
            tooltip_en="% of market-listed products that are present in your chain's catalog. Source: comparison of market catalog vs your own product list."
          />
        </div>

        {/* KPI Trend Strip */}
        {kpiTrendSnapshots.length >= 2 && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle className="text-sm">
                {isAr
                  ? 'اتجاه الأداء (آخر 5 جلسات)'
                  : 'Performance Trend (Last 5 Sessions)'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {kpiTrendIndicators.map(ind => {
                  const { values } = ind
                  const hasData = values.length >= 2
                  const first = values[0] ?? 0
                  const last = values[values.length - 1] ?? 0
                  const delta = last - first
                  const trendColor = !hasData
                    ? 'var(--color-text-muted)'
                    : delta > 0
                      ? 'var(--color-trend-up)'
                      : delta < 0
                        ? 'var(--color-trend-down)'
                        : 'var(--color-text-muted)'
                  return (
                    <div key={ind.key} className="flex flex-col gap-1.5 p-2 rounded-lg" style={{ background: 'var(--color-surface-muted)' }}>
                      <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                        {isAr ? ind.label_ar : ind.label_en}
                      </p>
                      {hasData ? (
                        <>
                          <Sparkline values={values} color={trendColor} />
                          <p className="text-xs font-semibold tabular-nums" style={{ color: trendColor }}>
                            {delta >= 0 ? '+' : ''}{delta.toFixed(1)}
                          </p>
                        </>
                      ) : (
                        <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                          {isAr ? 'لا يوجد تاريخ' : 'No history'}
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Secondary KPI Cards */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          {/* Market Rank — prominent badge */}
          <Card elevation="nested" className="flex flex-col">
            <div className="flex items-center gap-1.5 mb-1">
              <Trophy
                className="h-3.5 w-3.5 shrink-0"
                style={{ color: effectiveRank === 1 ? '#854d0e' : 'var(--color-text-muted)' }}
              />
              <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                {isAr ? 'ترتيبك في السوق' : 'Your Market Rank'}
              </p>
            </div>
            {effectiveRank != null ? (
              <div
                className="mt-1 inline-flex items-center justify-center rounded-xl px-3 py-1 font-extrabold text-2xl tabular-nums self-start"
                style={rankBadgeStyle}
              >
                #{effectiveRank}
              </div>
            ) : (
              <p className="text-2xl font-bold mt-1" style={{ color: 'var(--color-text-muted)' }}>—</p>
            )}
            <p className="text-[11px] mt-1.5" style={{ color: 'var(--color-text-subtle)' }}>
              {effectiveRank != null
                ? (isAr ? `من أصل ${effectiveParticipants} متنافسين` : `out of ${effectiveParticipants} chains`)
                : (isAr ? 'لا يوجد ترتيب' : 'No rank data')}
            </p>
            {rankContextLine && (
              <p
                className="text-[11px] mt-1 leading-snug"
                style={{ color: effectiveRank === 1 ? '#854d0e' : 'var(--color-text-muted)' }}
              >
                {rankContextLine}
              </p>
            )}
          </Card>
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

        {/* Market SKU & Cheapest % Stats */}
        {market.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>
                {isAr ? 'إحصائيات السوق — التشكيلة ونسبة الأرخص' : 'Market Stats — Assortment & Cheapest %'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
                {market.map((m) => {
                  const cheapestColor =
                    m.cheapest_pct >= 40
                      ? 'var(--color-trend-up)'
                      : m.cheapest_pct >= 20
                      ? fareeqHex.amber
                      : fareeqChart.coral
                  return (
                    <div
                      key={m.retailer.store_key}
                      className="rounded-xl border p-3 flex flex-col gap-2"
                      style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface-muted)' }}
                    >
                      <div className="flex items-center gap-2">
                        <RetailerLogo
                          retailer={m.retailer}
                          label={isAr ? m.retailer.brand_ar : m.retailer.brand_en}
                          size={32}
                          rounded="lg"
                        />
                        <p className="text-xs font-semibold text-[var(--color-text-primary)] truncate">
                          {isAr ? m.retailer.brand_ar : m.retailer.brand_en}
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-[var(--color-text-muted)]">
                          {isAr ? 'عدد المنتجات / SKU Count' : 'SKU Count / عدد المنتجات'}
                        </p>
                        <p className="text-lg font-bold tabular-nums" style={{ color: 'var(--color-text-primary)' }}>
                          {m.products.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-[var(--color-text-muted)]">
                          {isAr ? 'الأرخص % / Cheapest %' : 'Cheapest % / الأرخص %'}
                        </p>
                        <span
                          className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold tabular-nums"
                          style={{
                            backgroundColor: `${cheapestColor}20`,
                            color: cheapestColor,
                            border: `1px solid ${cheapestColor}40`,
                          }}
                        >
                          {m.cheapest_pct.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        )}

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
                  <>
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
                    <p className="text-[11px] mt-1" style={{ color: 'var(--color-text-muted)' }}>
                      {isAr
                        ? 'المحور الأيسر: عدد المنتجات — المحور الأيمن: مؤشر التسعير (%) — الخط المتقطع: تقدير الفترة السابقة.'
                        : 'Left axis: product count — Right axis: pricing index (%) — dashed line: prior period estimate.'}
                    </p>
                  </>
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
