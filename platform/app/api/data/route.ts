import { NextResponse } from 'next/server'
import { getDataBundle, getCacheInfo, type DataSource } from '@/lib/dataCache'
import { computeRetailerKPIs, buildProductComparisons, getMarketSummary, RETAILERS, retailersFromStores } from '@/lib/kpis'
import { generateRecommendations, generateAlerts } from '@/lib/recommendations'

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
    const { last_updated: _cache_last_updated, ...cacheInfo } = getCacheInfo(source)
    const retailers = retailersFromStores(bundle.stores)

    if (section === 'stores') {
      return NextResponse.json({ stores: bundle.stores, ...cacheInfo })
    }

    if (section === 'comparisons') {
      const comparisons = buildProductComparisons(storeKey, bundle.prices, bundle.matching)
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
      const comparisons = buildProductComparisons(storeKey, bundle.prices, bundle.matching)
      const recs = generateRecommendations(kpis, comparisons)
      const alerts = generateAlerts(kpis, comparisons)
      return NextResponse.json({ recommendations: recs, alerts, ...cacheInfo })
    }

    // Full dashboard data
    const kpis = computeRetailerKPIs(storeKey, bundle.prices, bundle.matching, retailers)
    const comparisons = buildProductComparisons(storeKey, bundle.prices, bundle.matching)
    const recs = generateRecommendations(kpis, comparisons)
    const alerts = generateAlerts(kpis, comparisons)
    const marketSummary = getMarketSummary(bundle.prices, bundle.matching, retailers)
    const allRetailersKpis = retailers.map(r =>
      computeRetailerKPIs(r.store_key, bundle.prices, bundle.matching, retailers)
    )

    return NextResponse.json({
      kpis,
      comparisons: comparisons.slice(0, 200),
      recommendations: recs,
      alerts,
      market: marketSummary,
      all_kpis: allRetailersKpis,
      retailers,
      last_updated: bundle.last_updated,
      ...cacheInfo,
    })
  } catch (error) {
    console.error('[API/data] Error:', error)
    return NextResponse.json({ error: 'Failed to load data' }, { status: 500 })
  }
}
