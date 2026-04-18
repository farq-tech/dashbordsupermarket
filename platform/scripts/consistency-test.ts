/**
 * Data consistency checks: same invariants the /api/data route relies on.
 * Run from platform/: NODE_ENV=test npx tsx scripts/consistency-test.ts
 */
import { getDataBundle, invalidateCache, type DataSource } from '../lib/dataCache'
import {
  computeRetailerKPIs,
  buildProductComparisons,
  getMarketSummary,
  retailersFromStores,
} from '../lib/kpis'
import { generateRecommendations, generateAlerts } from '../lib/recommendations'

function assertEq(name: string, a: number, b: number) {
  if (a !== b) throw new Error(`${name}: expected ${b}, got ${a}`)
}

async function runSource(source: DataSource) {
  invalidateCache(source)
  const bundle = await getDataBundle(source)
  const { matching, prices, stores } = bundle

  if (matching.length === 0) {
    console.log(`[${source}] SKIP: no matching rows`)
    return
  }

  const retailers = retailersFromStores(stores, { source })
  if (retailers.length === 0) {
    console.log(`[${source}] SKIP: no retailers (stores CSV empty)`)
    return
  }

  const marketStoreCount = Math.max(
    1,
    stores.length,
    new Set(prices.map(p => p.StoreKey)).size,
  )

  const market = getMarketSummary(prices, matching, retailers)

  for (const r of retailers) {
    const kpis = computeRetailerKPIs(r.store_key, prices, matching, retailers)
    const comparisons = buildProductComparisons(r.store_key, prices, matching, marketStoreCount)

    assertEq(`${source} #${r.store_key} comparisons.length`, comparisons.length, matching.length)
    assertEq(`${source} #${r.store_key} kpis.total_products`, kpis.total_products, matching.length)

    const catSum = kpis.categories.reduce((s, c) => s + c.product_count, 0)
    assertEq(`${source} #${r.store_key} Σ category product_count`, catSum, kpis.covered_products)

    const row = market.find(m => m.retailer.store_key === r.store_key)
    if (!row) throw new Error(`[${source}] market summary missing retailer ${r.store_key}`)
    assertEq(`${source} #${r.store_key} market.products`, row.products, kpis.covered_products)

    const expectedCoveragePct =
      matching.length > 0 ? Math.round((kpis.covered_products / matching.length) * 100) : 0
    assertEq(`${source} #${r.store_key} market.coverage_pct`, row.coverage_pct, expectedCoveragePct)
  }

  const r0 = retailers[0]!
  const k0 = computeRetailerKPIs(r0.store_key, prices, matching, retailers)
  const comp0 = buildProductComparisons(r0.store_key, prices, matching, marketStoreCount)
  generateRecommendations(k0, comp0)
  generateAlerts(k0, comp0)

  console.log(`[${source}] OK — ${retailers.length} retailers, ${matching.length} SKUs`)
}

async function main() {
  invalidateCache()
  await runSource('restaurants')
  await runSource('supermarket')
  console.log('Consistency checks passed.')
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
