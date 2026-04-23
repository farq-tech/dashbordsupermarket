import { NextResponse } from 'next/server'
import { getDataBundle, getCacheInfo, type DataSource } from '@/lib/dataCache'
import { computeRetailerKPIs, buildProductComparisons, getMarketSummary, retailersFromStores } from '@/lib/kpis'
import { generateRecommendations, generateAlerts } from '@/lib/recommendations'
import { buildDecisionBrief } from '@/lib/decisionLayer'
import { buildMatchCheapestScenario, buildLiftToMarketAvgScenario } from '@/lib/scenarios'
import { DECISION_POLICY } from '@/config/decisionPolicy'

export const dynamic = 'force-dynamic'

function parseSource(raw: string | null): DataSource {
  if (raw === 'supermarket' || raw === 'restaurants') return raw
  return 'restaurants'
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const storeKey = parseInt(searchParams.get('store_key') || '2', 10)
    const section = searchParams.get('section') || 'all'
    const source = parseSource(searchParams.get('source'))

    const bundle = await getDataBundle(source)
    const cacheInfoRaw = getCacheInfo(source)
    const { last_updated, ...cacheInfo } = cacheInfoRaw
    void last_updated
    const retailers = retailersFromStores(bundle.stores, { source })
    const marketStoreCount = Math.max(
      1,
      bundle.stores.length,
      new Set(bundle.prices.map(p => p.StoreKey)).size,
    )

    if (retailers.length === 0 && section !== 'stores') {
      return NextResponse.json(
        {
          error: 'No store data loaded. Add fustog_stores_lookup_*.csv under the data folder for this source.',
          retailers: [],
          last_updated: bundle.last_updated,
          ...cacheInfo,
        },
        { status: 503 },
      )
    }

    if (section === 'stores') {
      return NextResponse.json({ stores: bundle.stores, ...cacheInfo })
    }

    if (section === 'comparisons') {
      const comparisons = buildProductComparisons(storeKey, bundle.prices, bundle.matching, marketStoreCount)
      const cat = searchParams.get('category')
      const brand = searchParams.get('brand')
      const tag = searchParams.get('tag')
      let filtered = comparisons
      if (cat) filtered = filtered.filter(c => c.category_en === cat || c.category_ar === cat)
      if (brand) filtered = filtered.filter(c => c.brand_en === brand || c.brand_ar === brand)
      if (tag) filtered = filtered.filter(c => c.tag === tag)
      return NextResponse.json({ comparisons: filtered.slice(0, 300), total: filtered.length, ...cacheInfo })
    }

    if (section === 'kpis') {
      const kpis = computeRetailerKPIs(storeKey, bundle.prices, bundle.matching, retailers)
      return NextResponse.json({ kpis, ...cacheInfo })
    }

    if (section === 'market') {
      const marketSummary = getMarketSummary(bundle.prices, bundle.matching, retailers)
      return NextResponse.json({ market: marketSummary, ...cacheInfo })
    }

    if (section === 'recommendations') {
      const kpis = computeRetailerKPIs(storeKey, bundle.prices, bundle.matching, retailers)
      const comparisons = buildProductComparisons(storeKey, bundle.prices, bundle.matching, marketStoreCount)
      const recs = generateRecommendations(kpis, comparisons)
      const alerts = generateAlerts(kpis, comparisons)
      return NextResponse.json({ recommendations: recs, alerts, ...cacheInfo })
    }

    if (section === 'scenario') {
      const strategy = searchParams.get('strategy') === 'lift_to_market_avg' ? 'lift_to_market_avg' : 'match_cheapest'
      const topN = Math.min(
        DECISION_POLICY.scenarios.maxScenarioLineItems,
        Math.max(1, parseInt(searchParams.get('top_n') || String(DECISION_POLICY.scenarios.matchCheapestDefaultTopN), 10)),
      )
      const comparisons = buildProductComparisons(storeKey, bundle.prices, bundle.matching, marketStoreCount)
      const scenario =
        strategy === 'lift_to_market_avg'
          ? buildLiftToMarketAvgScenario(comparisons, topN)
          : buildMatchCheapestScenario(comparisons, topN, DECISION_POLICY.minSkuGapSar)
      return NextResponse.json({ scenario, ...cacheInfo })
    }

    if (section === 'decisions') {
      const kpis = computeRetailerKPIs(storeKey, bundle.prices, bundle.matching, retailers)
      const comparisons = buildProductComparisons(storeKey, bundle.prices, bundle.matching, marketStoreCount)
      const recs = generateRecommendations(kpis, comparisons)
      const alerts = generateAlerts(kpis, comparisons)
      const allRetailersKpis = retailers.map(r =>
        computeRetailerKPIs(r.store_key, bundle.prices, bundle.matching, retailers),
      )
      const decision_brief = buildDecisionBrief(
        kpis,
        comparisons,
        recs,
        alerts,
        allRetailersKpis,
        bundle.last_updated,
      )
      return NextResponse.json({ decision_brief, ...cacheInfo })
    }

    // Full dashboard data
    const kpis = computeRetailerKPIs(storeKey, bundle.prices, bundle.matching, retailers)
    const comparisons = buildProductComparisons(storeKey, bundle.prices, bundle.matching, marketStoreCount)
    const recs = generateRecommendations(kpis, comparisons)
    const alerts = generateAlerts(kpis, comparisons)
    const marketSummary = getMarketSummary(bundle.prices, bundle.matching, retailers)
    const allRetailersKpis = retailers.map(r =>
      computeRetailerKPIs(r.store_key, bundle.prices, bundle.matching, retailers)
    )

    const decision_brief = buildDecisionBrief(
      kpis,
      comparisons,
      recs,
      alerts,
      allRetailersKpis,
      bundle.last_updated,
    )

    return NextResponse.json({
      kpis,
      comparisons,
      recommendations: recs,
      alerts,
      market: marketSummary,
      all_kpis: allRetailersKpis,
      retailers,
      last_updated: bundle.last_updated,
      decision_brief,
      ...cacheInfo,
    })
  } catch (error) {
    console.error('[API/data] Error:', error)
    return NextResponse.json({ error: 'Failed to load data' }, { status: 500 })
  }
}
