'use client'
import { useState, useMemo, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { fareeqChart, fareeqHex } from '@/lib/design-system'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { Card } from '@/components/ui/card'
import { TagBadge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { LoadingOverlay } from '@/components/ui/spinner'
import { ErrorState } from '@/components/ui/error-state'
import { EmptyState } from '@/components/ui/empty-state'
import { Search, Download, X } from 'lucide-react'
import type { ProductComparison } from '@/lib/types'
import { cn } from '@/components/ui/cn'

const ACTION_MAP: Record<string, { ar: string; en: string; color: string }> = {
  decrease: { ar: 'خفض السعر', en: 'Decrease Price', color: '#dc2626' },
  increase: { ar: 'رفع السعر', en: 'Increase Price', color: fareeqChart.green },
  keep: { ar: 'إبقاء', en: 'Keep', color: fareeqChart.blue },
  expand: { ar: 'توسيع التوزيع', en: 'Expand Distribution', color: fareeqHex.amber },
  stock: { ar: 'إضافة للمخزون', en: 'Add to Stock', color: '#6b7280' },
}

function exportCsv(data: ProductComparison[], lang: string) {
  const isAr = lang === 'ar'
  const headers = isAr
    ? ['المنتج', 'الصنف', 'الماركة', 'الوحدة', 'الكمية', 'سعرك', 'متوسط السوق', 'الأرخص', 'الأغلى', 'فجوة %', 'الحالة', 'التوصية', 'الترتيب', 'الفجوة (ريال)', 'أرخص متجر']
    : ['Product', 'Category', 'Brand', 'Unit', 'Pack Size', 'Your Price', 'Market Avg', 'Min', 'Max', 'Gap %', 'Status', 'Action', 'Rank', 'Gap (SAR)', 'Cheapest Store']
  const escCsv = (v: unknown) => {
    const s = String(v ?? '')
    return s.includes(',') || s.includes('"') || s.includes('\n')
      ? `"${s.replace(/"/g, '""')}"`
      : s
  }
  const rows = data.map(d => [
    isAr ? d.title_ar : d.title_en,
    isAr ? d.category_ar : d.category_en,
    isAr ? d.brand_ar : d.brand_en,
    d.attr_unit ?? '',
    d.attr_val ?? '',
    d.your_price ?? 'N/A',
    d.market_avg,
    d.min_price,
    d.max_price,
    d.price_gap_pct,
    d.tag,
    d.recommended_action,
    d.price_rank ? `${d.price_rank} / ${d.price_rank_out_of}` : '',
    d.price_gap_sar != null ? d.price_gap_sar.toFixed(2) : '',
    isAr ? d.cheapest_store_name_ar : d.cheapest_store_name_en,
  ])
  const csv = [headers, ...rows].map(r => r.map(escCsv).join(',')).join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `product_comparison_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function ProductsPageContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { lang, dashboardData, loading, error, forceRefresh, selectedRetailer } = useAppStore()
  const isAr = lang === 'ar'
  const [search, setSearch] = useState('')
  const [filterTag, setFilterTag] = useState('')
  const [filterCat, setFilterCat] = useState('')
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 50

  const comparisons = useMemo(
    () => dashboardData?.comparisons ?? [],
    [dashboardData?.comparisons],
  )
  const fidParam = searchParams.get('fid')
  const highlightFid = fidParam ? parseInt(fidParam, 10) : NaN

  const categories = useMemo(
    () => [...new Set(comparisons.map(c => isAr ? c.category_ar : c.category_en))].sort(),
    [comparisons, isAr],
  )

  const filtered = useMemo(() => {
    if (Number.isFinite(highlightFid) && !search && !filterTag && !filterCat) {
      const hit = comparisons.find(c => c.FID === highlightFid)
      if (hit) return [hit]
    }
    let res = comparisons
    if (search) {
      const q = search.toLowerCase()
      res = res.filter(c =>
        c.title_ar.toLowerCase().includes(q) ||
        c.title_en.toLowerCase().includes(q) ||
        c.brand_ar.toLowerCase().includes(q) ||
        c.brand_en.toLowerCase().includes(q),
      )
    }
    if (filterTag) res = res.filter(c => c.tag === filterTag)
    if (filterCat) res = res.filter(c => (isAr ? c.category_ar : c.category_en) === filterCat)
    return res
  }, [comparisons, highlightFid, search, filterTag, filterCat, isAr])

  const deepLinkOnly = Number.isFinite(highlightFid) && !search && !filterTag && !filterCat

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const effectivePage = deepLinkOnly && filtered.length <= PAGE_SIZE ? 1 : Math.min(page, totalPages)
  const paged = filtered.slice((effectivePage - 1) * PAGE_SIZE, effectivePage * PAGE_SIZE)

  if (!loading && error && !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/products'].ar} title_en={PAGE_TITLES['/products'].en} /><div className="page-shell"><ErrorState lang={lang} onRetry={forceRefresh} /></div></div>
  }

  if (loading || !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/products'].ar} title_en={PAGE_TITLES['/products'].en} /><LoadingOverlay lang={lang} /></div>
  }

  const tagCounts = {
    overpriced: comparisons.filter(c => c.tag === 'overpriced').length,
    risk: comparisons.filter(c => c.tag === 'risk').length,
    competitive: comparisons.filter(c => c.tag === 'competitive').length,
    underpriced: comparisons.filter(c => c.tag === 'underpriced').length,
    opportunity: comparisons.filter(c => c.tag === 'opportunity').length,
    not_stocked: comparisons.filter(c => c.tag === 'not_stocked').length,
  }

  return (
    <div className="animate-fade-in">
      <Topbar title_ar={PAGE_TITLES['/products'].ar} title_en={PAGE_TITLES['/products'].en} />
      <div className="page-shell">

        {deepLinkOnly && (
          <div
            className="flex items-center justify-between gap-3 text-xs rounded-lg border px-3 py-2"
            style={{
              color: 'var(--color-interactive)',
              background: 'var(--color-surface-muted)',
              borderColor: 'var(--color-border)',
            }}
          >
            <span>
              {isAr
                ? 'عرض منتج محدد بالرابط.'
                : 'Showing linked product.'}
            </span>
            <button
              type="button"
              onClick={() => router.replace('/products')}
              className="flex items-center gap-1 font-medium hover:underline shrink-0"
              style={{ color: 'var(--color-interactive)' }}
            >
              <X className="h-3.5 w-3.5" />
              {isAr ? 'عرض كل المنتجات' : 'Show all products'}
            </button>
          </div>
        )}

        {/* Summary chips */}
        <div className="flex flex-wrap gap-2">
          {Object.entries(tagCounts).map(([tag, count]) => (
            <button
              key={tag}
              onClick={() => { setFilterTag(filterTag === tag ? '' : tag); setPage(1) }}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${
                filterTag === tag ? 'ring-2 ring-offset-1 ring-[color:var(--color-interactive)]' : ''
              } tag-${tag}`}
            >
              {count.toLocaleString()}
              <span>{isAr
                ? ({ overpriced: 'مرتفع', risk: 'خطر', competitive: 'تنافسي', underpriced: 'منخفض', opportunity: 'فرصة', not_stocked: 'غير متوفر' } as Record<string, string>)[tag] ?? tag
                : ({ overpriced: 'Overpriced', risk: 'Risk', competitive: 'Competitive', underpriced: 'Underpriced', opportunity: 'Opportunity', not_stocked: 'Not Stocked' } as Record<string, string>)[tag] ?? tag}</span>
            </button>
          ))}
        </div>

        {/* Filters */}
        <Card className="p-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
              <input
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1) }}
                placeholder={isAr ? 'ابحث عن منتج أو ماركة...' : 'Search product or brand...'}
                className="w-full ps-9 pe-3 py-2 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[color:rgba(27,89,248,0.35)]"
              />
            </div>
            <select
              value={filterCat}
              onChange={e => { setFilterCat(e.target.value); setPage(1) }}
              className="px-3 py-2 border border-neutral-200 rounded-lg text-sm text-neutral-700 focus:outline-none focus:ring-2 focus:ring-[color:rgba(27,89,248,0.35)]"
            >
              <option value="">{isAr ? 'كل الأصناف' : 'All Categories'}</option>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => exportCsv(filtered, lang)}>
                <Download className="h-3.5 w-3.5" />
                {isAr ? 'تصدير CSV' : 'Export CSV'}
              </Button>
              {(search || filterTag || filterCat) && (
                <Button variant="ghost" size="sm" onClick={() => { setSearch(''); setFilterTag(''); setFilterCat(''); setPage(1) }}>
                  {isAr ? 'إلغاء الفلاتر' : 'Clear Filters'}
                </Button>
              )}
            </div>
          </div>
          <p className="text-xs text-neutral-400 mt-2">
            {filtered.length.toLocaleString()} / {comparisons.length.toLocaleString()} {isAr ? 'منتج' : 'products'}
          </p>
        </Card>

        {/* Empty state */}
        {paged.length === 0 && !loading && (
          <EmptyState
            title={isAr ? 'لا توجد منتجات تطابق البحث' : 'No products match your search'}
            description={isAr ? 'جرّب تغيير الفلاتر أو مسح البحث لعرض القائمة الكاملة.' : 'Try adjusting filters or clearing the search to see all products.'}
            action={(search || filterTag || filterCat) ? (
              <Button variant="outline" size="sm" onClick={() => { setSearch(''); setFilterTag(''); setFilterCat(''); setPage(1) }}>
                {isAr ? 'مسح الفلاتر' : 'Clear filters'}
              </Button>
            ) : undefined}
          />
        )}

        {/* Table */}
        {paged.length > 0 && (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-neutral-50 border-b border-neutral-100">
                  <th className="sticky start-0 z-10 bg-neutral-50 text-start px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'المنتج' : 'Product'}</th>
                  <th className="text-start px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'الصنف' : 'Category'}</th>
                  <th className="text-end px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'سعرك' : 'Your Price'}</th>
                  <th className="text-end px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'متوسط السوق' : 'Market Avg'}</th>
                  <th className="text-end px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'الأرخص' : 'Lowest'}</th>
                  <th className="text-end px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'فجوة %' : 'Gap %'}</th>
                  <th className="text-center px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'الحالة' : 'Status'}</th>
                  <th className="text-center px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'التوصية' : 'Action'}</th>
                  <th className="text-center px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'الترتيب' : 'Rank'}</th>
                  <th className="text-end px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'الفجوة (ريال)' : 'Gap (SAR)'}</th>
                  <th className="text-start px-4 py-[var(--density-table-cell-y)] font-semibold text-neutral-600 text-xs">{isAr ? 'أرخص متجر' : 'Cheapest Store'}</th>
                </tr>
              </thead>
              <tbody>
                {paged.map(row => {
                  const action = ACTION_MAP[row.recommended_action]
                  const isHi = Number.isFinite(highlightFid) && row.FID === highlightFid
                  return (
                    <tr
                      id={`product-row-${row.FID}`}
                      key={row.FID}
                      className={cn(
                        'border-b border-neutral-50 hover:bg-neutral-50 transition-colors',
                        isHi && 'bg-blue-50 ring-2 ring-inset ring-blue-400',
                      )}
                    >
                      <td
                        className="sticky start-0 z-10 px-4 py-[var(--density-table-cell-y)]"
                        style={{ background: isHi ? '#eff6ff' : 'var(--color-surface)' }}
                      >
                        <p className="font-medium text-neutral-800 leading-tight">
                          {isAr ? row.title_ar : row.title_en}
                          {row.attr_val && row.attr_unit ? (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-100 text-neutral-500 ms-1">{row.attr_val} {row.attr_unit}</span>
                          ) : row.attr_unit ? (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-100 text-neutral-500 ms-1">{row.attr_unit}</span>
                          ) : null}
                        </p>
                        <p className="text-xs text-neutral-400">
                          {isAr ? row.brand_ar : row.brand_en}
                        </p>
                      </td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-xs text-neutral-500">
                        {isAr ? row.category_ar : row.category_en}
                      </td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-end font-semibold tabular-nums text-neutral-900">
                        {row.your_price !== null ? `${row.your_price.toFixed(2)}` : '—'}
                      </td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-end text-neutral-500 tabular-nums">
                        {row.market_avg.toFixed(2)}
                      </td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-end font-medium tabular-nums text-[color:var(--color-trend-up)]">
                        {row.min_price.toFixed(2)}
                      </td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-end">
                        {row.your_price !== null ? (
                          <span className={`font-semibold tabular-nums text-sm ${
                            row.price_gap_pct > 10 ? 'text-red-600' :
                            row.price_gap_pct < -3 ? 'text-[color:var(--color-trend-up)]' : 'text-neutral-600'
                          }`}>
                            {row.price_gap_pct > 0 ? '+' : ''}{row.price_gap_pct.toFixed(1)}%
                          </span>
                        ) : '—'}
                      </td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-center">
                        <TagBadge tag={row.tag} lang={lang} />
                      </td>
                      <td className="px-4 py-[var(--density-table-cell-y)] text-center">
                        <span
                          className="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
                          style={{ backgroundColor: `${action.color}15`, color: action.color }}
                        >
                          {isAr ? action.ar : action.en}
                        </span>
                      </td>

                      {/* Rank */}
                      <td className="px-4 py-[var(--density-table-cell-y)] text-center">
                        {row.price_rank ? (
                          <span
                            className="inline-block px-2 py-0.5 rounded-full text-xs font-semibold tabular-nums"
                            style={
                              row.price_rank === 1
                                ? { background: '#fef9c3', color: '#854d0e' }
                                : row.price_rank === 2
                                ? { background: 'var(--color-surface-muted)', color: 'var(--color-text-secondary)' }
                                : undefined
                            }
                          >
                            {row.price_rank} / {row.price_rank_out_of}
                          </span>
                        ) : '—'}
                      </td>

                      {/* SAR Gap */}
                      <td className="px-4 py-[var(--density-table-cell-y)] text-end text-xs tabular-nums">
                        {row.price_gap_sar != null ? (
                          row.price_gap_sar > 0 ? (
                            <span style={{ color: fareeqChart.coral }} className="font-semibold">
                              ▲ +{row.price_gap_sar.toFixed(2)}
                            </span>
                          ) : row.price_gap_sar < 0 ? (
                            <span style={{ color: fareeqChart.green }} className="font-semibold">
                              {row.price_gap_sar.toFixed(2)}
                            </span>
                          ) : (
                            <span style={{ color: fareeqChart.green }} className="font-semibold">✓</span>
                          )
                        ) : '—'}
                      </td>

                      {/* Cheapest Store */}
                      <td className="px-4 py-[var(--density-table-cell-y)] text-xs text-neutral-600">
                        {(() => {
                          const storeName = isAr ? row.cheapest_store_name_ar : row.cheapest_store_name_en
                          if (!storeName) return '—'
                          const myBrand = isAr ? selectedRetailer?.brand_ar : selectedRetailer?.brand_en
                          const isOurs = myBrand && storeName.toLowerCase() === myBrand.toLowerCase()
                          return isOurs ? (
                            <span style={{ color: fareeqChart.green }} className="font-semibold inline-flex items-center gap-1">
                              {storeName}
                              <span className="text-[10px] px-1 py-0.5 rounded" style={{ background: `${fareeqChart.green}18` }}>
                                {isAr ? '⭐ أنت' : '⭐ You'}
                              </span>
                            </span>
                          ) : storeName
                        })()}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-[var(--density-table-cell-y)] border-t border-neutral-100">
            <p className="text-xs text-neutral-400">
              {isAr ? `الصفحة ${effectivePage} من ${totalPages}` : `Page ${effectivePage} of ${totalPages}`}
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={effectivePage <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>
                {isAr ? 'السابق' : 'Prev'}
              </Button>
              <Button variant="outline" size="sm" disabled={effectivePage >= totalPages} onClick={() => setPage(p => p + 1)}>
                {isAr ? 'التالي' : 'Next'}
              </Button>
            </div>
          </div>
        </Card>
        )}
      </div>
    </div>
  )
}

export default function ProductsPage() {
  return (
    <Suspense fallback={(
      <div>
        <Topbar title_ar={PAGE_TITLES['/products'].ar} title_en={PAGE_TITLES['/products'].en} />
        <LoadingOverlay />
      </div>
    )}
    >
      <ProductsPageContent />
    </Suspense>
  )
}
