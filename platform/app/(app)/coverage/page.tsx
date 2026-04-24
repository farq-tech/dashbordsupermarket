'use client'

import { useEffect, useState, useMemo } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { getPageTopbarCopy } from '@/lib/experienceCopy'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { KpiCard } from '@/components/ui/kpi-card'
import { SimpleBarChart } from '@/components/charts/BarChartComponent'
import { SimplePieChart } from '@/components/charts/PieChartComponent'
import { ChartReveal } from '@/components/ui/chart-reveal'
import { EmptyState } from '@/components/ui/empty-state'
import { KpiCardSkeleton, ChartCardSkeleton } from '@/components/ui/skeleton'
import { Store, MapPin, Layers, ShieldCheck, ChevronDown, Eye, ChevronRight } from 'lucide-react'
import { ErrorState } from '@/components/ui/error-state'
import Image from 'next/image'
import { fareeqChart, fareeqHex } from '@/lib/design-system'

interface CityBreakdown {
  city_en: string
  city_ar: string
  count: number
}

interface BrandSummary {
  brand_ar: string
  brand_en: string
  logo: string | null
  total_branches: number
  cities: CityBreakdown[]
  cities_count: number
  with_territory: number
  territory_count: number
  coverage_pct: number
  with_media_pct: number
}

interface CityInfo {
  city_ar: string
  city_en: string
  brands: number
  pois: number
}

interface ApiResponse {
  total_grocery_pois: number
  identified_brand_pois: number
  generic_pois: number
  brands_count: number
  brands: BrandSummary[]
  cities: CityInfo[]
}

const BRAND_COLORS = [
  fareeqChart.blue,
  fareeqChart.green,
  fareeqHex.amber,
  fareeqChart.coral,
  '#065f46',
  '#8B5CF6',
  '#EC4899',
  '#14B8A6',
  '#F97316',
  '#6366F1',
  '#84CC16',
  '#06B6D4',
  '#E11D48',
  '#A855F7',
  '#0EA5E9',
]

export default function CoveragePage() {
  const { lang, dataSource } = useAppStore()
  const isAr = lang === 'ar'
  const t = PAGE_TITLES['/coverage']

  const [data, setData] = useState<ApiResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [selectedCity, setSelectedCity] = useState<string>('__all__')
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null)
  const [cityDropdownOpen, setCityDropdownOpen] = useState(false)
  const [citySearch, setCitySearch] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setFetchError(false)
    const url = selectedCity === '__all__' ? '/api/coverage' : `/api/coverage?city=${encodeURIComponent(selectedCity)}`
    fetch(url, { signal: controller.signal })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((d: ApiResponse) => {
        setData(d)
        setSelectedBrand(null)
        setLoading(false)
      })
      .catch((err) => {
        if ((err as Error).name === 'AbortError') return
        setFetchError(true)
        setLoading(false)
      })
    return () => controller.abort()
  }, [selectedCity])

  const brandDetail = useMemo(() => {
    if (!data || !selectedBrand) return null
    return data.brands.find(b => b.brand_en === selectedBrand) ?? null
  }, [data, selectedBrand])

  const coverageTopbar = useMemo(() => {
    const tb = getPageTopbarCopy('/coverage', dataSource)
    return (
      <Topbar
        title_ar={t.ar}
        title_en={t.en}
        description_ar={tb.description_ar}
        description_en={tb.description_en}
      />
    )
  }, [t.ar, t.en, dataSource])

  if (!loading && fetchError) {
    return (
      <div>
        {coverageTopbar}
        <div className="page-shell">
          <ErrorState
            lang={isAr ? 'ar' : 'en'}
            onRetry={() => {
              setFetchError(false)
              setLoading(true)
              const url = selectedCity === '__all__' ? '/api/coverage' : `/api/coverage?city=${encodeURIComponent(selectedCity)}`
              fetch(url)
                .then(r => { if (!r.ok) throw new Error(); return r.json() })
                .then((d: ApiResponse) => { setData(d); setLoading(false) })
                .catch(() => { setFetchError(true); setLoading(false) })
            }}
          />
        </div>
      </div>
    )
  }

  if (loading || !data) {
    return (
      <div>
        {coverageTopbar}
        <div className="page-shell">
          <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] sm:grid-cols-2 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => <KpiCardSkeleton key={i} />)}
          </div>
          <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-2">
            <ChartCardSkeleton height={300} />
            <ChartCardSkeleton height={300} />
          </div>
        </div>
      </div>
    )
  }

  if (!data.brands.length) {
    return (
      <div>
        {coverageTopbar}
        <div className="page-shell">
          <EmptyState
            title={isAr ? 'لا توجد بيانات تغطية' : 'No coverage data'}
            description={isAr ? 'لم يتم العثور على بيانات السوبرماركتات.' : 'Supermarket coverage data not found.'}
          />
        </div>
      </div>
    )
  }

  const totalBranches = data.brands.reduce((s, b) => s + b.total_branches, 0)
  const totalBrands = data.brands_count
  const identifiedPct = data.total_grocery_pois > 0
    ? Math.round(data.identified_brand_pois / data.total_grocery_pois * 100)
    : 0
  const avgCoverage = totalBranches > 0
    ? Math.round(data.brands.reduce((s, b) => s + b.coverage_pct * b.total_branches, 0) / totalBranches * 10) / 10
    : 0
  const avgMedia = totalBranches > 0
    ? Math.round(data.brands.reduce((s, b) => s + b.with_media_pct * b.total_branches, 0) / totalBranches * 10) / 10
    : 0

  const branchChartData = data.brands.slice(0, 15).map(b => ({
    name: isAr ? b.brand_ar : b.brand_en,
    [isAr ? 'عدد الفروع' : 'Branches']: b.total_branches,
  }))

  const coverageChartData = data.brands
    .filter(b => b.total_branches >= 5)
    .map(b => ({
      name: isAr ? b.brand_ar : b.brand_en,
      [isAr ? 'نسبة التغطية %' : 'Coverage %']: b.coverage_pct,
    }))

  const pieData = data.brands.slice(0, 10).map((b, i) => ({
    name: isAr ? b.brand_ar : b.brand_en,
    value: b.total_branches,
    color: BRAND_COLORS[i % BRAND_COLORS.length],
  }))

  return (
    <div>
      {coverageTopbar}
      <div className="page-shell space-y-[var(--density-grid-gap)]">
        {/* City filter */}
        <div className="relative inline-block">
          <button
            type="button"
            onClick={() => setCityDropdownOpen(o => !o)}
            className="flex items-center gap-2 rounded-[var(--radius-lg)] border px-4 py-2.5 text-sm font-medium transition-colors"
            style={{
              borderColor: 'var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text-primary)',
            }}
          >
            <MapPin className="h-4 w-4" style={{ color: 'var(--color-interactive)' }} />
            {selectedCity === '__all__'
              ? (isAr ? 'جميع المدن' : 'All cities')
              : (isAr
                  ? data.cities.find(c => c.city_en === selectedCity)?.city_ar ?? selectedCity
                  : selectedCity
                )
            }
            <ChevronDown className="h-4 w-4 opacity-60" />
          </button>
          {cityDropdownOpen && (
            <>
              <div className="fixed inset-0 z-30" onClick={() => setCityDropdownOpen(false)} />
              <div
                className="absolute top-full mt-1 z-40 min-w-[240px] rounded-[var(--radius-lg)] border shadow-lg overflow-hidden flex flex-col"
                style={{
                  background: 'var(--color-surface)',
                  borderColor: 'var(--color-border)',
                  insetInlineStart: 0,
                  maxHeight: '320px',
                }}
              >
                {/* Search input */}
                <div className="border-b px-2 py-2" style={{ borderColor: 'var(--color-border)' }}>
                  <input
                    type="search"
                    autoFocus
                    value={citySearch}
                    onChange={e => setCitySearch(e.target.value)}
                    placeholder={isAr ? 'بحث عن مدينة...' : 'Search city...'}
                    className="w-full px-3 py-1.5 text-sm rounded-lg border focus:outline-none focus:ring-1 focus:ring-[var(--color-interactive)]"
                    style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface-muted)', color: 'var(--color-text-primary)' }}
                  />
                </div>
                <div className="overflow-y-auto">
                  {!citySearch && (
                    <button
                      type="button"
                      onClick={() => { setSelectedCity('__all__'); setCityDropdownOpen(false); setCitySearch('') }}
                      className="w-full px-4 py-2.5 text-start text-sm hover:bg-[var(--color-surface-muted)] transition-colors"
                      style={{
                        color: selectedCity === '__all__' ? 'var(--color-interactive)' : 'var(--color-text-primary)',
                        fontWeight: selectedCity === '__all__' ? 600 : 400,
                      }}
                    >
                      {isAr ? 'جميع المدن' : 'All cities'}
                    </button>
                  )}
                  {data.cities
                    .filter(c => !citySearch || (isAr ? c.city_ar : c.city_en).toLowerCase().includes(citySearch.toLowerCase()))
                    .map(c => (
                      <button
                        key={c.city_en}
                        type="button"
                        onClick={() => { setSelectedCity(c.city_en); setCityDropdownOpen(false); setCitySearch('') }}
                        className="w-full px-4 py-2.5 text-start text-sm hover:bg-[var(--color-surface-muted)] transition-colors flex items-center justify-between"
                        style={{
                          color: selectedCity === c.city_en ? 'var(--color-interactive)' : 'var(--color-text-primary)',
                          fontWeight: selectedCity === c.city_en ? 600 : 400,
                        }}
                      >
                        <span>{isAr ? c.city_ar : c.city_en}</span>
                        <span className="text-xs tabular-nums opacity-60">
                          {c.brands} {isAr ? 'علامة' : 'brands'}
                        </span>
                      </button>
                    ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] sm:grid-cols-2 md:grid-cols-4">
          <KpiCard
            title_ar="العلامات التجارية"
            title_en="Brands"
            value={totalBrands}
            icon={<Store className="h-5 w-5" />}
            color={fareeqChart.blue}
            lang={lang}
            countUp
            subtitle={isAr
              ? `من أصل ${data.total_grocery_pois.toLocaleString()} نقطة بقالة`
              : `out of ${data.total_grocery_pois.toLocaleString()} grocery POIs`
            }
          />
          <KpiCard
            title_ar="إجمالي الفروع"
            title_en="Total Branches"
            value={totalBranches}
            icon={<MapPin className="h-5 w-5" />}
            color={fareeqChart.green}
            lang={lang}
            countUp
          />
          <KpiCard
            title_ar="التغطية الميدانية"
            title_en="Territory Coverage"
            value={avgCoverage}
            unit="%"
            icon={<Layers className="h-5 w-5" />}
            color={fareeqHex.amber}
            lang={lang}
            countUp
            countDecimals={1}
          />
          <KpiCard
            title_ar="التوثيق بالصور"
            title_en="Media Coverage"
            value={avgMedia}
            unit="%"
            icon={<ShieldCheck className="h-5 w-5" />}
            color={fareeqChart.coral}
            lang={lang}
            countUp
            countDecimals={1}
          />
        </div>

        {/* Data Coverage Quality */}
        {data.total_grocery_pois > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>
                {isAr ? 'جودة تغطية البيانات' : 'Data Coverage Quality'}
              </CardTitle>
              <p className="text-[11px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                {isAr
                  ? 'نسبة نقاط الاهتمام التي تم تحديد علامتها التجارية'
                  : 'Share of surveyed POIs with an identified brand'}
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Total count */}
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                {isAr ? 'إجمالي نقاط الاهتمام المسحوبة:' : 'Total POIs surveyed:'}
                {' '}
                <span className="font-bold tabular-nums" style={{ color: 'var(--color-text-primary)' }}>
                  {data.total_grocery_pois.toLocaleString()}
                </span>
              </p>

              {/* Progress bar */}
              <div className="space-y-1.5">
                <div
                  className="relative h-4 w-full rounded-full overflow-hidden"
                  style={{ background: 'var(--color-surface-muted)' }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${identifiedPct}%`,
                      background: 'var(--color-trend-up)',
                    }}
                  />
                </div>
                <p className="text-base font-bold tabular-nums" style={{ color: 'var(--color-trend-up)' }}>
                  {identifiedPct}%{' '}
                  <span className="text-sm font-normal" style={{ color: 'var(--color-text-secondary)' }}>
                    {isAr ? 'معرّف / Identified' : 'Identified'}
                  </span>
                </p>
              </div>

              {/* Stat blocks */}
              <div className="grid grid-cols-2 gap-3">
                <div
                  className="rounded-[var(--radius-lg)] border p-3"
                  style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
                >
                  <p className="text-[10px] font-medium" style={{ color: 'var(--color-text-muted)' }}>
                    ✅ {isAr ? 'نقاط معرّفة (علامة تجارية)' : 'Identified (known brands)'}
                  </p>
                  <p
                    className="text-xl font-bold tabular-nums mt-0.5"
                    style={{ color: 'var(--color-trend-up)' }}
                  >
                    {data.identified_brand_pois.toLocaleString()}
                  </p>
                </div>
                <div
                  className="rounded-[var(--radius-lg)] border p-3"
                  style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
                >
                  <p className="text-[10px] font-medium" style={{ color: 'var(--color-text-muted)' }}>
                    {'❓'} {isAr ? 'نقاط غير معرّفة' : 'Generic / Unmatched'}
                  </p>
                  <p
                    className="text-xl font-bold tabular-nums mt-0.5"
                    style={{ color: 'var(--color-text-secondary)' }}
                  >
                    {data.generic_pois.toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Contextual insight */}
              <div
                className="rounded-[var(--radius-lg)] border-s-4 px-4 py-3"
                style={{
                  borderColor: identifiedPct >= 75
                    ? 'var(--color-trend-up)'
                    : identifiedPct >= 50
                      ? fareeqHex.amber
                      : 'var(--color-trend-down)',
                  background: identifiedPct >= 75
                    ? 'color-mix(in srgb, var(--color-trend-up) 6%, transparent)'
                    : identifiedPct >= 50
                      ? `color-mix(in srgb, ${fareeqHex.amber} 8%, transparent)`
                      : 'color-mix(in srgb, var(--color-trend-down) 6%, transparent)',
                }}
              >
                <p
                  className="text-sm"
                  style={{
                    color: identifiedPct >= 75
                      ? 'var(--color-trend-up)'
                      : identifiedPct >= 50
                        ? fareeqHex.amber
                        : 'var(--color-trend-down)',
                  }}
                >
                  {identifiedPct >= 75
                    ? (isAr
                      ? 'تغطية بيانات ممتازة — 3/4 من نقاط السوق مُصنّفة.'
                      : 'Excellent data coverage — 3 in 4 market locations are branded.')
                    : identifiedPct >= 50
                      ? (isAr
                        ? 'تغطية جيدة. الجزء غير المعرّف فرصة للرصد المستقبلي.'
                        : 'Good coverage. Unidentified POIs represent future monitoring opportunity.')
                      : (isAr
                        ? 'تغطية جزئية. قد تكون هناك علامات تجارية غير ممثّلة في التحليل.'
                        : 'Partial coverage. Some brands may be underrepresented in the analysis.')}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-2">
          <ChartReveal>
            <Card>
              <CardHeader>
                <CardTitle>{isAr ? 'عدد الفروع لكل علامة' : 'Branches per Brand'}</CardTitle>
                {data.brands.length > 15 && (
                  <p className="text-[11px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                    {isAr ? `يعرض أعلى 15 من ${data.brands.length} علامة` : `Showing top 15 of ${data.brands.length} brands`}
                  </p>
                )}
              </CardHeader>
              <CardContent>
                <SimpleBarChart
                  data={branchChartData}
                  dataKey={isAr ? 'عدد الفروع' : 'Branches'}
                  color={fareeqChart.blue}
                  height={320}
                />
              </CardContent>
            </Card>
          </ChartReveal>
          <ChartReveal>
            <Card>
              <CardHeader>
                <CardTitle>{isAr ? 'حصة الفروع' : 'Branch Share'}</CardTitle>
                {data.brands.length > 10 && (
                  <p className="text-[11px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                    {isAr ? `يعرض أعلى 10 من ${data.brands.length} علامة` : `Showing top 10 of ${data.brands.length} brands`}
                  </p>
                )}
              </CardHeader>
              <CardContent>
                <SimplePieChart data={pieData} height={320} />
              </CardContent>
            </Card>
          </ChartReveal>
        </div>

        <ChartReveal>
          <Card>
            <CardHeader>
              <CardTitle>{isAr ? 'نسبة التغطية الميدانية (5 فروع فأكثر)' : 'Territory Coverage (5+ branches)'}</CardTitle>
            </CardHeader>
            <CardContent>
              <SimpleBarChart
                data={coverageChartData}
                dataKey={isAr ? 'نسبة التغطية %' : 'Coverage %'}
                color={fareeqChart.green}
                height={300}
                unit="%"
              />
            </CardContent>
          </Card>
        </ChartReveal>

        {/* Brands table */}
        <Card>
          <CardHeader>
            <CardTitle>{isAr ? 'تفاصيل العلامات التجارية' : 'Brand Details'}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr
                    className="border-b text-start"
                    style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
                  >
                    <th className="py-3 px-3 text-start font-medium sticky start-0 z-10" style={{ background: 'var(--color-surface)' }}>{isAr ? 'العلامة التجارية' : 'Brand'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'الفروع' : 'Branches'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'المدن' : 'Cities'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'المناطق' : 'Territories'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'التغطية' : 'Coverage'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'الصور' : 'Media'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'التوزيع' : 'Distribution'}</th>
                    <th className="py-3 px-3 w-8" />
                  </tr>
                </thead>
                <tbody>
                  {data.brands.map(b => (
                    <tr
                      key={b.brand_en}
                      className="border-b transition-colors hover:bg-[var(--color-surface-muted)] cursor-pointer"
                      style={{
                        borderColor: 'var(--color-border)',
                        background: selectedBrand === b.brand_en
                          ? 'color-mix(in srgb, var(--color-interactive) 8%, transparent)'
                          : undefined,
                      }}
                      onClick={() => setSelectedBrand(selectedBrand === b.brand_en ? null : b.brand_en)}
                    >
                      <td
                        className="py-3 px-3 sticky start-0 z-10"
                        style={{
                          background: selectedBrand === b.brand_en
                            ? 'color-mix(in srgb, var(--color-interactive) 8%, var(--color-surface))'
                            : 'var(--color-surface)',
                        }}
                      >
                        <div className="flex items-center gap-2">
                          {b.logo ? (
                            <span className="relative h-8 w-8 shrink-0 overflow-hidden rounded-lg bg-white ring-1 ring-black/[0.06]">
                              <Image
                                src={b.logo}
                                alt={b.brand_en}
                                fill
                                className="object-contain p-0.5"
                                sizes="32px"
                              />
                            </span>
                          ) : (
                            <span
                              className="h-8 w-8 rounded-lg flex items-center justify-center text-xs font-bold text-white shrink-0"
                              style={{ background: BRAND_COLORS[data.brands.indexOf(b) % BRAND_COLORS.length] }}
                            >
                              {b.brand_ar.charAt(0)}
                            </span>
                          )}
                          <div>
                            <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
                              {isAr ? b.brand_ar : b.brand_en}
                            </p>
                            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                              {isAr ? b.brand_en : b.brand_ar}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-3 tabular-nums font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                        {b.total_branches}
                      </td>
                      <td className="py-3 px-3 tabular-nums">{b.cities_count}</td>
                      <td className="py-3 px-3 tabular-nums">{b.territory_count}</td>
                      <td className="py-3 px-3">
                        <CoverageBar pct={b.coverage_pct} />
                      </td>
                      <td className="py-3 px-3 tabular-nums">{b.with_media_pct}%</td>
                      <td className="py-3 px-3">
                        <div className="flex gap-1 flex-wrap max-w-[200px]">
                          {b.cities.map(c => (
                            <span
                              key={c.city_en}
                              className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px]"
                              style={{
                                background: 'var(--color-surface-muted)',
                                color: 'var(--color-text-secondary)',
                              }}
                            >
                              {isAr ? c.city_ar : c.city_en}
                              <span className="font-semibold tabular-nums">{c.count}</span>
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3 px-2 text-center">
                        <ChevronRight
                          className="h-4 w-4 transition-transform duration-200 opacity-40"
                          style={{
                            color: 'var(--color-text-muted)',
                            transform: selectedBrand === b.brand_en ? 'rotate(90deg)' : undefined,
                          }}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Brand detail card */}
        {brandDetail && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="h-4 w-4" style={{ color: 'var(--color-interactive)' }} />
                {isAr ? brandDetail.brand_ar : brandDetail.brand_en}
                <span className="text-xs font-normal" style={{ color: 'var(--color-text-muted)' }}>
                  — {isAr ? 'تفاصيل التوزيع' : 'Distribution details'}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
                <StatBlock
                  label={isAr ? 'إجمالي الفروع' : 'Total branches'}
                  value={brandDetail.total_branches}
                />
                <StatBlock
                  label={isAr ? 'المدن' : 'Cities'}
                  value={brandDetail.cities_count}
                />
                <StatBlock
                  label={isAr ? 'المناطق' : 'Territories'}
                  value={brandDetail.territory_count}
                />
                <StatBlock
                  label={isAr ? 'التغطية' : 'Coverage'}
                  value={`${brandDetail.coverage_pct}%`}
                />
                <StatBlock
                  label={isAr ? 'الصور' : 'Media'}
                  value={`${brandDetail.with_media_pct}%`}
                />
              </div>
              <div className="mt-4">
                <p className="text-xs font-medium mb-2" style={{ color: 'var(--color-text-muted)' }}>
                  {isAr ? 'التوزيع حسب المدينة' : 'Distribution by city'}
                </p>
                <div className="flex gap-3 flex-wrap">
                  {brandDetail.cities.map((c, i) => (
                    <div
                      key={c.city_en}
                      className="rounded-[var(--radius-lg)] border p-3 min-w-[120px]"
                      style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
                    >
                      <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                        {isAr ? c.city_ar : c.city_en}
                      </p>
                      <p className="text-xl font-bold tabular-nums mt-1" style={{ color: BRAND_COLORS[i % BRAND_COLORS.length] }}>
                        {c.count}
                      </p>
                      <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                        {brandDetail.total_branches > 0
                          ? `${Math.round(c.count / brandDetail.total_branches * 100)}%`
                          : '—'
                        }
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ── Expansion Intelligence ── */}
        <ExpansionIntelligence data={data} isAr={isAr} />
      </div>
    </div>
  )
}

function CoverageBar({ pct }: { pct: number }) {
  const color =
    pct >= 80
      ? 'var(--color-trend-up)'
      : pct >= 40
        ? fareeqHex.amber
        : 'var(--color-trend-down)'
  return (
    <div className="flex items-center gap-2">
      <div
        className="h-2 flex-1 max-w-[80px] rounded-full overflow-hidden"
        style={{ background: 'var(--color-surface-muted)' }}
      >
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${Math.min(100, pct)}%`, background: color }}
        />
      </div>
      <span className="text-xs tabular-nums" style={{ color: 'var(--color-text-secondary)' }}>
        {pct}%
      </span>
    </div>
  )
}

function StatBlock({ label, value }: { label: string; value: string | number }) {
  return (
    <div
      className="rounded-[var(--radius-lg)] border p-3"
      style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
    >
      <p className="text-[10px] font-medium" style={{ color: 'var(--color-text-muted)' }}>{label}</p>
      <p className="text-lg font-bold tabular-nums mt-0.5" style={{ color: 'var(--color-text-primary)' }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </p>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Expansion Intelligence
// ─────────────────────────────────────────────────────────────

interface ExpansionCity extends CityInfo {
  expansionScore: number
  opportunityLevel: 'high' | 'medium' | 'mature'
}

function computeExpansionScore(c: CityInfo): number {
  return Math.round(c.brands * 10 + c.pois * 0.5)
}

function opportunityLevel(score: number): 'high' | 'medium' | 'mature' {
  if (score > 200) return 'high'
  if (score >= 100) return 'medium'
  return 'mature'
}

function OpportunityBadge({ level, isAr }: { level: 'high' | 'medium' | 'mature'; isAr: boolean }) {
  const styles: Record<typeof level, { bg: string; color: string; label_ar: string; label_en: string }> = {
    high: {
      bg: 'color-mix(in srgb, var(--color-trend-up) 12%, transparent)',
      color: 'var(--color-trend-up)',
      label_ar: 'فرصة عالية',
      label_en: 'High Opportunity',
    },
    medium: {
      bg: 'color-mix(in srgb, #f59e0b 12%, transparent)',
      color: '#b45309',
      label_ar: 'فرصة متوسطة',
      label_en: 'Medium Opportunity',
    },
    mature: {
      bg: 'var(--color-surface-muted)',
      color: 'var(--color-text-muted)',
      label_ar: 'سوق ناضج',
      label_en: 'Mature Market',
    },
  }
  const s = styles[level]
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium"
      style={{ background: s.bg, color: s.color }}
    >
      {isAr ? s.label_ar : s.label_en}
    </span>
  )
}

function ExpansionIntelligence({ data, isAr }: { data: ApiResponse; isAr: boolean }) {
  const expansionCities = useMemo<ExpansionCity[]>(() => {
    return data.cities
      .map(c => {
        const score = computeExpansionScore(c)
        return { ...c, expansionScore: score, opportunityLevel: opportunityLevel(score) }
      })
      .sort((a, b) => b.expansionScore - a.expansionScore)
  }, [data.cities])

  // Top 8 cities by POI for brand distribution grid
  const top8Cities = useMemo(() => {
    return [...data.cities].sort((a, b) => b.pois - a.pois).slice(0, 8)
  }, [data.cities])

  // Brand lookup per city: for each city_en, find brands that have that city
  const brandsByCity = useMemo(() => {
    const map: Record<string, { brand: BrandSummary; count: number }[]> = {}
    for (const city of top8Cities) {
      const entries = data.brands
        .map(b => {
          const cityEntry = b.cities.find(c => c.city_en === city.city_en)
          return cityEntry ? { brand: b, count: cityEntry.count } : null
        })
        .filter((x): x is { brand: BrandSummary; count: number } => x !== null)
        .sort((a, b) => b.count - a.count)
      map[city.city_en] = entries
    }
    return map
  }, [top8Cities, data.brands])

  // Section C: competitive intensity stats
  const mostCompetitive = useMemo(
    () => [...data.cities].sort((a, b) => b.brands - a.brands)[0] ?? null,
    [data.cities]
  )
  const leastCompetitive = useMemo(
    () => data.cities.filter(c => c.pois > 0).sort((a, b) => a.brands - b.brands)[0] ?? null,
    [data.cities]
  )
  const avgBrandsPerCity = useMemo(() => {
    if (!data.cities.length) return 0
    const sum = data.cities.reduce((s, c) => s + c.brands, 0)
    return Math.round((sum / data.cities.length) * 10) / 10
  }, [data.cities])

  const lowOpportunityCities = expansionCities.filter(c => c.opportunityLevel === 'mature')
  const lowCityNames = lowOpportunityCities.map(c => (isAr ? c.city_ar : c.city_en)).join('، ')

  return (
    <div className="animate-fade-in space-y-[var(--density-grid-gap)]">
      {/* Divider */}
      <div className="border-t" style={{ borderColor: 'var(--color-border)' }} />

      {/* Section header */}
      <div>
        <h2 className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>
          {isAr ? 'ذكاء التوسع' : 'Expansion Intelligence'}
        </h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          {isAr
            ? 'تحليل الفرص الجغرافية وكثافة المنافسة لدعم قرارات التوسع.'
            : 'Geographic opportunity analysis and competitive intensity to support expansion decisions.'}
        </p>
      </div>

      {/* ── Section A: City Expansion Scorecard ── */}
      <Card>
        <CardHeader>
          <CardTitle>
            {isAr
              ? 'فرص التوسع الجغرافي / Geographic Expansion Opportunities'
              : 'Geographic Expansion Opportunities / فرص التوسع الجغرافي'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr
                  className="border-b text-start"
                  style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
                >
                  <th className="py-3 px-3 text-start font-medium">{isAr ? 'المدينة' : 'City'}</th>
                  <th className="py-3 px-3 text-start font-medium">{isAr ? 'العلامات الموجودة' : 'Brands Present'}</th>
                  <th className="py-3 px-3 text-start font-medium">{isAr ? 'إجمالي المنافذ' : 'Total POIs'}</th>
                  <th className="py-3 px-3 text-start font-medium">{isAr ? 'درجة التوسع' : 'Expansion Score'}</th>
                  <th className="py-3 px-3 text-start font-medium">{isAr ? 'مستوى الفرصة' : 'Opportunity Level'}</th>
                </tr>
              </thead>
              <tbody>
                {expansionCities.map(city => (
                  <tr
                    key={city.city_en}
                    className="border-b transition-colors hover:bg-[var(--color-surface-muted)]"
                    style={{ borderColor: 'var(--color-border)' }}
                  >
                    <td className="py-3 px-3">
                      <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
                        {isAr ? city.city_ar : city.city_en}
                      </p>
                      <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                        {isAr ? city.city_en : city.city_ar}
                      </p>
                    </td>
                    <td className="py-3 px-3 tabular-nums font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                      {city.brands}
                    </td>
                    <td className="py-3 px-3 tabular-nums" style={{ color: 'var(--color-text-secondary)' }}>
                      {city.pois.toLocaleString()}
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div
                          className="h-1.5 w-16 rounded-full overflow-hidden"
                          style={{ background: 'var(--color-surface-muted)' }}
                        >
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${Math.min(100, (city.expansionScore / Math.max(...expansionCities.map(c => c.expansionScore), 1)) * 100)}%`,
                              background: city.opportunityLevel === 'high'
                                ? 'var(--color-trend-up)'
                                : city.opportunityLevel === 'medium'
                                  ? '#f59e0b'
                                  : 'var(--color-text-muted)',
                            }}
                          />
                        </div>
                        <span className="tabular-nums text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                          {city.expansionScore}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <OpportunityBadge level={city.opportunityLevel} isAr={isAr} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* ── Section B: Brand Distribution by City ── */}
      <Card>
        <CardHeader>
          <CardTitle>
            {isAr
              ? 'توزيع العلامات التجارية بالمدن / Brand Distribution by City'
              : 'Brand Distribution by City / توزيع العلامات التجارية بالمدن'}
          </CardTitle>
          <p className="text-[11px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            {isAr ? 'أعلى 8 مدن حسب عدد المنافذ' : 'Top 8 cities by POI count'}
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {top8Cities.map(city => {
              const cityBrands = brandsByCity[city.city_en] ?? []
              const top5 = cityBrands.slice(0, 5)
              return (
                <div
                  key={city.city_en}
                  className="rounded-[var(--radius-lg)] border p-4"
                  style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
                >
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div>
                      <p className="font-semibold text-sm" style={{ color: 'var(--color-text-primary)' }}>
                        {isAr ? city.city_ar : city.city_en}
                      </p>
                      <p className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>
                        {cityBrands.length} {isAr ? 'علامة تجارية' : 'brands'}
                      </p>
                    </div>
                    <span
                      className="text-xs tabular-nums font-bold px-2 py-0.5 rounded-full"
                      style={{
                        background: 'color-mix(in srgb, var(--color-interactive) 10%, transparent)',
                        color: 'var(--color-interactive)',
                      }}
                    >
                      {city.pois.toLocaleString()} {isAr ? 'منفذ' : 'POIs'}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {top5.map(({ brand, count }) => (
                      <div
                        key={brand.brand_en}
                        className="flex items-center gap-1 rounded-full border px-2 py-1"
                        style={{
                          borderColor: 'var(--color-border)',
                          background: 'var(--color-surface-muted)',
                        }}
                      >
                        {brand.logo ? (
                          <span className="relative h-4 w-4 shrink-0 overflow-hidden rounded bg-white">
                            <Image
                              src={brand.logo}
                              alt={brand.brand_en}
                              width={16}
                              height={16}
                              className="object-contain"
                            />
                          </span>
                        ) : (
                          <span
                            className="h-4 w-4 rounded flex items-center justify-center text-[9px] font-bold text-white shrink-0"
                            style={{ background: BRAND_COLORS[data.brands.indexOf(brand) % BRAND_COLORS.length] }}
                          >
                            {brand.brand_ar.charAt(0)}
                          </span>
                        )}
                        <span className="text-[11px]" style={{ color: 'var(--color-text-secondary)' }}>
                          {isAr ? brand.brand_ar : brand.brand_en}
                        </span>
                        <span
                          className="text-[10px] tabular-nums font-semibold"
                          style={{ color: 'var(--color-text-muted)' }}
                        >
                          {count}
                        </span>
                      </div>
                    ))}
                    {cityBrands.length > 5 && (
                      <span
                        className="flex items-center rounded-full px-2 py-1 text-[11px]"
                        style={{ background: 'var(--color-surface-muted)', color: 'var(--color-text-muted)' }}
                      >
                        +{cityBrands.length - 5}
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* ── Section C: Competitive Intensity ── */}
      <Card>
        <CardHeader>
          <CardTitle>
            {isAr
              ? 'كثافة المنافسة / Competitive Intensity'
              : 'Competitive Intensity / كثافة المنافسة'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {/* Most competitive */}
            <div
              className="rounded-[var(--radius-lg)] border p-4"
              style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
            >
              <p className="text-[11px] font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {isAr ? 'أكثر مدينة منافسة' : 'Most Competitive City'}
              </p>
              <p className="text-lg font-bold mt-1" style={{ color: 'var(--color-text-primary)' }}>
                {mostCompetitive ? (isAr ? mostCompetitive.city_ar : mostCompetitive.city_en) : '—'}
              </p>
              {mostCompetitive && (
                <p className="text-xs mt-0.5 tabular-nums" style={{ color: 'var(--color-text-secondary)' }}>
                  {mostCompetitive.brands} {isAr ? 'علامة' : 'brands'} · {mostCompetitive.pois.toLocaleString()} {isAr ? 'منفذ' : 'POIs'}
                </p>
              )}
            </div>

            {/* Least competitive */}
            <div
              className="rounded-[var(--radius-lg)] border p-4"
              style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
            >
              <p className="text-[11px] font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {isAr ? 'أقل مدينة منافسة' : 'Least Competitive City'}
              </p>
              <p className="text-lg font-bold mt-1" style={{ color: 'var(--color-trend-up)' }}>
                {leastCompetitive ? (isAr ? leastCompetitive.city_ar : leastCompetitive.city_en) : '—'}
              </p>
              {leastCompetitive && (
                <p className="text-xs mt-0.5 tabular-nums" style={{ color: 'var(--color-text-secondary)' }}>
                  {leastCompetitive.brands} {isAr ? 'علامة' : 'brands'} · {leastCompetitive.pois.toLocaleString()} {isAr ? 'منفذ' : 'POIs'}
                </p>
              )}
            </div>

            {/* Average brands */}
            <div
              className="rounded-[var(--radius-lg)] border p-4"
              style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
            >
              <p className="text-[11px] font-medium" style={{ color: 'var(--color-text-muted)' }}>
                {isAr ? 'متوسط العلامات لكل مدينة' : 'Avg Brands per City'}
              </p>
              <p className="text-lg font-bold tabular-nums mt-1" style={{ color: 'var(--color-interactive)' }}>
                {avgBrandsPerCity}
              </p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary)' }}>
                {isAr ? `عبر ${data.cities.length} مدينة` : `across ${data.cities.length} cities`}
              </p>
            </div>
          </div>

          {/* Insight text */}
          {lowOpportunityCities.length > 0 && (
            <div
              className="rounded-[var(--radius-lg)] border-s-4 px-4 py-3"
              style={{
                borderColor: 'var(--color-interactive)',
                background: 'color-mix(in srgb, var(--color-interactive) 6%, transparent)',
              }}
            >
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                {isAr
                  ? `المدن ذات الكثافة المنخفضة (${lowCityNames}) قد تمثل فرصاً للتوسع بمنافسة أقل.`
                  : `Cities with low competitive density (${lowCityNames}) may represent expansion opportunities with less competition.`}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
