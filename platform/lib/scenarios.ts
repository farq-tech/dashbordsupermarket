import type { ProductComparison } from './types'

export type ScenarioStrategy = 'match_cheapest' | 'lift_to_market_avg'

export interface ScenarioLineItem {
  fid: number
  title_ar: string
  title_en: string
  amount_sar: number
  your_price: number | null
  reference_price: number
}

export interface ScenarioResult {
  strategy: ScenarioStrategy
  top_n: number
  sku_count: number
  /** Sum of SAR gaps to eliminate (match cheapest) or headroom to market avg (lift). */
  total_amount_sar: number
  line_items: ScenarioLineItem[]
}

/**
 * Top-N overpriced SKUs by gap: total SAR you are above the cheapest competitor.
 */
export function buildMatchCheapestScenario(
  comparisons: ProductComparison[],
  topN: number,
  minGapSar = 0,
): ScenarioResult {
  const candidates = comparisons
    .filter(c =>
      c.your_price !== null
      && c.price_gap_sar > minGapSar
      && (c.tag === 'overpriced' || c.tag === 'risk'),
    )
    .sort((a, b) => b.price_gap_sar - a.price_gap_sar)
    .slice(0, topN)

  const total = candidates.reduce((s, c) => s + c.price_gap_sar, 0)
  return {
    strategy: 'match_cheapest',
    top_n: topN,
    sku_count: candidates.length,
    total_amount_sar: Math.round(total * 100) / 100,
    line_items: candidates.map(c => ({
      fid: c.FID,
      title_ar: c.title_ar,
      title_en: c.title_en,
      amount_sar: Math.round(c.price_gap_sar * 100) / 100,
      your_price: c.your_price,
      reference_price: c.cheapest_price,
    })),
  }
}

/**
 * Top-N underpriced SKUs: sum of (market_avg - your_price) where positive.
 */
export function buildLiftToMarketAvgScenario(
  comparisons: ProductComparison[],
  topN: number,
): ScenarioResult {
  const candidates = comparisons
    .filter(c => c.your_price !== null && c.tag === 'underpriced')
    .map((c) => {
      const headroom = Math.max(0, c.market_avg - c.your_price!)
      return { c, headroom }
    })
    .sort((a, b) => b.headroom - a.headroom)
    .slice(0, topN)

  const total = candidates.reduce((s, x) => s + x.headroom, 0)
  return {
    strategy: 'lift_to_market_avg',
    top_n: topN,
    sku_count: candidates.length,
    total_amount_sar: Math.round(total * 100) / 100,
    line_items: candidates.map(({ c, headroom }) => ({
      fid: c.FID,
      title_ar: c.title_ar,
      title_en: c.title_en,
      amount_sar: Math.round(headroom * 100) / 100,
      your_price: c.your_price,
      reference_price: c.market_avg,
    })),
  }
}
