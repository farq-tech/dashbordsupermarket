import fs from 'fs'
import path from 'path'
import { parseCsv, num, int } from './csvParser'
import type { DataBundle, StoreRow, PriceRow, MatchingRow } from './types'

export type DataSource = 'restaurants' | 'supermarket'

function dataDirForSource(source: DataSource): string {
  // Both directories live under platform/
  return source === 'supermarket'
    ? path.join(process.cwd(), 'data_supermarket')
    : path.join(process.cwd(), 'data_restaurants')
}

const CACHE_TTL_MS = 60 * 60 * 1000 // 1 hour

interface CacheState {
  data: DataBundle | null
  timestamp: number
  loading: boolean
}

const caches: Record<DataSource, CacheState> = {
  restaurants: { data: null, timestamp: 0, loading: false },
  supermarket: { data: null, timestamp: 0, loading: false },
}

function findLatestFile(dataDir: string, pattern: RegExp): string | null {
  try {
    const files = fs.readdirSync(dataDir)
    const matches = files
      .filter(f => pattern.test(f))
      .sort()
      .reverse()
    return matches.length > 0 ? path.join(dataDir, matches[0]) : null
  } catch {
    return null
  }
}

function loadStores(dataDir: string): StoreRow[] {
  const file = findLatestFile(dataDir, /^fustog_stores_lookup_.*\.csv$/)
  if (!file) return []
  const text = fs.readFileSync(file, 'utf-8')
  const rows = parseCsv(text)
  return rows.map(r => ({
    store_key: int(r.store_key),
    sid: int(r.sid),
    rid: int(r.rid),
    store_name_ar: r.store_name_ar || '',
    store_name_en: r.store_name_en || '',
    retailer_brand_ar: r.retailer_brand_ar || null,
    retailer_brand_en: r.retailer_brand_en || null,
    is_integration_ready: r.is_integration_ready === 'True',
  }))
}

function loadPrices(dataDir: string): PriceRow[] {
  const file = findLatestFile(dataDir, /^fustog_prices_enriched_long_.*\.csv$/)
  if (!file) return []
  const text = fs.readFileSync(file, 'utf-8')
  const rows = parseCsv(text)
  return rows
    .filter(r => r.FID && r.Price && num(r.Price) > 0)
    .map(r => ({
      FID: int(r.FID),
      TitleAr: r.TitleAr || '',
      TitleEn: r.TitleEn || '',
      BrandAR: r.BrandAR || '',
      BrandEN: r.BrandEN || '',
      CateguryAR: r.CateguryAR || '',
      CateguryEN: r.CateguryEN || '',
      AttrUnit: r.AttrUnit || '',
      AttrVal: r.AttrVal ? num(r.AttrVal) : null,
      ImageURL: r.ImageURL || '',
      StoreKey: int(r.StoreKey),
      Price: num(r.Price),
      retailer_brand_ar: r.retailer_brand_ar || null,
      retailer_brand_en: r.retailer_brand_en || null,
    }))
}

function loadMatching(dataDir: string): MatchingRow[] {
  const file = findLatestFile(dataDir, /^fustog_matching_summary_.*\.csv$/)
  if (!file) return []
  const text = fs.readFileSync(file, 'utf-8')
  const rows = parseCsv(text)
  return rows.map(r => ({
    FID: int(r.FID),
    TitleAr: r.TitleAr || '',
    TitleEn: r.TitleEn || '',
    BrandAR: r.BrandAR || '',
    BrandEN: r.BrandEN || '',
    CateguryAR: r.CateguryAR || '',
    CateguryEN: r.CateguryEN || '',
    min_price: num(r.min_price),
    max_price: num(r.max_price),
    price_spread: num(r.price_spread),
    stores_count: int(r.stores_count),
    price_rows: int(r.price_rows),
    cheapest_price: num(r.cheapest_price),
    cheapest_store_key: int(r.cheapest_store_key),
    cheapest_store_name_ar: r.cheapest_store_name_ar || '',
    cheapest_store_name_en: r.cheapest_store_name_en || '',
    cheapest_sid: int(r.cheapest_sid),
    cheapest_rid: int(r.cheapest_rid),
  }))
}

async function loadData(source: DataSource): Promise<DataBundle> {
  const dataDir = dataDirForSource(source)
  console.log('[DataCache] Loading data from CSV files...')
  const stores = loadStores(dataDir)
  const prices = loadPrices(dataDir)
  const matching = loadMatching(dataDir)
  console.log(`[DataCache] Loaded(${source}): ${stores.length} stores, ${prices.length} prices, ${matching.length} products`)
  return {
    stores,
    prices,
    matching,
    last_updated: new Date().toISOString(),
  }
}

export async function getDataBundle(source: DataSource = 'restaurants'): Promise<DataBundle> {
  const cache = caches[source]
  const now = Date.now()
  if (cache.data && now - cache.timestamp < CACHE_TTL_MS) {
    return cache.data
  }
  if (cache.loading) {
    // Wait for current load to finish
    await new Promise<void>(resolve => {
      const check = setInterval(() => {
        if (!cache.loading) {
          clearInterval(check)
          resolve()
        }
      }, 100)
    })
    return cache.data!
  }

  cache.loading = true
  try {
    cache.data = await loadData(source)
    cache.timestamp = Date.now()
    return cache.data
  } finally {
    cache.loading = false
  }
}

export function invalidateCache(source?: DataSource): void {
  if (!source) {
    ;(Object.keys(caches) as DataSource[]).forEach((s) => {
      caches[s].data = null
      caches[s].timestamp = 0
    })
    return
  }
  caches[source].data = null
  caches[source].timestamp = 0
}

export function getCacheInfo(source: DataSource = 'restaurants'): { last_updated: string | null; age_minutes: number } {
  const cache = caches[source]
  if (!cache.data) return { last_updated: null, age_minutes: -1 }
  const age = (Date.now() - cache.timestamp) / 60000
  return { last_updated: cache.data.last_updated, age_minutes: Math.round(age) }
}

// Start hourly background refresh
if (typeof process !== 'undefined' && process.env.NODE_ENV !== 'test') {
  setInterval(async () => {
    console.log('[DataCache] Hourly background refresh...')
    invalidateCache()
    await getDataBundle('restaurants')
    await getDataBundle('supermarket')
  }, CACHE_TTL_MS)
}
