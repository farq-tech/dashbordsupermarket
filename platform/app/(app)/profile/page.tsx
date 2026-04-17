'use client'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingOverlay } from '@/components/ui/spinner'
import { SimpleBarChart } from '@/components/charts/BarChartComponent'
import { TrendingUp, TrendingDown, Minus, Award, Target, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

function ScoreGauge({ value, color }: { value: number; color: string }) {
  const angle = (value / 100) * 180
  const rad = (angle - 90) * (Math.PI / 180)
  const r = 70
  const cx = 100
  const cy = 90
  const nx = cx + r * Math.cos(rad)
  const ny = cy + r * Math.sin(rad)
  const strokeDasharray = `${(value / 100) * 220} 220`

  return (
    <svg width="200" height="120" viewBox="0 0 200 120">
      <path d="M20,100 A80,80 0 0,1 180,100" fill="none" stroke="#e4ebe6" strokeWidth="12" strokeLinecap="round" />
      <path
        d="M20,100 A80,80 0 0,1 180,100"
        fill="none"
        stroke={color}
        strokeWidth="12"
        strokeLinecap="round"
        strokeDasharray={strokeDasharray}
        strokeDashoffset="0"
      />
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={color} strokeWidth="2.5" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="5" fill={color} />
      <text x={cx} y={cy + 25} textAnchor="middle" fontSize="22" fontWeight="bold" fill={color}>{value.toFixed(0)}</text>
    </svg>
  )
}

function CompareBar({ label, myVal, competitorVal, myColor, compColor, unit = '' }: {
  label: string; myVal: number; competitorVal: number; myColor: string; compColor: string; unit?: string
}) {
  const max = Math.max(myVal, competitorVal, 1)
  return (
    <div className="space-y-1">
      <p className="text-xs text-neutral-500">{label}</p>
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-neutral-100 rounded-full h-2">
          <div className="h-full rounded-full" style={{ width: `${(myVal / max) * 100}%`, backgroundColor: myColor }} />
        </div>
        <span className="text-xs font-semibold w-16 text-right tabular-nums">{myVal.toFixed(1)}{unit}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-neutral-100 rounded-full h-2">
          <div className="h-full rounded-full" style={{ width: `${(competitorVal / max) * 100}%`, backgroundColor: compColor }} />
        </div>
        <span className="text-xs text-neutral-400 w-16 text-right tabular-nums">{competitorVal.toFixed(1)}{unit}</span>
      </div>
    </div>
  )
}

export default function ProfilePage() {
  const { lang, dashboardData, loading, selectedRetailer } = useAppStore()
  const isAr = lang === 'ar'

  if (loading || !dashboardData) {
    return <div><Topbar title_ar="ملف المتجر" title_en="Store Profile" /><LoadingOverlay /></div>
  }

  const { kpis, all_kpis } = dashboardData
  const competitors = all_kpis.filter(k => k.retailer.store_key !== selectedRetailer?.store_key)
  const topCompetitor = competitors.sort((a, b) => b.performance_score - a.performance_score)[0]
  const myRank = [...all_kpis].sort((a, b) => b.performance_score - a.performance_score)
    .findIndex(k => k.retailer.store_key === selectedRetailer?.store_key) + 1

  // Strength/Weakness analysis
  const strengths: string[] = []
  const weaknesses: string[] = []

  if (kpis.pricing_index < 100) strengths.push(isAr ? 'أسعار تنافسية أقل من المتوسط' : 'Competitive prices below market average')
  else weaknesses.push(isAr ? 'أسعار أعلى من المتوسط' : 'Prices above market average')
  if (kpis.competitive_index > 60) strengths.push(isAr ? 'مؤشر تنافسية قوي' : 'Strong competitive index')
  else weaknesses.push(isAr ? 'تنافسية منخفضة' : 'Low competitiveness')
  if (kpis.coverage_index > 70) strengths.push(isAr ? 'تغطية واسعة للمنتجات' : 'Wide product coverage')
  else weaknesses.push(isAr ? 'فجوات في تغطية المنتجات' : 'Product coverage gaps')
  if (kpis.cheapest_count > kpis.total_products * 0.2) strengths.push(isAr ? 'الأرخص في كثير من المنتجات' : 'Cheapest in many products')

  // Top categories for chart
  const topCatData = kpis.categories.slice(0, 8).map(c => ({
    name: isAr ? c.name_ar.slice(0, 12) : c.name_en.slice(0, 12),
    [isAr ? 'مؤشر السعر' : 'Price Index']: Math.round(c.pricing_index),
  }))

  return (
    <div className="animate-fade-in">
      <Topbar title_ar="ملف المتجر" title_en="Store Profile" />
      <div className="p-6 space-y-6">

        {/* Profile Header */}
        <Card>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div
              className="h-16 w-16 rounded-2xl flex items-center justify-center text-2xl font-bold text-white shadow-lg shrink-0"
              style={{ backgroundColor: selectedRetailer?.color }}
            >
              {selectedRetailer?.logo_letter}
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-neutral-900">
                {isAr ? selectedRetailer?.brand_ar : selectedRetailer?.brand_en}
              </h2>
              <p className="text-neutral-400 text-sm mt-0.5">
                {isAr ? selectedRetailer?.name_ar : selectedRetailer?.name_en}
              </p>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <Badge variant="success">
                  <Award className="h-3 w-3 me-1" />
                  {isAr ? `الترتيب #${myRank}` : `Rank #${myRank}`}
                </Badge>
                <Badge variant="neutral">
                  {kpis.covered_products} {isAr ? 'منتج' : 'products'}
                </Badge>
                <Badge variant="info">
                  {kpis.categories.length} {isAr ? 'صنف' : 'categories'}
                </Badge>
              </div>
            </div>
            <div className="flex flex-col items-center">
              <ScoreGauge value={kpis.performance_score} color={selectedRetailer?.color ?? '#1a5c3a'} />
              <p className="text-xs text-neutral-400 -mt-2">{isAr ? 'نقاط الأداء' : 'Performance Score'}</p>
            </div>
          </div>
        </Card>

        {/* Strengths & Weaknesses */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <CardTitle>{isAr ? 'نقاط القوة' : 'Strengths'}</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-green-700">
                    <span className="text-green-500 mt-0.5">✓</span>
                    {s}
                  </li>
                ))}
                {strengths.length === 0 && (
                  <li className="text-sm text-neutral-400">{isAr ? 'لا توجد نقاط قوة بارزة' : 'No notable strengths'}</li>
                )}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingDown className="h-4 w-4 text-red-500" />
                <CardTitle>{isAr ? 'نقاط الضعف' : 'Weaknesses'}</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {weaknesses.map((w, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-red-600">
                    <span className="text-red-400 mt-0.5">✗</span>
                    {w}
                  </li>
                ))}
                {weaknesses.length === 0 && (
                  <li className="text-sm text-neutral-400">{isAr ? 'أداء ممتاز في جميع المجالات' : 'Excellent performance in all areas'}</li>
                )}
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* You vs Market & Top Competitor */}
        {topCompetitor && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>
                  {isAr
                    ? `أنت مقابل ${topCompetitor.retailer.brand_ar}`
                    : `You vs ${topCompetitor.retailer.brand_en}`}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <CompareBar
                  label={isAr ? 'نقاط الأداء' : 'Performance Score'}
                  myVal={kpis.performance_score}
                  competitorVal={topCompetitor.performance_score}
                  myColor={selectedRetailer?.color ?? '#1a5c3a'}
                  compColor={topCompetitor.retailer.color}
                  unit=""
                />
                <CompareBar
                  label={isAr ? 'مؤشر التنافسية %' : 'Competitive Index %'}
                  myVal={kpis.competitive_index}
                  competitorVal={topCompetitor.competitive_index}
                  myColor={selectedRetailer?.color ?? '#1a5c3a'}
                  compColor={topCompetitor.retailer.color}
                  unit="%"
                />
                <CompareBar
                  label={isAr ? 'تغطية المنتجات %' : 'Coverage %'}
                  myVal={kpis.coverage_index}
                  competitorVal={topCompetitor.coverage_index}
                  myColor={selectedRetailer?.color ?? '#1a5c3a'}
                  compColor={topCompetitor.retailer.color}
                  unit="%"
                />
                <CompareBar
                  label={isAr ? 'متوسط السعر' : 'Avg Price'}
                  myVal={kpis.avg_price}
                  competitorVal={topCompetitor.avg_price}
                  myColor={selectedRetailer?.color ?? '#1a5c3a'}
                  compColor={topCompetitor.retailer.color}
                  unit=" SAR"
                />
                <div className="flex items-center gap-3 text-xs text-neutral-400 pt-1">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: selectedRetailer?.color }} />
                    {isAr ? 'أنت' : 'You'}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: topCompetitor.retailer.color }} />
                    {isAr ? topCompetitor.retailer.brand_ar : topCompetitor.retailer.brand_en}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{isAr ? 'أداء التسعير حسب الصنف' : 'Pricing Index by Category'}</CardTitle>
              </CardHeader>
              <CardContent>
                <SimpleBarChart
                  data={topCatData}
                  dataKey={isAr ? 'مؤشر السعر' : 'Price Index'}
                  colors={topCatData.map(d => {
                    const v = d[isAr ? 'مؤشر السعر' : 'Price Index'] as number
                    return v > 105 ? '#dc2626' : v < 95 ? '#16a34a' : '#2563eb'
                  })}
                  height={240}
                />
              </CardContent>
            </Card>
          </div>
        )}

        {/* CTA */}
        <div className="bg-gradient-to-r from-[#0f3d27] to-[#1a5c3a] rounded-2xl p-6 flex items-center justify-between">
          <div>
            <p className="text-white font-bold text-lg">
              {isAr ? 'ماذا يجب أن تفعل الآن؟' : 'What should you do next?'}
            </p>
            <p className="text-white/70 text-sm mt-1">
              {isAr ? 'عرض التوصيات المخصصة لك' : 'View your personalized recommendations'}
            </p>
          </div>
          <Link
            href="/recommendations"
            className="bg-white text-[#1a5c3a] font-semibold px-5 py-2.5 rounded-xl flex items-center gap-2 hover:bg-neutral-50 transition-colors text-sm"
          >
            <Target className="h-4 w-4" />
            {isAr ? 'عرض التوصيات' : 'View Actions'}
            <ArrowLeft className={`h-4 w-4 ${isAr ? 'rotate-180' : ''}`} />
          </Link>
        </div>

      </div>
    </div>
  )
}
