'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useAppStore } from '@/store/useAppStore'
import { Topbar } from '@/components/layout/Topbar'
import { PAGE_TITLES } from '@/lib/navConfig'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingOverlay } from '@/components/ui/spinner'
import { Button } from '@/components/ui/button'
import {
  Scale,
  AlertTriangle,
  Package,
  Target,
  ChevronRight,
  FlaskConical,
  Printer,
  FileDown,
  History,
  UserCircle,
} from 'lucide-react'
import type { DecisionItem } from '@/lib/types'
import type { ScenarioResult } from '@/lib/scenarios'
import { cn } from '@/components/ui/cn'
import { DECISION_POLICY } from '@/config/decisionPolicy'
import {
  getWorkflowEntry,
  setWorkflowEntry,
  exportWorkflowJson,
  type DecisionWorkflowStatus,
} from '@/lib/decisionWorkflow'
import { getKpiSnapshots, getPreviousSnapshot, type KpiSnapshot } from '@/lib/kpiSnapshotHistory'
import { buildDecisionBriefHtml, downloadHtmlFile } from '@/lib/exportDecisionHtml'

const KIND_LABEL = {
  sku_price: { ar: 'منتج', en: 'SKU' },
  portfolio_pricing: { ar: 'تسعير', en: 'Pricing' },
  portfolio_coverage: { ar: 'تغطية', en: 'Coverage' },
  competitive: { ar: 'تنافسية', en: 'Competitive' },
  alert: { ar: 'تنبيه', en: 'Alert' },
} as const

const WF_STATUS: { value: DecisionWorkflowStatus; ar: string; en: string }[] = [
  { value: 'new', ar: 'جديد', en: 'New' },
  { value: 'doing', ar: 'قيد التنفيذ', en: 'In progress' },
  { value: 'done', ar: 'منجز', en: 'Done' },
  { value: 'dropped', ar: 'ملغى', en: 'Dropped' },
]

function pillarColor(score: number) {
  if (score >= 70) return '#1fe08f'
  if (score >= 45) return '#ca8a04'
  return '#ff3e13'
}

export default function DecisionsPage() {
  const { lang, dashboardData, loading, fetchData, selectedRetailer, dataSource } = useAppStore()
  const isAr = lang === 'ar'
  const [kindFilter, setKindFilter] = useState<string>('')
  const [wfTick, setWfTick] = useState(0)
  const [scenarioStrategy, setScenarioStrategy] = useState<'match_cheapest' | 'lift_to_market_avg'>('match_cheapest')
  const [scenarioTopN, setScenarioTopN] = useState<number>(DECISION_POLICY.scenarios.matchCheapestDefaultTopN)
  const [scenario, setScenario] = useState<ScenarioResult | null>(null)
  const [scenarioLoading, setScenarioLoading] = useState(false)

  useEffect(() => {
    if (!dashboardData && !loading) fetchData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const brief = dashboardData?.decision_brief
  const kpiForHistory = dashboardData?.kpis

  const currentSnapshot: KpiSnapshot | null = useMemo(() => {
    if (!kpiForHistory || !selectedRetailer || !dashboardData) return null
    return {
      at: dashboardData.last_updated,
      store_key: selectedRetailer.store_key,
      source: dataSource,
      performance_score: kpiForHistory.performance_score,
      competitive_index: kpiForHistory.competitive_index,
      coverage_index: kpiForHistory.coverage_index,
      pricing_index: kpiForHistory.pricing_index,
    }
  }, [kpiForHistory, selectedRetailer, dataSource, dashboardData])

  const previousSnapshot = currentSnapshot ? getPreviousSnapshot(currentSnapshot) : null

  useEffect(() => {
    if (!selectedRetailer) return
    let cancelled = false
    queueMicrotask(() => {
      if (!cancelled) setScenarioLoading(true)
    })
    const q = new URLSearchParams({
      section: 'scenario',
      store_key: String(selectedRetailer.store_key),
      source: dataSource,
      strategy: scenarioStrategy,
      top_n: String(scenarioTopN),
    })
    fetch(`/api/data?${q}`)
      .then(r => r.json())
      .then((j) => {
        if (!cancelled && j.scenario) setScenario(j.scenario as ScenarioResult)
      })
      .catch(() => {
        if (!cancelled) setScenario(null)
      })
      .finally(() => {
        if (!cancelled) setScenarioLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [selectedRetailer, dataSource, scenarioStrategy, scenarioTopN])

  const filteredQueue = useMemo(() => {
    const q = brief?.queue ?? []
    if (!kindFilter) return q
    return q.filter(i => i.kind === kindFilter)
  }, [brief?.queue, kindFilter])

  const bumpWorkflow = useCallback(() => {
    setWfTick(x => x + 1)
  }, [])

  const handlePrint = () => {
    window.print()
  }

  const handleExportHtml = () => {
    if (!brief) return
    const html = buildDecisionBriefHtml(brief, lang === 'ar' ? 'ar' : 'en')
    downloadHtmlFile(html, `decision_brief_${Date.now()}.html`)
  }

  if (loading || !dashboardData) {
    return (
      <div>
        <Topbar title_ar={PAGE_TITLES['/decisions'].ar} title_en={PAGE_TITLES['/decisions'].en} />
        <LoadingOverlay />
      </div>
    )
  }

  if (!brief) {
    return (
      <div className="animate-fade-in">
        <Topbar title_ar={PAGE_TITLES['/decisions'].ar} title_en={PAGE_TITLES['/decisions'].en} />
        <div className="max-w-lg mx-auto page-shell">
          <Card>
            <CardContent className="pt-6 text-center text-sm text-neutral-600">
              {isAr
                ? 'لا تتوفر طبقة القرار. حدّث البيانات من الشريط العلوي.'
                : 'Decision layer unavailable. Refresh data from the top bar.'}
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      <div className="no-print">
        <Topbar
          title_ar={PAGE_TITLES['/decisions'].ar}
          title_en={PAGE_TITLES['/decisions'].en}
          subtitle_ar="طبقة قرار كاملة: سياسات، سيناريوهات، سير عمل، تاريخ، تصدير"
          subtitle_en="Full decision layer: policy, scenarios, workflow, history, export"
        />
      </div>

      <div id="decision-print-root" className="mx-auto max-w-6xl page-shell">
        {/* Toolbar */}
        <div className="no-print flex flex-wrap gap-2 justify-end">
          <Button variant="outline" size="sm" onClick={handlePrint}>
            <Printer className="h-4 w-4 me-1" />
            {isAr ? 'طباعة / PDF' : 'Print / PDF'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportHtml}>
            <FileDown className="h-4 w-4 me-1" />
            {isAr ? 'تصدير HTML' : 'Export HTML'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const blob = new Blob([exportWorkflowJson()], { type: 'application/json' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `decision_workflow_${Date.now()}.json`
              a.click()
              URL.revokeObjectURL(url)
            }}
          >
            {isAr ? 'تصدير سير العمل' : 'Export workflow JSON'}
          </Button>
          <Link href="/dashboard">
            <Button variant="outline" size="sm">{isAr ? 'اللوحة' : 'Dashboard'}</Button>
          </Link>
        </div>

        {/* Executive snapshot */}
        <Card className="print-avoid-break border-[rgba(27,89,248,0.2)] bg-gradient-to-br from-[var(--color-surface-muted)] to-white">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row md:items-start gap-4">
              <div
                className="h-12 w-12 rounded-2xl flex items-center justify-center shrink-0"
                style={{ background: 'var(--color-interactive)' }}
              >
                <Scale className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-lg font-bold text-neutral-900 leading-snug">
                  {isAr ? brief.headline_ar : brief.headline_en}
                </h2>
                <p className="text-sm text-neutral-600 mt-2 leading-relaxed">
                  {isAr ? brief.subline_ar : brief.subline_en}
                </p>
                <p className="text-xs text-neutral-400 mt-2">
                  {isAr ? 'البيانات:' : 'Data:'}{' '}
                  {new Date(brief.data_as_of).toLocaleString(isAr ? 'ar-SA' : 'en-US')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* History vs previous session */}
        {currentSnapshot && (
          <Card className="no-print">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <History className="h-4 w-4" />
                {isAr ? 'مقارنة مع الجلسة السابقة (نفس المتجر والمصدر)' : 'vs previous session (same store & source)'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!previousSnapshot ? (
                <p className="text-xs text-neutral-500">
                  {isAr ? 'لا يوجد لقطة سابقة بعد — تُحفظ تلقائياً عند كل تحميل ناجح للبيانات.' : 'No prior snapshot yet — saved automatically on each successful data load.'}
                </p>
              ) : (
                <div className="grid grid-cols-2 gap-3 text-xs sm:gap-4 md:grid-cols-4">
                  {([
                    ['performance_score', isAr ? 'الأداء' : 'Performance'],
                    ['competitive_index', isAr ? 'تنافسية' : 'Competitive'],
                    ['coverage_index', isAr ? 'تغطية' : 'Coverage'],
                    ['pricing_index', isAr ? 'مؤشر سعر' : 'Pricing idx'],
                  ] as const).map(([key, label]) => {
                    const cur = currentSnapshot[key]
                    const prev = previousSnapshot[key]
                    const d = cur - prev
                    return (
                      <div key={key} className="p-2 rounded-lg bg-neutral-50 border border-neutral-100">
                        <p className="text-neutral-500">{label}</p>
                        <p className="font-bold tabular-nums text-neutral-900">{cur.toFixed(1)}</p>
                        <p
                          className={d >= 0 ? 'text-[color:var(--color-trend-up)]' : 'text-[color:var(--color-trend-down)]'}
                        >
                          Δ {d >= 0 ? '+' : ''}{d.toFixed(2)}
                        </p>
                      </div>
                    )
                  })}
                </div>
              )}
              <p className="text-[11px] text-neutral-400 mt-2">
                {isAr ? `لقطات محفوظة محلياً: ${getKpiSnapshots().length}` : `Local snapshots: ${getKpiSnapshots().length}`}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Scenarios */}
        <Card className="no-print">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FlaskConical className="h-5 w-5 text-indigo-600" />
              {isAr ? 'سيناريوهات (ما إذا)' : 'What-if scenarios'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-3 items-end">
              <div>
                <label className="text-xs text-neutral-500 block mb-1">{isAr ? 'الاستراتيجية' : 'Strategy'}</label>
                <select
                  value={scenarioStrategy}
                  onChange={e => setScenarioStrategy(e.target.value as 'match_cheapest' | 'lift_to_market_avg')}
                  className="border rounded-lg px-2 py-1.5 text-sm"
                >
                  <option value="match_cheapest">{isAr ? 'مواءمة أعلى N مع الأرخص' : 'Top N match cheapest'}</option>
                  <option value="lift_to_market_avg">{isAr ? 'رفع أعلى N نحو متوسط السوق' : 'Top N lift toward market avg'}</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-neutral-500 block mb-1">N</label>
                <input
                  type="number"
                  min={1}
                  max={DECISION_POLICY.scenarios.maxScenarioLineItems}
                  value={scenarioTopN}
                  onChange={e => setScenarioTopN(Math.max(1, parseInt(e.target.value, 10) || 1))}
                  className="border rounded-lg px-2 py-1.5 text-sm w-24"
                />
              </div>
            </div>
            {scenarioLoading && <p className="text-xs text-neutral-400">{isAr ? 'جاري الحساب…' : 'Computing…'}</p>}
            {scenario && !scenarioLoading && (
              <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4">
                <p className="font-semibold text-indigo-900 text-sm">
                  {scenario.strategy === 'match_cheapest'
                    ? (isAr ? 'مجموع الفجوة لمواءمة الأرخص' : 'Total gap to match cheapest')
                    : (isAr ? 'مجموع الهامش نحو متوسط السوق' : 'Total headroom vs market avg')}
                  :{' '}
                  <span className="tabular-nums">{scenario.total_amount_sar.toLocaleString()} SAR</span>
                </p>
                <p className="text-xs text-indigo-700 mt-1">
                  {isAr ? 'عدد المنتجات في السيناريو:' : 'SKUs in scenario:'} {scenario.sku_count}
                </p>
                <div className="mt-3 max-h-48 overflow-y-auto text-xs space-y-1">
                  {scenario.line_items.slice(0, 20).map(line => (
                    <div key={line.fid} className="flex justify-between gap-2 border-b border-indigo-100 pb-1">
                      <span className="truncate">{isAr ? line.title_ar : line.title_en}</span>
                      <span className="tabular-nums shrink-0">{line.amount_sar.toFixed(2)}</span>
                    </div>
                  ))}
                  {scenario.line_items.length > 20 && (
                    <p className="text-neutral-500">+{scenario.line_items.length - 20} …</p>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Three pillars */}
        <div className="grid grid-cols-1 gap-[var(--density-grid-gap)] md:grid-cols-3">
          {brief.pillars.map(p => (
            <Card key={p.key} className="print-avoid-break">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold flex items-center justify-between gap-2">
                  <span>{isAr ? p.label_ar : p.label_en}</span>
                  <span className="tabular-nums text-lg" style={{ color: pillarColor(p.score) }}>
                    {p.score}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-2 rounded-full bg-neutral-100 overflow-hidden mb-2">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${p.score}%`, backgroundColor: pillarColor(p.score) }}
                  />
                </div>
                <p className="text-xs text-neutral-500 leading-relaxed">
                  {isAr ? p.hint_ar : p.hint_en}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Ranked queue + workflow */}
        <Card className="print-avoid-break">
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" style={{ color: 'var(--color-interactive)' }} />
                {isAr ? 'قائمة القرارات + سير العمل' : 'Decision queue + workflow'}
              </CardTitle>
              <div className="flex flex-wrap gap-1.5 no-print">
                <button
                  type="button"
                  onClick={() => setKindFilter('')}
                  className={cn(
                    'px-2.5 py-1 text-xs rounded-full border transition-colors',
                    !kindFilter
                      ? 'bg-[var(--color-interactive)] text-white border-[var(--color-interactive)]'
                      : 'border-neutral-200 text-neutral-600',
                  )}
                >
                  {isAr ? 'الكل' : 'All'}
                </button>
                {(Object.keys(KIND_LABEL) as DecisionItem['kind'][]).map(k => (
                  <button
                    key={k}
                    type="button"
                    onClick={() => setKindFilter(kindFilter === k ? '' : k)}
                    className={cn(
                      'px-2.5 py-1 text-xs rounded-full border transition-colors',
                      kindFilter === k ? 'bg-neutral-800 text-white' : 'border-neutral-200 text-neutral-600',
                    )}
                  >
                    {isAr ? KIND_LABEL[k].ar : KIND_LABEL[k].en}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <span className="sr-only" aria-hidden>{wfTick}</span>
            <div className="space-y-3">
              {filteredQueue.length === 0 ? (
                <p className="text-sm text-neutral-400 text-center py-8">
                  {isAr ? 'لا عناصر ضمن هذا الفلتر' : 'No items for this filter'}
                </p>
              ) : (
                filteredQueue.map((item, idx) => {
                  const wf = getWorkflowEntry(item.id)
                  return (
                    <div
                      key={item.id}
                      className="flex gap-4 p-4 rounded-xl border border-neutral-100 bg-neutral-50/50 hover:bg-neutral-50 transition-colors"
                    >
                      <div className="font-bold text-neutral-300 w-8 tabular-nums text-right shrink-0">#{idx + 1}</div>
                      <div className="flex-1 min-w-0 space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="neutral" size="sm">
                            {isAr ? KIND_LABEL[item.kind].ar : KIND_LABEL[item.kind].en}
                          </Badge>
                          <Badge
                            variant={item.impact === 'high' ? 'danger' : item.impact === 'medium' ? 'warning' : 'neutral'}
                            size="sm"
                          >
                            {item.impact}
                          </Badge>
                          <span className="text-xs text-neutral-400 tabular-nums ms-auto">
                            score {item.score}
                          </span>
                        </div>
                        <h3 className="font-semibold text-neutral-900 text-sm leading-snug">
                          {isAr ? item.title_ar : item.title_en}
                        </h3>
                        <p className="text-xs text-neutral-600 leading-relaxed">
                          {isAr ? item.context_ar : item.context_en}
                        </p>
                        <div className="flex flex-wrap gap-x-4 gap-y-1">
                          {item.evidence.map((ev, i) => (
                            <span key={i} className="text-[11px] text-neutral-500">
                              <span className="font-medium text-neutral-700">
                                {isAr ? ev.label_ar : ev.label_en}:
                              </span>{' '}
                              {ev.value}
                            </span>
                          ))}
                        </div>
                        <p
                          className="text-xs font-medium pt-1 border-t border-neutral-100"
                          style={{ color: 'var(--color-interactive)' }}
                        >
                          {isAr ? 'مقترح:' : 'Suggested:'}{' '}
                          {isAr ? item.suggested_action_ar : item.suggested_action_en}
                        </p>

                        <div className="no-print flex flex-wrap items-center gap-2 pt-2 border-t border-neutral-100">
                          <UserCircle className="h-4 w-4 text-neutral-400" />
                          <select
                            value={wf?.status ?? 'new'}
                            onChange={(e) => {
                              setWorkflowEntry(item.id, { status: e.target.value as DecisionWorkflowStatus })
                              bumpWorkflow()
                            }}
                            className="text-xs border rounded px-2 py-1"
                          >
                            {WF_STATUS.map(s => (
                              <option key={s.value} value={s.value}>{isAr ? s.ar : s.en}</option>
                            ))}
                          </select>
                          <input
                            type="text"
                            placeholder={isAr ? 'المسؤول' : 'Owner'}
                            defaultValue={wf?.assignee ?? ''}
                            onBlur={(e) => {
                              setWorkflowEntry(item.id, { assignee: e.target.value })
                              bumpWorkflow()
                            }}
                            className="text-xs border rounded px-2 py-1 flex-1 min-w-[120px]"
                          />
                        </div>

                        {item.fid !== undefined && (
                          <Link
                            href={`/products?fid=${item.fid}`}
                            className="no-print inline-flex items-center gap-1 text-xs text-[color:var(--color-interactive)] hover:text-[color:var(--color-interactive-hover)] hover:underline"
                          >
                            <Package className="h-3.5 w-3.5" />
                            {isAr ? 'فتح في المنتجات' : 'Open in Products'}
                          </Link>
                        )}
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </CardContent>
        </Card>

        <div className="no-print flex items-start gap-2 text-xs text-neutral-500 bg-amber-50 border border-amber-100 rounded-lg p-3">
          <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
          <p>
            {isAr
              ? `السياسة: حد أقصى ${DECISION_POLICY.maxQueueItems} عنصراً في الطابور؛ فجوة SKU ≥ ${DECISION_POLICY.minSkuGapSar} ريال. سير العمل يُحفظ في المتصفح فقط.`
              : `Policy: max ${DECISION_POLICY.maxQueueItems} queue items; SKU gap ≥ ${DECISION_POLICY.minSkuGapSar} SAR. Workflow is browser-local only.`}
          </p>
        </div>

        <div className="no-print flex justify-end">
          <Link href="/recommendations">
            <Button size="sm">
              {isAr ? 'التوصيات التفصيلية' : 'Full recommendations'}
              <ChevronRight className="h-4 w-4 ms-1" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
