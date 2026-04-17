import type {
  StoreRow,
  PriceRow,
  MatchingRow,
  Retailer,
  RetailerKPIs,
  CategoryKPI,
  ProductComparison,
} from './types'

export const RETAILERS: Retailer[] = [
  {
    store_key: 2,
    rid: 2,
    name_ar: 'الرياض - العالية بلازا',
    name_en: 'Riyadh - Alia Plaza',
    brand_ar: 'بنده',
    brand_en: 'Panda',
    color: '#E53E3E',
    logo_letter: 'P',
  },
  {
    store_key: 5,
    rid: 5,
    name_ar: 'أسواق العثيم - الرياض',
    name_en: 'Othaim Markets - Riyadh',
    brand_ar: 'أسواق العثيم',
    brand_en: 'Othaim',
    color: '#2B6CB0',
    logo_letter: 'E',
  },
  {
    store_key: 6,
    rid: 6,
    name_ar: 'لولو هايبر ماركت - الرياض',
    name_en: 'LuLu Hyper Market - Riyadh',
    brand_ar: 'لولو',
    brand_en: 'LuLu',
    color: '#276749',
    logo_letter: 'L',
  },
]

export function getRetailerByKey(store_key: number): Retailer | undefined {
  return RETAILERS.find(r => r.store_key === store_key)
}

export function computeRetailerKPIs(
  storeKey: number,
  prices: PriceRow[],
  matching: MatchingRow[],
): RetailerKPIs {
  const retailer = RETAILERS.find(r => r.store_key === storeKey)!
  const myPrices = prices.filter(p => p.StoreKey === storeKey)
  const myPriceMap = new Map<number, number>()
  myPrices.forEach(p => myPriceMap.set(p.FID, p.Price))

  const covered = matching.filter(m => myPriceMap.has(m.FID))
  const total = matching.length

  // Pricing index: my avg price / market avg price * 100
  let sumMy = 0
  let sumMarket = 0
  let count = 0
  let cheapestCount = 0
  let overpricedCount = 0
  let underpricedCount = 0
  let competitiveCount = 0

  covered.forEach(m => {
    const myPrice = myPriceMap.get(m.FID)!
    const marketAvg = (m.min_price + m.max_price) / 2
    sumMy += myPrice
    sumMarket += marketAvg
    count++

    const gapPct = ((myPrice - m.min_price) / m.min_price) * 100
    if (gapPct <= 2) cheapestCount++
    if (gapPct > 10) overpricedCount++
    else if (gapPct < -5) underpricedCount++
    else competitiveCount++
  })

  const avgMy = count > 0 ? sumMy / count : 0
  const avgMarket = count > 0 ? sumMarket / count : 0
  const pricingIndex = avgMarket > 0 ? (avgMy / avgMarket) * 100 : 100

  // Competitive index: % of products where I'm within 5% of cheapest
  const competitiveIndex = count > 0 ? ((cheapestCount + competitiveCount) / count) * 100 : 0

  // Coverage index: % of market products I carry
  const coverageIndex = total > 0 ? (covered.length / total) * 100 : 0

  // Performance score: composite
  const pricingScore = Math.max(0, 100 - Math.abs(pricingIndex - 100) * 2)
  const performanceScore = (pricingScore * 0.3 + competitiveIndex * 0.4 + coverageIndex * 0.3)

  // Categories
  const catMap = new Map<string, { name_ar: string; name_en: string; products: MatchingRow[]; myPrices: number[] }>()
  covered.forEach(m => {
    const key = m.CateguryEN
    if (!catMap.has(key)) {
      catMap.set(key, { name_ar: m.CateguryAR, name_en: m.CateguryEN, products: [], myPrices: [] })
    }
    const entry = catMap.get(key)!
    entry.products.push(m)
    const mp = myPriceMap.get(m.FID)
    if (mp !== undefined) entry.myPrices.push(mp)
  })

  const categories: CategoryKPI[] = Array.from(catMap.values())
    .map(c => {
      const myAvg = c.myPrices.length > 0 ? c.myPrices.reduce((a, b) => a + b, 0) / c.myPrices.length : 0
      const marketAvg = c.products.length > 0
        ? c.products.reduce((a, m) => a + (m.min_price + m.max_price) / 2, 0) / c.products.length
        : 0
      const pi = marketAvg > 0 ? (myAvg / marketAvg) * 100 : 100
      const cheapest = c.products.filter(m => {
        const mp = myPriceMap.get(m.FID)
        return mp !== undefined && ((mp - m.min_price) / m.min_price) * 100 <= 2
      }).length
      const competitive = c.products.filter(m => {
        const mp = myPriceMap.get(m.FID)
        if (!mp) return false
        const gap = ((mp - m.min_price) / m.min_price) * 100
        return gap > 2 && gap <= 10
      }).length
      return {
        name_ar: c.name_ar,
        name_en: c.name_en,
        product_count: c.products.length,
        avg_price: myAvg,
        market_avg_price: marketAvg,
        pricing_index: pi,
        cheapest_count: cheapest,
        competitive_count: competitive,
      }
    })
    .sort((a, b) => b.product_count - a.product_count)

  return {
    retailer,
    pricing_index: Math.round(pricingIndex * 10) / 10,
    competitive_index: Math.round(competitiveIndex * 10) / 10,
    coverage_index: Math.round(coverageIndex * 10) / 10,
    performance_score: Math.round(performanceScore * 10) / 10,
    avg_price: Math.round(avgMy * 100) / 100,
    market_avg_price: Math.round(avgMarket * 100) / 100,
    cheapest_count: cheapestCount,
    overpriced_count: overpricedCount,
    underpriced_count: underpricedCount,
    competitive_count: competitiveCount,
    total_products: total,
    covered_products: covered.length,
    categories,
  }
}

export function buildProductComparisons(
  storeKey: number,
  prices: PriceRow[],
  matching: MatchingRow[],
  totalStores: number = 6,
): ProductComparison[] {
  const myPriceMap = new Map<number, number>()
  prices.filter(p => p.StoreKey === storeKey).forEach(p => myPriceMap.set(p.FID, p.Price))

  // Build all-store price map
  const allPricesMap = new Map<number, Map<number, number>>()
  prices.forEach(p => {
    if (!allPricesMap.has(p.FID)) allPricesMap.set(p.FID, new Map())
    allPricesMap.get(p.FID)!.set(p.StoreKey, p.Price)
  })

  return matching.map(m => {
    const myPrice = myPriceMap.get(m.FID) ?? null
    const storePrices = allPricesMap.get(m.FID) ?? new Map()
    const marketAvg = (m.min_price + m.max_price) / 2

    // Price rank (1 = cheapest)
    const sortedPrices = Array.from(storePrices.values()).sort((a, b) => a - b)
    const priceRank = myPrice !== null ? sortedPrices.indexOf(myPrice) + 1 : -1

    const priceSpreads = Array.from(storePrices.entries())
    const gapPct = myPrice !== null ? ((myPrice - m.min_price) / m.min_price) * 100 : 0
    const gapSar = myPrice !== null ? (myPrice - m.cheapest_price) : 0

    // Tag
    let tag: ProductComparison['tag'] = 'not_stocked'
    let action: ProductComparison['recommended_action'] = 'stock'
    if (myPrice !== null) {
      if (gapPct > 15) { tag = 'overpriced'; action = 'decrease' }
      else if (gapPct > 8) { tag = 'risk'; action = 'decrease' }
      else if (gapPct < -5) { tag = 'underpriced'; action = 'increase' }
      else if (gapPct <= 5) { tag = 'competitive'; action = 'keep' }
      else { tag = 'opportunity'; action = 'keep' }
      if (storePrices.size < totalStores * 0.5) action = 'expand'
    }

    return {
      FID: m.FID,
      title_ar: m.TitleAr,
      title_en: m.TitleEn,
      brand_ar: m.BrandAR,
      brand_en: m.BrandEN,
      category_ar: m.CateguryAR,
      category_en: m.CateguryEN,
      your_price: myPrice,
      market_avg: Math.round(marketAvg * 100) / 100,
      min_price: m.min_price,
      max_price: m.max_price,
      cheapest_price: m.cheapest_price,
      cheapest_store_key: m.cheapest_store_key,
      cheapest_store_name_ar: m.cheapest_store_name_ar,
      cheapest_store_name_en: m.cheapest_store_name_en,
      price_gap_pct: Math.round(gapPct * 10) / 10,
      price_gap_sar: Math.round(gapSar * 100) / 100,
      price_rank: priceRank,
      price_rank_out_of: sortedPrices.length,
      availability_pct: Math.round((storePrices.size / totalStores) * 100),
      stores_with_price_count: storePrices.size,
      tag,
      recommended_action: action,
      prices_by_store: Object.fromEntries(priceSpreads),
    }
  })
}

export function getTopCategories(kpis: RetailerKPIs): CategoryKPI[] {
  return kpis.categories
    .filter(c => c.pricing_index > 0)
    .sort((a, b) => b.product_count - a.product_count)
    .slice(0, 8)
}

export function getMarketSummary(prices: PriceRow[], matching: MatchingRow[]) {
  const retailerStats = RETAILERS.map(r => {
    const rPrices = prices.filter(p => p.StoreKey === r.store_key)
    const rMap = new Map<number, number>()
    rPrices.forEach(p => rMap.set(p.FID, p.Price))
    const covered = matching.filter(m => rMap.has(m.FID))
    const avgPrice = covered.length > 0
      ? covered.reduce((s, m) => s + rMap.get(m.FID)!, 0) / covered.length
      : 0
    const cheapestCount = covered.filter(m => {
      const mp = rMap.get(m.FID)!
      return ((mp - m.min_price) / m.min_price) * 100 <= 2
    }).length

    return {
      retailer: r,
      products: covered.length,
      avg_price: Math.round(avgPrice * 100) / 100,
      cheapest_pct: covered.length > 0 ? Math.round((cheapestCount / covered.length) * 100) : 0,
      coverage_pct: Math.round((covered.length / matching.length) * 100),
    }
  })
  return retailerStats
}
