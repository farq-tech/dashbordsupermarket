import type {
  Alert,
  DecisionBrief,
  DecisionItem,
  DecisionPillarScore,
  ProductComparison,
  Recommendation,
  RetailerKPIs,
} from './types'
import { DECISION_POLICY } from '@/config/decisionPolicy'

const W = DECISION_POLICY.scoreWeights

function impactWeight(i: Recommendation['impact']): number {
  return W.recommendationImpactBonus[i === 'high' ? 'high' : i === 'medium' ? 'medium' : 'low']
}

function recScore(r: Recommendation): number {
  const base = 88 - r.priority * W.recommendationPriorityPenalty
  return Math.min(100, Math.max(0, base + impactWeight(r.impact)))
}

function alertScore(a: Alert): number {
  const m = W.alertSeverity
  const f = a.severity === 'high' ? m.high : a.severity === 'medium' ? m.medium : m.low
  return Math.round(100 * f)
}

function marketPositionScore(rank: number, participants: number): number {
  if (participants <= 1) return 100
  const worst = participants - 1
  const pos = rank - 1
  return Math.round(100 - (pos / worst) * 100)
}

/**
 * Builds a single Decision Brief: pillar snapshot (from KPIs) + ranked queue
 * (alerts → recommendations → worst SKU gaps). All numbers trace to bundle-derived inputs.
 */
export function buildDecisionBrief(
  kpis: RetailerKPIs,
  comparisons: ProductComparison[],
  recommendations: Recommendation[],
  alerts: Alert[],
  all_kpis: RetailerKPIs[],
  last_updated: string,
): DecisionBrief {
  const participants = all_kpis.length
  const sorted = [...all_kpis].sort((a, b) => b.performance_score - a.performance_score)
  const market_rank = Math.max(
    1,
    sorted.findIndex(k => k.retailer.store_key === kpis.retailer.store_key) + 1,
  )
  const posScore = marketPositionScore(market_rank, participants)

  const headline_ar =
    market_rank === 1
      ? `مركزك الأول في الأداء بين ${participants} سلاسل في هذه البيانات`
      : market_rank <= 3
        ? `أنت ضمن أعلى 3 سلاسل أداءً (#${market_rank} من ${participants})`
        : `ترتيبك #${market_rank} من ${participants} من حيث درجة الأداء`

  const headline_en =
    market_rank === 1
      ? `You rank #1 on performance score among ${participants} chains in this dataset`
      : market_rank <= 3
        ? `You are in the top 3 chains (#${market_rank} of ${participants})`
        : `Your performance rank is #${market_rank} of ${participants}`

  const subline_ar = `درجة الأداء ${kpis.performance_score.toFixed(1)} · مؤشر التنافسية ${kpis.competitive_index.toFixed(0)}% · التغطية ${kpis.coverage_index.toFixed(0)}% · مؤشر السعر ${kpis.pricing_index.toFixed(1)}%`
  const subline_en = `Performance ${kpis.performance_score.toFixed(1)} · Competitive ${kpis.competitive_index.toFixed(0)}% · Coverage ${kpis.coverage_index.toFixed(0)}% · Pricing index ${kpis.pricing_index.toFixed(1)}%`

  const pillars: DecisionPillarScore[] = [
    {
      key: 'price_competitiveness',
      label_ar: 'التنافسية السعرية',
      label_en: 'Price competitiveness',
      score: Math.round(Math.min(100, Math.max(0, kpis.competitive_index))),
      hint_ar: 'نسبة المنتجات ضمن نطاق تنافسي مقابل الأرخص.',
      hint_en: 'Share of your priced items within a competitive band vs cheapest.',
    },
    {
      key: 'assortment_coverage',
      label_ar: 'تغطية المحفظة',
      label_en: 'Assortment coverage',
      score: Math.round(Math.min(100, Math.max(0, kpis.coverage_index))),
      hint_ar: 'حصة منتجات السوق التي لديك سعر لها.',
      hint_en: 'Share of market-matched SKUs you carry with a price.',
    },
    {
      key: 'market_position',
      label_ar: 'المركز في السوق',
      label_en: 'Market position',
      score: posScore,
      hint_ar: 'مشتق من ترتيب درجة الأداء بين السلاسل في نفس البيانات.',
      hint_en: 'Derived from performance-score rank among chains in this dataset.',
    },
  ]

  const queue: DecisionItem[] = []

  for (const a of alerts) {
    queue.push({
      id: `alert:${a.id}`,
      score: alertScore(a),
      kind: 'alert',
      title_ar: a.title_ar,
      title_en: a.title_en,
      context_ar: a.description_ar,
      context_en: a.description_en,
      impact: a.severity === 'high' ? 'high' : a.severity === 'medium' ? 'medium' : 'low',
      suggested_action_ar: 'مراجعة فورية وربطها بخطة تسعير أو تغطية.',
      suggested_action_en: 'Review now and tie to pricing or assortment follow-up.',
      evidence: [
        {
          label_ar: 'الخطورة',
          label_en: 'Severity',
          value: a.severity,
        },
      ],
      alert_id: a.id,
    })
  }

  for (const r of recommendations) {
    const kind: DecisionItem['kind'] =
      r.type === 'pricing'
        ? 'portfolio_pricing'
        : r.type === 'coverage' || r.type === 'expansion'
          ? 'portfolio_coverage'
          : 'competitive'
    queue.push({
      id: `rec:${r.id}`,
      score: recScore(r),
      kind,
      title_ar: r.title_ar,
      title_en: r.title_en,
      context_ar: r.reason_ar,
      context_en: r.reason_en,
      impact: r.impact,
      suggested_action_ar: r.action_ar,
      suggested_action_en: r.action_en,
      evidence: [
        { label_ar: 'الأولوية', label_en: 'Priority', value: String(r.priority) },
        {
          label_ar: 'النوع',
          label_en: 'Type',
          value: r.type,
        },
        ...(r.value_estimate != null && r.value_estimate > 0
          ? [
              {
                label_ar: 'قيمة مرتبطة (ريال)',
                label_en: 'Related value (SAR)',
                value: String(r.value_estimate),
              },
            ]
          : []),
      ],
      recommendation_id: r.id,
    })
  }

  const overpriced = comparisons
    .filter(c =>
      c.your_price !== null
      && c.price_gap_sar >= DECISION_POLICY.minSkuGapSar
      && (c.tag === 'overpriced' || c.tag === 'risk'),
    )
    .sort((a, b) => b.price_gap_sar - a.price_gap_sar)
  const maxGap = overpriced[0]?.price_gap_sar ?? 1

  for (const c of overpriced.slice(0, DECISION_POLICY.maxSkuDecisions)) {
    const score = maxGap > 0
      ? Math.min(100, Math.round((c.price_gap_sar / maxGap) * W.skuMaxScore))
      : 0
    queue.push({
      id: `sku:${c.FID}`,
      score,
      kind: 'sku_price',
      title_ar: c.title_ar,
      title_en: c.title_en,
      context_ar: `فجوة سعر: ${c.price_gap_sar.toFixed(2)} ريال (${c.price_gap_pct.toFixed(1)}%) مقابل ${c.cheapest_store_name_ar}`,
      context_en: `Gap: ${c.price_gap_sar.toFixed(2)} SAR (${c.price_gap_pct.toFixed(1)}%) vs ${c.cheapest_store_name_en}`,
      impact: c.price_gap_pct >= 20 ? 'high' : c.price_gap_pct >= 12 ? 'medium' : 'low',
      suggested_action_ar: 'ضبط السعر أو مراجعة شرط المورد/العرض.',
      suggested_action_en: 'Adjust price or review supplier/promo terms.',
      evidence: [
        { label_ar: 'سعرك', label_en: 'Your price', value: String(c.your_price) },
        { label_ar: 'أقل سعر', label_en: 'Cheapest', value: String(c.cheapest_price) },
        { label_ar: 'الفئة', label_en: 'Category', value: c.category_en },
      ],
      fid: c.FID,
    })
  }

  queue.sort((a, b) => b.score - a.score)

  const seen = new Set<string>()
  const deduped = queue.filter((item) => {
    if (seen.has(item.id)) return false
    seen.add(item.id)
    return true
  })

  return {
    headline_ar,
    headline_en,
    subline_ar,
    subline_en,
    pillars,
    queue: deduped.slice(0, DECISION_POLICY.maxQueueItems),
    data_as_of: last_updated,
    market_rank,
    market_participants: participants,
  }
}
