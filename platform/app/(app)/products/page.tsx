'use client'
import { useState, useMemo, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { Card } from '@/components/ui/card'
import { TagBadge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { LoadingOverlay } from '@/components/ui/spinner'
import { Search, Download } from 'lucide-react'
import type { ProductComparison } from '@/lib/types'
import { cn } from '@/components/ui/cn'

const ACTION_MAP: Record<string, { ar: string; en: string; color: string }> = {
  decrease: { ar: 'خفض السعر', en: 'Decrease Price', color: '#dc2626' },
  increase: { ar: 'رفع السعر', en: 'Increase Price', color: '#16a34a' },
  keep: { ar: 'إبقاء', en: 'Keep', color: '#2563eb' },
  expand: { ar: 'توسيع التوزيع', en: 'Expand Distribution', color: '#ca8a04' },
  stock: { ar: 'إضافة للمخزون', en: 'Add to Stock', color: '#6b7280' },
}

function exportCsv(data: ProductComparison[], lang: string) {
  const isAr = lang === 'ar'
  const headers = isAr
    ? ['المنتج', 'الصنف', 'الماركة', 'سعرك', 'متوسط السوق', 'الأرخص', 'الأغلى', 'فجوة %', 'الحالة', 'التوصية']
    : ['Product', 'Category', 'Brand', 'Your Price', 'Market Avg', 'Min', 'Max', 'Gap %', 'Status', 'Action']
  const rows = data.map(d => [
    isAr ? d.title_ar : d.title_en,
    isAr ? d.category_ar : d.category_en,
    isAr ? d.brand_ar : d.brand_en,
    d.your_price ?? 'N/A',
    d.market_avg,
    d.min_price,
    d.max_price,
    d.price_gap_pct,
    d.tag,
    d.recommended_action,
  ])
  const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `product_comparison_${Date.now()}.csv`
  a.click()
}

function ProductsPageContent() {
  const searchParams = useSearchParams()
  const { lang, dashboardData, loading } = useAppStore()
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

  if (loading || !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/products'].ar} title_en={PAGE_TITLES['/products'].en} /><LoadingOverlay /></div>
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
      <div className="space-y-4 p-4 sm:space-y-6 sm:p-6">

        {deepLinkOnly && (
          <p className="text-xs text-blue-700 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
            {isAr
              ? 'عرض منتج مرتبط بالرابط. امسح البحث أو أضف فلاتر لعرض القائمة الكاملة.'
              : 'Showing linked product. Use search or filters to see the full list again.'}
          </p>
        )}

        {/* Summary chips */}
        <div className="flex flex-wrap gap-2">
          {Object.entries(tagCounts).map(([tag, count]) => (
            <button
              key={tag}
              onClick={() => { setFilterTag(filterTag === tag ? '' : tag); setPage(1) }}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${
                filterTag === tag ? 'ring-2 ring-offset-1 ring-[#1a5c3a]' : ''
              } tag-${tag}`}
            >
              {count.toLocaleString()}
              <span>{isAr
                ? { overpriced: 'مرتفع', risk: 'خطر', competitive: 'تنافسي', underpriced: 'منخفض', opportunity: 'فرصة', not_stocked: 'غير متوفر' }[tag]
                : tag}</span>
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
                className="w-full ps-9 pe-3 py-2 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1a5c3a]/30"
              />
            </div>
            <select
              value={filterCat}
              onChange={e => { setFilterCat(e.target.value); setPage(1) }}
              className="px-3 py-2 border border-neutral-200 rounded-lg text-sm text-neutral-700 focus:outline-none focus:ring-2 focus:ring-[#1a5c3a]/30"
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

        {/* Table */}
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-neutral-50 border-b border-neutral-100">
                  <th className="text-start px-4 py-3 font-semibold text-neutral-600 text-xs">{isAr ? 'المنتج' : 'Product'}</th>
                  <th className="text-start px-4 py-3 font-semibold text-neutral-600 text-xs">{isAr ? 'الصنف' : 'Category'}</th>
                  <th className="text-end px-4 py-3 font-semibold text-neutral-600 text-xs">{isAr ? 'سعرك' : 'Your Price'}</th>
                  <th className="text-end px-4 py-3 font-semibold text-neutral-600 text-xs">{isAr ? 'متوسط السوق' : 'Market Avg'}</th>
                  <th className="text-end px-4 py-3 font-semibold text-neutral-600 text-xs">{isAr ? 'الأرخص' : 'Lowest'}</th>
                  <th className="text-end px-4 py-3 font-semibold text-neutral-600 text-xs">{isAr ? 'فجوة %' : 'Gap %'}</th>
                  <th className="text-center px-4 py-3 font-semibold text-neutral-600 text-xs">{isAr ? 'الحالة' : 'Status'}</th>
                  <th className="text-center px-4 py-3 font-semibold text-neutral-600 text-xs">{isAr ? 'التوصية' : 'Action'}</th>
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
                      <td className="px-4 py-3">
                        <p className="font-medium text-neutral-800 leading-tight">
                          {isAr ? row.title_ar : row.title_en}
                        </p>
                        <p className="text-xs text-neutral-400">
                          {isAr ? row.brand_ar : row.brand_en}
                        </p>
                      </td>
                      <td className="px-4 py-3 text-xs text-neutral-500">
                        {isAr ? row.category_ar : row.category_en}
                      </td>
                      <td className="px-4 py-3 text-end font-semibold tabular-nums text-neutral-900">
                        {row.your_price !== null ? `${row.your_price.toFixed(2)}` : '—'}
                      </td>
                      <td className="px-4 py-3 text-end text-neutral-500 tabular-nums">
                        {row.market_avg.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-end text-green-600 font-medium tabular-nums">
                        {row.min_price.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-end">
                        {row.your_price !== null ? (
                          <span className={`font-semibold tabular-nums text-sm ${
                            row.price_gap_pct > 10 ? 'text-red-600' :
                            row.price_gap_pct < -3 ? 'text-green-600' : 'text-neutral-600'
                          }`}>
                            {row.price_gap_pct > 0 ? '+' : ''}{row.price_gap_pct.toFixed(1)}%
                          </span>
                        ) : '—'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <TagBadge tag={row.tag} lang={lang} />
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
                          style={{ backgroundColor: `${action.color}15`, color: action.color }}
                        >
                          {isAr ? action.ar : action.en}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-neutral-100">
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
