'use client'
import { useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { LoadingOverlay } from '@/components/ui/spinner'
import { Lightbulb, TrendingUp, Map, Zap, Download, CheckCircle } from 'lucide-react'
import type { Recommendation, Alert } from '@/lib/types'

const IMPACT_MAP = {
  high: { ar: 'عالي', en: 'High', color: '#dc2626', bg: '#fee2e2' },
  medium: { ar: 'متوسط', en: 'Medium', color: '#f59e0b', bg: '#fef3c7' },
  low: { ar: 'منخفض', en: 'Low', color: '#6b7280', bg: '#f3f4f6' },
}

const TYPE_MAP = {
  pricing: { ar: 'تسعير', en: 'Pricing', icon: <TrendingUp className="h-4 w-4" />, color: '#1b59f8' },
  coverage: { ar: 'تغطية', en: 'Coverage', icon: <Map className="h-4 w-4" />, color: '#ca8a04' },
  expansion: { ar: 'توسع', en: 'Expansion', icon: <Zap className="h-4 w-4" />, color: '#0f2552' },
  competitive: { ar: 'تنافسية', en: 'Competitive', icon: <Lightbulb className="h-4 w-4" />, color: '#7c3aed' },
}

function RecCard({ rec, lang, onDone }: { rec: Recommendation; lang: string; onDone: (id: string) => void }) {
  const isAr = lang === 'ar'
  const impact = IMPACT_MAP[rec.impact]
  const type = TYPE_MAP[rec.type]

  return (
    <div className="bg-white rounded-xl border border-neutral-100 p-5 hover:shadow-md transition-all animate-fade-in">
      <div className="flex items-start gap-4">
        <div
          className="h-10 w-10 rounded-xl flex items-center justify-center shrink-0"
          style={{ backgroundColor: `${type.color}15`, color: type.color }}
        >
          {type.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="font-semibold text-neutral-900 leading-snug">
              {isAr ? rec.title_ar : rec.title_en}
            </h3>
            <span
              className="inline-block px-2 py-0.5 rounded-full text-xs font-semibold shrink-0"
              style={{ backgroundColor: impact.bg, color: impact.color }}
            >
              {isAr ? impact.ar : impact.en}
            </span>
          </div>
          <p className="text-sm text-neutral-500 leading-relaxed">
            {isAr ? rec.reason_ar : rec.reason_en}
          </p>
          <div className="flex flex-wrap items-center gap-3 mt-3">
            <span
              className="inline-flex items-center gap-1.5 text-xs font-medium"
              style={{ color: type.color }}
            >
              {type.icon}
              {isAr ? type.ar : type.en}
            </span>
            <span className="text-xs text-neutral-400">
              {isAr ? 'الإجراء:' : 'Action:'}{' '}
              <span className="font-medium text-neutral-700">{isAr ? rec.action_ar : rec.action_en}</span>
            </span>
            <Badge variant="neutral">{isAr ? rec.category_ar : rec.category_en}</Badge>
            {rec.value_estimate != null && rec.value_estimate > 0 && (
              <span className="text-xs font-semibold" style={{ color: 'var(--color-interactive)' }}>
                {rec.value_estimate.toLocaleString()} {isAr ? 'ريال (من البيانات)' : 'SAR (from data)'}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={() => onDone(rec.id)}
          className="shrink-0 text-neutral-300 transition-colors mt-0.5 hover:[color:var(--color-interactive)]"
          title={isAr ? 'تم' : 'Mark done'}
        >
          <CheckCircle className="h-5 w-5" />
        </button>
      </div>
    </div>
  )
}

function AlertCard({ alert, lang }: { alert: Alert; lang: string }) {
  const isAr = lang === 'ar'
  const severityColors = {
    high: { bg: '#fee2e2', border: '#fca5a5', text: '#dc2626' },
    medium: { bg: '#fff7ed', border: '#fdba74', text: '#ea580c' },
    low: { bg: '#f2f7ff', border: '#93c5fd', text: '#1b59f8' },
  }
  const colors = severityColors[alert.severity]
  const typeIcons = { price_change: '💰', competitor_move: '⚔️', opportunity: '✨', risk: '⚠️' }

  return (
    <div
      className="rounded-xl p-4 border"
      style={{ backgroundColor: colors.bg, borderColor: colors.border }}
    >
      <div className="flex items-start gap-3">
        <span className="text-xl shrink-0">{typeIcons[alert.type]}</span>
        <div>
          <p className="font-semibold text-sm" style={{ color: colors.text }}>
            {isAr ? alert.title_ar : alert.title_en}
          </p>
          <p className="text-xs text-neutral-600 mt-0.5">
            {isAr ? alert.description_ar : alert.description_en}
          </p>
        </div>
      </div>
    </div>
  )
}

function exportRecs(recs: Recommendation[], lang: string) {
  const isAr = lang === 'ar'
  const headers = isAr
            ? ['العنوان', 'النوع', 'الأثر', 'الصنف', 'الإجراء', 'السبب', 'القيمة (ريال من البيانات)']
    : ['Title', 'Type', 'Impact', 'Category', 'Action', 'Reason', 'Value (SAR from data)']
  const rows = recs.map(r => [
    isAr ? r.title_ar : r.title_en,
    r.type,
    r.impact,
    isAr ? r.category_ar : r.category_en,
    isAr ? r.action_ar : r.action_en,
    isAr ? r.reason_ar : r.reason_en,
    r.value_estimate ?? '',
  ])
  const csv = [headers, ...rows].map(r => r.map(v => `"${v}"`).join(',')).join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `recommendations_${Date.now()}.csv`
  a.click()
}

export default function RecommendationsPage() {
  const { lang, dashboardData, loading } = useAppStore()
  const isAr = lang === 'ar'
  const [filterType, setFilterType] = useState<string>('')
  const [filterImpact, setFilterImpact] = useState<string>('')
  const [done, setDone] = useState<Set<string>>(new Set())
  const [tab, setTab] = useState<'recs' | 'alerts'>('recs')

  const allRecs = dashboardData?.recommendations ?? []
  const alerts = dashboardData?.alerts ?? []

  const filtered = allRecs.filter(r => {
    if (done.has(r.id)) return false
    if (filterType && r.type !== filterType) return false
    if (filterImpact && r.impact !== filterImpact) return false
    return true
  })

  const totalValue = filtered.reduce((s, r) => s + (r.value_estimate ?? 0), 0)

  if (loading || !dashboardData) {
    return <div><Topbar title_ar={PAGE_TITLES['/recommendations'].ar} title_en={PAGE_TITLES['/recommendations'].en} /><LoadingOverlay /></div>
  }

  return (
    <div className="animate-fade-in">
      <Topbar title_ar={PAGE_TITLES['/recommendations'].ar} title_en={PAGE_TITLES['/recommendations'].en} />
      <div className="space-y-4 p-4 sm:space-y-6 sm:p-6">

        {/* Summary */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 md:grid-cols-4">
          <div className="bg-gradient-to-br from-[#0f2552] to-[#1b59f8] rounded-xl p-4 text-white shadow-[var(--shadow-tile)]">
            <p className="text-white/70 text-xs">{isAr ? 'إجمالي التوصيات' : 'Total Recommendations'}</p>
            <p className="text-3xl font-bold mt-1">{filtered.length}</p>
          </div>
          {Object.entries(TYPE_MAP).map(([type, info]) => {
            const count = filtered.filter(r => r.type === type).length
            return (
              <div key={type} className="bg-white rounded-xl border border-neutral-100 p-4">
                <p className="text-xs text-neutral-500 flex items-center gap-1.5">
                  <span style={{ color: info.color }}>{info.icon}</span>
                  {isAr ? info.ar : info.en}
                </p>
                <p className="text-2xl font-bold tabular-nums mt-1" style={{ color: info.color }}>{count}</p>
              </div>
            )
          })}
        </div>

        {totalValue > 0 && (
          <div
            className="flex flex-col gap-3 rounded-xl border px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5"
            style={{
              borderColor: 'var(--color-border)',
              background: 'var(--color-surface-muted)',
            }}
          >
            <p className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              {isAr ? 'مجموع القيم الرقمية (فجوات سعر من البيانات):' : 'Sum of quantified price gaps (from data):'}
              {' '}
              <span style={{ color: 'var(--color-interactive)' }}>
                {totalValue.toLocaleString()} {isAr ? 'ريال' : 'SAR'}
              </span>
            </p>
            <Button variant="ghost" size="sm" onClick={() => exportRecs(filtered, lang)}>
              <Download className="h-3.5 w-3.5" />
              {isAr ? 'تصدير' : 'Export'}
            </Button>
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-neutral-200 gap-1">
          {[
            { key: 'recs', ar: 'التوصيات', en: 'Recommendations', count: filtered.length },
            { key: 'alerts', ar: 'التنبيهات', en: 'Alerts', count: alerts.length },
          ].map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key as 'recs' | 'alerts')}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                tab === t.key
                  ? 'border-[color:var(--color-interactive)] text-[color:var(--color-interactive)]'
                  : 'border-transparent text-neutral-500 hover:text-neutral-700'
              }`}
            >
              {isAr ? t.ar : t.en}
              <span
                className={`text-xs px-1.5 py-0.5 rounded-full ${tab === t.key ? 'bg-[var(--color-surface-hover)]' : 'bg-neutral-100 text-neutral-500'}`}
                style={tab === t.key ? { color: 'var(--color-interactive)' } : undefined}
              >
                {t.count}
              </span>
            </button>
          ))}
        </div>

        {tab === 'recs' && (
          <>
            {/* Filters */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => { setFilterType(''); setFilterImpact('') }}
                className={`px-3 py-1.5 text-xs rounded-full border font-medium transition-colors ${
                  !filterType && !filterImpact
                    ? 'bg-[var(--color-interactive)] text-white border-[var(--color-interactive)]'
                    : 'border-neutral-200 text-neutral-600 hover:bg-neutral-50'
                }`}
              >
                {isAr ? 'الكل' : 'All'} ({allRecs.filter(r => !done.has(r.id)).length})
              </button>
              {Object.entries(TYPE_MAP).map(([type, info]) => (
                <button
                  key={type}
                  onClick={() => setFilterType(filterType === type ? '' : type)}
                  className={`px-3 py-1.5 text-xs rounded-full border font-medium transition-colors ${
                    filterType === type ? 'text-white border-transparent' : 'border-neutral-200 text-neutral-600 hover:bg-neutral-50'
                  }`}
                  style={filterType === type ? { backgroundColor: info.color, borderColor: info.color } : undefined}
                >
                  {isAr ? info.ar : info.en}
                </button>
              ))}
              <div className="border-r border-neutral-200 mx-1" />
              {(['high', 'medium', 'low'] as const).map(impact => (
                <button
                  key={impact}
                  onClick={() => setFilterImpact(filterImpact === impact ? '' : impact)}
                  className={`px-3 py-1.5 text-xs rounded-full border font-medium transition-colors ${
                    filterImpact === impact ? 'text-white border-transparent' : 'border-neutral-200 text-neutral-600 hover:bg-neutral-50'
                  }`}
                  style={filterImpact === impact ? { backgroundColor: IMPACT_MAP[impact].color } : undefined}
                >
                  {isAr ? IMPACT_MAP[impact].ar : IMPACT_MAP[impact].en}
                </button>
              ))}
            </div>

            {/* Recommendations list */}
            {filtered.length === 0 ? (
              <Card className="py-12 text-center">
                <p className="text-neutral-400 text-sm">{isAr ? 'لا توجد توصيات تطابق الفلتر' : 'No recommendations match filter'}</p>
              </Card>
            ) : (
              <div className="space-y-3">
                {filtered.map(rec => (
                  <RecCard
                    key={rec.id}
                    rec={rec}
                    lang={lang}
                    onDone={id => setDone(prev => new Set([...prev, id]))}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {tab === 'alerts' && (
          <div className="space-y-3">
            {alerts.length === 0 ? (
              <Card className="py-12 text-center">
                <p className="text-neutral-400 text-sm">{isAr ? 'لا توجد تنبيهات حالياً' : 'No active alerts'}</p>
              </Card>
            ) : (
              alerts.map(alert => (
                <AlertCard key={alert.id} alert={alert} lang={lang} />
              ))
            )}
          </div>
        )}

      </div>
    </div>
  )
}
