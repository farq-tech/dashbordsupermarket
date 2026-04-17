import fs from 'fs'
import path from 'path'
import { parseCsv, num, int } from './csvParser'
import type { DataBundle, StoreRow, PriceRow, MatchingRow } from './types'

const DATA_DIR = path.join(process.cwd(), '..', 'data')
const CACHE_TTL_MS = 60 * 60 * 1000 // 1 hour

interface CacheState {
  data: DataBundle | null
  timestamp: number
  loading: boolean
}

const cache: CacheState = {
  data: null,
  timestamp: 0,
  loading: false,
}

function findLatestFile(pattern: RegExp): string | null {
  try {
    const files = fs.readdirSync(DATA_DIR)
    const matches = files
      .filter(f => pattern.test(f))
      .sort()
      .reverse()
    return matches.length > 0 ? path.join(DATA_DIR, matches[0]) : null
  } catch {
    return null
  }
}

function loadStores(): StoreRow[] {
  const file = findLatestFile(/^fustog_stores_lookup_.*\.csv$/)
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

function loadPrices(): PriceRow[] {
  const file = findLatestFile(/^fustog_prices_enriched_long_.*\.csv$/)
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

function loadMatching(): MatchingRow[] {
  const file = findLatestFile(/^fustog_matching_summary_.*\.csv$/)
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

async function loadData(): Promise<DataBundle> {
  console.log('[DataCache] Loading data from CSV files...')
  const stores = loadStores()
  const prices = loadPrices()
  const matching = loadMatching()
  console.log(`[DataCache] Loaded: ${stores.length} stores, ${prices.length} prices, ${matching.length} products`)
  return {
    stores,
    prices,
    matching,
    last_updated: new Date().toISOString(),
  }
}

export async function getDataBundle(): Promise<DataBundle> {
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
    cache.data = await loadData()
    cache.timestamp = Date.now()
    return cache.data
  } finally {
    cache.loading = false
  }
}

export function invalidateCache(): void {
  cache.data = null
  cache.timestamp = 0
}

export function getCacheInfo(): { last_updated: string | null; age_minutes: number } {
  if (!cache.data) return { last_updated: null, age_minutes: -1 }
  const age = (Date.now() - cache.timestamp) / 60000
  return { last_updated: cache.data.last_updated, age_minutes: Math.round(age) }
}

// Start hourly background refresh
if (typeof process !== 'undefined' && process.env.NODE_ENV !== 'test') {
  setInterval(async () => {
    console.log('[DataCache] Hourly background refresh...')
    invalidateCache()
    await getDataBundle()
  }, CACHE_TTL_MS)
}
