'use client'
import { useState, useMemo } from 'react'
import { fareeqChart, fareeqHex } from '@/lib/design-system'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { LoadingOverlay } from '@/components/ui/spinner'
import { ErrorState } from '@/components/ui/error-state'
import { MultiBarChart, HorizontalBarChart } from '@/components/charts/BarChartComponent'
import { RetailerLogo } from '@/components/ui/RetailerLogo'

const escCsv = (v: unknown) => {
  const s = String(v ?? '')
  return s.includes(',') || s.includes('"') || s.includes('\n') ? `"${s.replace(/"/g, '""')}"` : s
}

export default function CompetitorsPage() {
  const { lang, dashboardData, loading, error, forceRefresh, selectedRetailer } = useAppStore()
  const isAr = lang === 'ar'

  const [selectedCompetitorKey, setSelectedCompetitorKey] = useState<number | null>(null)
  const [tablePage, setTablePage] = useState(0)

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
    { dataKey: isAr ? 'نقاط الأداء' : 'Performance', name: isAr ? 'الأداء' : 'Performance', color: fareeqChart.blue },
    { dataKey: isAr ? 'مؤشر التنافسية' : 'Competitive Index', name: isAr ? 'التنافسية' : 'Competitive', color: fareeqChart.green },
    { dataKey: isAr ? 'التغطية %' : 'Coverage %', name: isAr ? 'التغطية' : 'Coverage', color: fareeqHex.amber },
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

  // ── Head-to-Head Deep Dive ──────────────────────────────────────────────────

  const selectedCompetitor = competitors.find(c => c.retailer.store_key === selectedCompetitorKey) ?? null

  // All SKUs both carry
  const sharedSKUs = useMemo(() => {
    if (!selectedCompetitorKey) return []
    return comparisons.filter(c =>
      c.your_price !== null &&
      c.prices_by_store[selectedCompetitorKey] !== undefined
    )
  }, [comparisons, selectedCompetitorKey])

  // SKUs unique to me (I carry, they don't)
  const uniqueToMe = useMemo(() => {
    if (!selectedCompetitorKey) return 0
    return comparisons.filter(c =>
      c.your_price !== null &&
      c.prices_by_store[selectedCompetitorKey] === undefined
    ).length
  }, [comparisons, selectedCompetitorKey])

  // SKUs unique to competitor (they carry, I don't)
  const uniqueToComp = useMemo(() => {
    if (!selectedCompetitorKey) return 0
    return comparisons.filter(c =>
      c.your_price === null &&
      c.prices_by_store[selectedCompetitorKey] !== undefined
    ).length
  }, [comparisons, selectedCompetitorKey])

  // Enriched shared SKUs with gap info — sorted by |gap| desc
  const enrichedSKUs = useMemo(() => {
    if (!selectedCompetitorKey) return []
    return sharedSKUs
      .map(c => {
        const myPrice = c.your_price as number
        const compPrice = c.prices_by_store[selectedCompetitorKey]
        const gapPct = ((myPrice - compPrice) / compPrice) * 100
        const absGap = Math.abs(gapPct)
        let winner: 'me' | 'them' | 'tied'
        if (absGap <= 0.5) winner = 'tied'
        else if (myPrice <= compPrice) winner = 'me'
        else winner = 'them'
        return { ...c, myPrice, compPrice, gapPct: Math.round(gapPct * 10) / 10, absGap, winner }
      })
      .sort((a, b) => b.absGap - a.absGap)
      .slice(0, 100)
  }, [sharedSKUs, selectedCompetitorKey])

  const myOverallWinRate = useMemo(() => {
    if (!enrichedSKUs.length) return 0
    const wins = enrichedSKUs.filter(s => s.winner === 'me' || s.winner === 'tied').length
    return Math.round((wins / enrichedSKUs.length) * 100)
  }, [enrichedSKUs])

  // Category scorecard
  const categoryScorecard = useMemo(() => {
    if (!enrichedSKUs.length) return []
    const catMap = new Map<string, { name_ar: string; name_en: string; iWin: number; theyWin: number; tied: number }>()
    enrichedSKUs.forEach(s => {
      if (!catMap.has(s.category_en)) {
        catMap.set(s.category_en, { name_ar: s.category_ar, name_en: s.category_en, iWin: 0, theyWin: 0, tied: 0 })
      }
      const entry = catMap.get(s.category_en)!
      if (s.winner === 'me') entry.iWin++
      else if (s.winner === 'them') entry.theyWin++
      else entry.tied++
    })
    return Array.from(catMap.values())
      .map(c => {
        const total = c.iWin + c.theyWin + c.tied
        const winRate = total > 0 ? Math.round(((c.iWin + c.tied * 0.5) / total) * 100) : 0
        return { ...c, total, winRate }
      })
      .sort((a, b) => b.total - a.total)
      .slice(0, 8)
  }, [enrichedSKUs])

  // Market basket (top 30 by availability_pct)
  const basketData = useMemo(() => {
    if (!selectedCompetitorKey || !sharedSKUs.length) return null
    const top30 = [...sharedSKUs]
      .sort((a, b) => b.availability_pct - a.availability_pct)
      .slice(0, 30)
    const myTotal = top30.reduce((sum, c) => sum + (c.your_price as number), 0)
    const compTotal = top30.reduce((sum, c) => sum + c.prices_by_store[selectedCompetitorKey], 0)
    const diffSar = myTotal - compTotal
    const diffPct = compTotal > 0 ? ((myTotal - compTotal) / compTotal) * 100 : 0
    const cheaper: 'me' | 'them' | 'tied' = Math.abs(diffPct) <= 0.5 ? 'tied' : diffSar < 0 ? 'me' : 'them'
    return { count: top30.length, myTotal, compTotal, diffSar, diffPct: Math.round(diffPct * 10) / 10, cheaper }
  }, [sharedSKUs, selectedCompetitorKey])

  // Pagination
  const PAGE_SIZE = 50
  const totalPages = Math.ceil(enrichedSKUs.length / PAGE_SIZE)
  const pagedSKUs = enrichedSKUs.slice(tablePage * PAGE_SIZE, (tablePage + 1) * PAGE_SIZE)

  // CSV export
  const handleExportCsv = () => {
    if (!enrichedSKUs.length || !selectedCompetitor) return
    const compName = isAr ? selectedCompetitor.retailer.brand_ar : selectedCompetitor.retailer.brand_en
    const headers = isAr
      ? ['اسم المنتج', 'الفئة', 'سعري (ريال)', `سعر ${compName} (ريال)`, 'الفجوة %', 'النتيجة']
      : ['Product', 'Category', 'My Price (SAR)', `${compName} Price (SAR)`, 'Gap %', 'Result']
    const winnerLabel = (w: 'me' | 'them' | 'tied') => {
      if (w === 'me') return isAr ? 'أنا الأرخص' : 'I Win'
      if (w === 'them') return isAr ? 'المنافس أرخص' : 'They Win'
      return isAr ? 'متساوٍ' : 'Tied'
    }
    const rows = enrichedSKUs.map(s => [
      escCsv(isAr ? s.title_ar : s.title_en),
      escCsv(isAr ? s.category_ar : s.category_en),
      escCsv(s.myPrice.toFixed(2)),
      escCsv(s.compPrice.toFixed(2)),
      escCsv(s.gapPct.toFixed(1)),
      escCsv(winnerLabel(s.winner)),
    ])
    const csv = '\uFEFF' + [headers.map(escCsv).join(','), ...rows.map(r => r.join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `head-to-head-${compName}-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (!loading && error && !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/competitors'].ar} title_en={PAGE_TITLES['/competitors'].en} /><div className="page-shell"><ErrorState lang={lang} onRetry={forceRefresh} /></div></div>
  }

  if (loading || !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/competitors'].ar} title_en={PAGE_TITLES['/competitors'].en} /><LoadingOverlay lang={lang} /></div>
  }

  return (
    <div className="animate-fade-in">
      <Topbar title_ar={PAGE_TITLES['/competitors'].ar} title_en={PAGE_TITLES['/competitors'].en} />
      <div className="page-shell">

        {/* Competitor Cards */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-2">
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
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'تموضع الأسعار في السوق' : 'Market Price Positioning'}</CardTitle>
              <p className="text-xs text-neutral-400 mt-0.5">{isAr ? 'متوسط سعر كل سلسلة (ريال) — كلما كان الشريط أقصر = أرخص' : 'Average price per chain (SAR) — shorter bar = cheaper'}</p>
            </CardHeader>
            <CardContent>
              <HorizontalBarChart
                data={pricePie.map(p => ({ name: p.name, [isAr ? 'متوسط السعر' : 'Avg Price']: p.value, _color: p.color }))}
                dataKey={isAr ? 'متوسط السعر' : 'Avg Price'}
                colors={pricePie.map(p => p.color)}
                unit=" SAR"
                height={Math.max(180, pricePie.length * 40)}
              />
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

        {/* ── Head-to-Head Deep Dive ─────────────────────────────────────────── */}
        <div className="animate-fade-in">
          {/* Section header */}
          <div className="flex items-center gap-3 mb-4">
            <div className="h-px flex-1 bg-[var(--color-border)]" />
            <h2 className="text-base font-bold text-[var(--color-text-primary)] whitespace-nowrap px-2">
              {isAr ? 'تحليل تفصيلي مقارن' : 'Head-to-Head Analysis'}
            </h2>
            <div className="h-px flex-1 bg-[var(--color-border)]" />
          </div>

          {/* Competitor selector buttons */}
          <div className="flex flex-wrap gap-2 mb-6">
            {competitors.map(comp => {
              const isSelected = comp.retailer.store_key === selectedCompetitorKey
              return (
                <button
                  key={comp.retailer.store_key}
                  onClick={() => {
                    setSelectedCompetitorKey(isSelected ? null : comp.retailer.store_key)
                    setTablePage(0)
                  }}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border transition-all cursor-pointer"
                  style={{
                    borderColor: isSelected ? comp.retailer.color : 'var(--color-border)',
                    backgroundColor: isSelected ? `${comp.retailer.color}15` : 'var(--color-surface-muted)',
                    color: isSelected ? comp.retailer.color : 'var(--color-text-primary)',
                    boxShadow: isSelected ? `0 0 0 2px ${comp.retailer.color}40` : undefined,
                  }}
                >
                  <RetailerLogo retailer={comp.retailer} label="" size={22} rounded="md" />
                  <span>{isAr ? comp.retailer.brand_ar : comp.retailer.brand_en}</span>
                </button>
              )
            })}
          </div>

          {!selectedCompetitor ? (
            <Card>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-12 gap-3 text-center">
                  <span className="text-4xl">🔍</span>
                  <p className="text-[var(--color-text-primary)] font-semibold text-base">
                    {isAr ? 'اختر منافساً للمقارنة التفصيلية' : 'Select a competitor for detailed analysis'}
                  </p>
                  <p className="text-sm text-[var(--color-text-muted)]">
                    {isAr
                      ? 'انقر على أحد أسماء المنافسين أعلاه لعرض مقارنة SKU شاملة'
                      : 'Click a competitor above to view a full SKU-level comparison'}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {/* ── Overlap Summary Strip ── */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  {
                    label: isAr ? 'المنتجات المشتركة' : 'Shared SKUs',
                    value: sharedSKUs.length,
                    sub: isAr ? 'كلانا يحمله' : 'Both carry',
                    color: 'var(--color-interactive)',
                  },
                  {
                    label: isAr ? 'حصري عندي' : 'Only at Mine',
                    value: uniqueToMe,
                    sub: isAr ? 'لا يحمله المنافس' : 'Competitor lacks',
                    color: fareeqChart.green,
                  },
                  {
                    label: isAr ? 'حصري عند المنافس' : 'Only at Theirs',
                    value: uniqueToComp,
                    sub: isAr ? 'أفتقده في تشكيلتي' : 'Missing from my range',
                    color: fareeqChart.coral,
                  },
                  {
                    label: isAr ? 'معدل فوزي' : 'My Win Rate',
                    value: `${myOverallWinRate}%`,
                    sub: isAr ? 'على المنتجات المشتركة' : 'on shared SKUs',
                    color: myOverallWinRate >= 55 ? fareeqChart.green : myOverallWinRate < 45 ? fareeqChart.coral : 'var(--color-interactive)',
                  },
                ].map((stat, i) => (
                  <Card key={i}>
                    <div className="p-4">
                      <p className="text-xs text-[var(--color-text-muted)] mb-1">{stat.label}</p>
                      <p className="text-2xl font-bold tabular-nums" style={{ color: stat.color }}>{stat.value}</p>
                      <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">{stat.sub}</p>
                    </div>
                  </Card>
                ))}
              </div>

              {/* ── Category Win/Loss Scorecard + Basket ── */}
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
                {/* Category scorecard — 2/3 width */}
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>
                      {isAr ? 'بطاقة أداء الفئات' : 'Category Win/Loss Scorecard'}
                    </CardTitle>
                    <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                      {isAr
                        ? `مقارنة مع ${isAr ? selectedCompetitor.retailer.brand_ar : selectedCompetitor.retailer.brand_en}`
                        : `vs ${selectedCompetitor.retailer.brand_en}`}
                    </p>
                  </CardHeader>
                  <CardContent>
                    {categoryScorecard.length === 0 ? (
                      <p className="text-sm text-[var(--color-text-muted)] py-4 text-center">
                        {isAr ? 'لا توجد بيانات' : 'No data'}
                      </p>
                    ) : (
                      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                        {categoryScorecard.map((cat, i) => {
                          const isGreen = cat.winRate > 55
                          const isRed = cat.winRate < 45
                          const bgColor = isGreen
                            ? 'rgba(22,163,74,0.08)'
                            : isRed
                            ? 'rgba(239,131,84,0.08)'
                            : 'var(--color-surface-muted)'
                          const accentColor = isGreen ? fareeqChart.green : isRed ? fareeqChart.coral : 'var(--color-text-secondary)'
                          return (
                            <div
                              key={i}
                              className="rounded-xl p-3 flex flex-col gap-1"
                              style={{ backgroundColor: bgColor, border: `1px solid ${isGreen ? 'rgba(22,163,74,0.2)' : isRed ? 'rgba(239,131,84,0.2)' : 'var(--color-border)'}` }}
                            >
                              <p className="text-xs font-medium text-[var(--color-text-primary)] truncate leading-tight">
                                {isAr ? cat.name_ar : cat.name_en}
                              </p>
                              <p className="text-xl font-bold tabular-nums" style={{ color: accentColor }}>
                                {cat.winRate}%
                              </p>
                              <div className="flex gap-2 text-xs text-[var(--color-text-muted)]">
                                <span className="text-[#16a34a] font-semibold">{cat.iWin}✓</span>
                                <span className="text-[#ef8354] font-semibold">{cat.theyWin}✗</span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Basket comparison — 1/3 width */}
                <Card>
                  <CardHeader>
                    <CardTitle>{isAr ? 'سلة السوق (30 منتج)' : 'Market Basket (30 SKUs)'}</CardTitle>
                    <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                      {isAr ? 'أعلى 30 منتجاً حسب التوافر' : 'Top 30 SKUs by availability'}
                    </p>
                  </CardHeader>
                  <CardContent>
                    {!basketData ? (
                      <p className="text-sm text-[var(--color-text-muted)] py-4 text-center">
                        {isAr ? 'لا توجد بيانات كافية' : 'Not enough data'}
                      </p>
                    ) : (
                      <div className="space-y-3">
                        <div className="flex justify-between items-end">
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">
                              {isAr ? 'إجمالي سلتي' : 'My basket total'}
                            </p>
                            <p className="text-xl font-bold tabular-nums text-[var(--color-text-primary)]">
                              {basketData.myTotal.toFixed(1)} <span className="text-sm font-normal text-[var(--color-text-muted)]">SAR</span>
                            </p>
                          </div>
                          <div className="text-end">
                            <p className="text-xs text-[var(--color-text-muted)]">
                              {isAr
                                ? `إجمالي ${selectedCompetitor.retailer.brand_ar}`
                                : `${selectedCompetitor.retailer.brand_en} total`}
                            </p>
                            <p className="text-xl font-bold tabular-nums" style={{ color: selectedCompetitor.retailer.color }}>
                              {basketData.compTotal.toFixed(1)} <span className="text-sm font-normal text-[var(--color-text-muted)]">SAR</span>
                            </p>
                          </div>
                        </div>

                        <div
                          className="rounded-xl p-3 text-center"
                          style={{
                            backgroundColor: basketData.cheaper === 'me'
                              ? 'rgba(22,163,74,0.1)'
                              : basketData.cheaper === 'them'
                              ? 'rgba(239,131,84,0.1)'
                              : 'var(--color-surface-muted)',
                            borderWidth: 1,
                            borderStyle: 'solid',
                            borderColor: basketData.cheaper === 'me'
                              ? 'rgba(22,163,74,0.3)'
                              : basketData.cheaper === 'them'
                              ? 'rgba(239,131,84,0.3)'
                              : 'var(--color-border)',
                          }}
                        >
                          <p className="text-xs text-[var(--color-text-muted)] mb-1">
                            {isAr ? 'الفرق' : 'Difference'}
                          </p>
                          <p
                            className="text-lg font-bold tabular-nums"
                            style={{
                              color: basketData.cheaper === 'me'
                                ? fareeqChart.green
                                : basketData.cheaper === 'them'
                                ? fareeqChart.coral
                                : 'var(--color-text-secondary)',
                            }}
                          >
                            {Math.abs(basketData.diffSar).toFixed(1)} SAR ({Math.abs(basketData.diffPct).toFixed(1)}%)
                          </p>
                          <p className="text-xs font-semibold mt-1"
                            style={{
                              color: basketData.cheaper === 'me'
                                ? fareeqChart.green
                                : basketData.cheaper === 'them'
                                ? fareeqChart.coral
                                : 'var(--color-text-secondary)',
                            }}
                          >
                            {basketData.cheaper === 'me'
                              ? (isAr ? '✓ سلتي أرخص' : '✓ My basket is cheaper')
                              : basketData.cheaper === 'them'
                              ? (isAr ? `✗ سلة ${selectedCompetitor.retailer.brand_ar} أرخص` : `✗ ${selectedCompetitor.retailer.brand_en} is cheaper`)
                              : (isAr ? '≈ متقاربان' : '≈ About equal')}
                          </p>
                        </div>

                        <p className="text-xs text-[var(--color-text-muted)] text-center">
                          {isAr ? `${basketData.count} منتجاً مشتركاً` : `${basketData.count} shared products`}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* ── Head-to-Head Product Table ── */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <div>
                      <CardTitle>
                        {isAr
                          ? `مقارنة SKU مع ${selectedCompetitor.retailer.brand_ar}`
                          : `SKU Comparison vs ${selectedCompetitor.retailer.brand_en}`}
                      </CardTitle>
                      <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                        {isAr
                          ? `${enrichedSKUs.length} منتجاً مشتركاً · مرتب حسب الفجوة`
                          : `${enrichedSKUs.length} shared SKUs · sorted by gap`}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleExportCsv}
                      disabled={enrichedSKUs.length === 0}
                    >
                      ↓ {isAr ? 'تصدير CSV' : 'Export CSV'}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {enrichedSKUs.length === 0 ? (
                    <p className="text-sm text-[var(--color-text-muted)] py-8 text-center">
                      {isAr ? 'لا توجد منتجات مشتركة' : 'No shared SKUs found'}
                    </p>
                  ) : (
                    <>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-[var(--color-border)]">
                              <th className="py-2 px-3 text-start font-semibold text-[var(--color-text-secondary)] text-xs">
                                {isAr ? 'المنتج' : 'Product'}
                              </th>
                              <th className="py-2 px-3 text-start font-semibold text-[var(--color-text-secondary)] text-xs hidden sm:table-cell">
                                {isAr ? 'الفئة' : 'Category'}
                              </th>
                              <th className="py-2 px-3 text-end font-semibold text-[var(--color-text-secondary)] text-xs">
                                {isAr ? 'سعري' : 'My Price'}
                              </th>
                              <th className="py-2 px-3 text-end font-semibold text-xs" style={{ color: selectedCompetitor.retailer.color }}>
                                {isAr ? selectedCompetitor.retailer.brand_ar : selectedCompetitor.retailer.brand_en}
                              </th>
                              <th className="py-2 px-3 text-end font-semibold text-[var(--color-text-secondary)] text-xs hidden md:table-cell">
                                {isAr ? 'الفجوة %' : 'Gap %'}
                              </th>
                              <th className="py-2 px-3 text-center font-semibold text-[var(--color-text-secondary)] text-xs">
                                {isAr ? 'النتيجة' : 'Result'}
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {pagedSKUs.map((sku, idx) => (
                              <tr
                                key={sku.FID}
                                className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-surface-muted)] transition-colors"
                              >
                                <td className="py-2.5 px-3 text-start">
                                  <p className="font-medium text-[var(--color-text-primary)] truncate max-w-[200px]">
                                    {isAr ? sku.title_ar : sku.title_en}
                                  </p>
                                  <p className="text-xs text-[var(--color-text-muted)] sm:hidden truncate">
                                    {isAr ? sku.category_ar : sku.category_en}
                                  </p>
                                </td>
                                <td className="py-2.5 px-3 text-start text-[var(--color-text-secondary)] hidden sm:table-cell">
                                  <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--color-surface-muted)]">
                                    {isAr ? sku.category_ar : sku.category_en}
                                  </span>
                                </td>
                                <td className="py-2.5 px-3 text-end tabular-nums font-semibold text-[var(--color-text-primary)]">
                                  {sku.myPrice.toFixed(2)}
                                </td>
                                <td className="py-2.5 px-3 text-end tabular-nums font-semibold" style={{ color: selectedCompetitor.retailer.color }}>
                                  {sku.compPrice.toFixed(2)}
                                </td>
                                <td className="py-2.5 px-3 text-end tabular-nums hidden md:table-cell">
                                  <span
                                    className="text-xs font-semibold"
                                    style={{
                                      color: sku.gapPct < -0.5
                                        ? fareeqChart.green
                                        : sku.gapPct > 0.5
                                        ? fareeqChart.coral
                                        : 'var(--color-text-secondary)',
                                    }}
                                  >
                                    {sku.gapPct > 0 ? '+' : ''}{sku.gapPct.toFixed(1)}%
                                  </span>
                                </td>
                                <td className="py-2.5 px-3 text-center">
                                  {sku.winner === 'me' ? (
                                    <Badge variant="success">
                                      {isAr ? 'أنا الأرخص' : 'I Win'}
                                    </Badge>
                                  ) : sku.winner === 'them' ? (
                                    <Badge variant="danger">
                                      {isAr ? 'المنافس أرخص' : 'They Win'}
                                    </Badge>
                                  ) : (
                                    <Badge variant="neutral">
                                      {isAr ? 'متساوٍ' : 'Tied'}
                                    </Badge>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Pagination */}
                      {totalPages > 1 && (
                        <div className="flex items-center justify-between mt-4 pt-3 border-t border-[var(--color-border)]">
                          <p className="text-xs text-[var(--color-text-muted)]">
                            {isAr
                              ? `صفحة ${tablePage + 1} من ${totalPages}`
                              : `Page ${tablePage + 1} of ${totalPages}`}
                          </p>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setTablePage(p => Math.max(0, p - 1))}
                              disabled={tablePage === 0}
                            >
                              {isAr ? '→ السابق' : '← Prev'}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setTablePage(p => Math.min(totalPages - 1, p + 1))}
                              disabled={tablePage >= totalPages - 1}
                            >
                              {isAr ? '← التالي' : 'Next →'}
                            </Button>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
        {/* ── End Deep Dive ── */}

      </div>
    </div>
  )
}
