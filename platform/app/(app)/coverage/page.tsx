'use client'

import { useEffect, useState, useMemo } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { KpiCard } from '@/components/ui/kpi-card'
import { SimpleBarChart } from '@/components/charts/BarChartComponent'
import { SimplePieChart } from '@/components/charts/PieChartComponent'
import { ChartReveal } from '@/components/ui/chart-reveal'
import { EmptyState } from '@/components/ui/empty-state'
import { KpiCardSkeleton, ChartCardSkeleton } from '@/components/ui/skeleton'
import { Store, MapPin, Layers, ShieldCheck, ChevronDown, Eye } from 'lucide-react'
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
  fareeqHex.mintDark,
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
  const { lang } = useAppStore()
  const isAr = lang === 'ar'
  const t = PAGE_TITLES['/coverage']

  const [data, setData] = useState<ApiResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedCity, setSelectedCity] = useState<string>('__all__')
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null)
  const [cityDropdownOpen, setCityDropdownOpen] = useState(false)

  useEffect(() => {
    setLoading(true)
    const url = selectedCity === '__all__' ? '/api/coverage' : `/api/coverage?city=${encodeURIComponent(selectedCity)}`
    fetch(url)
      .then(r => r.json())
      .then((d: ApiResponse) => {
        setData(d)
        setSelectedBrand(null)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [selectedCity])

  const brandDetail = useMemo(() => {
    if (!data || !selectedBrand) return null
    return data.brands.find(b => b.brand_en === selectedBrand) ?? null
  }, [data, selectedBrand])

  if (loading || !data) {
    return (
      <div>
        <Topbar
          title_ar={t.ar}
          title_en={t.en}
          description_ar="تغطية السوبرماركتات والعلامات التجارية في السوق."
          description_en="Supermarket and grocery brand coverage in the market."
        />
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
        <Topbar title_ar={t.ar} title_en={t.en} />
        <div className="page-shell">
          <EmptyState
            title_ar="لا توجد بيانات تغطية"
            title_en="No coverage data"
            description_ar="لم يتم العثور على بيانات السوبرماركتات."
            description_en="Supermarket coverage data not found."
          />
        </div>
      </div>
    )
  }

  const totalBranches = data.brands.reduce((s, b) => s + b.total_branches, 0)
  const totalBrands = data.brands_count
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
      <Topbar
        title_ar={t.ar}
        title_en={t.en}
        description_ar="تغطية السوبرماركتات والعلامات التجارية في السوق."
        description_en="Supermarket and grocery brand coverage in the market."
      />
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
                className="absolute top-full mt-1 z-40 min-w-[220px] rounded-[var(--radius-lg)] border shadow-lg overflow-hidden"
                style={{
                  background: 'var(--color-surface)',
                  borderColor: 'var(--color-border)',
                  insetInlineStart: 0,
                }}
              >
                <button
                  type="button"
                  onClick={() => { setSelectedCity('__all__'); setCityDropdownOpen(false) }}
                  className="w-full px-4 py-2.5 text-start text-sm hover:bg-[var(--color-surface-muted)] transition-colors"
                  style={{
                    color: selectedCity === '__all__' ? 'var(--color-interactive)' : 'var(--color-text-primary)',
                    fontWeight: selectedCity === '__all__' ? 600 : 400,
                  }}
                >
                  {isAr ? 'جميع المدن' : 'All cities'}
                </button>
                {data.cities.map(c => (
                  <button
                    key={c.city_en}
                    type="button"
                    onClick={() => { setSelectedCity(c.city_en); setCityDropdownOpen(false) }}
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

        {/* Charts */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-2">
          <ChartReveal>
            <Card>
              <CardHeader>
                <CardTitle>{isAr ? 'عدد الفروع لكل علامة' : 'Branches per Brand'}</CardTitle>
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
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'العلامة التجارية' : 'Brand'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'الفروع' : 'Branches'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'المدن' : 'Cities'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'المناطق' : 'Territories'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'التغطية' : 'Coverage'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'الصور' : 'Media'}</th>
                    <th className="py-3 px-3 text-start font-medium">{isAr ? 'التوزيع' : 'Distribution'}</th>
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
                      <td className="py-3 px-3">
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
