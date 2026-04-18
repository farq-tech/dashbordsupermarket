'use client'

export interface KpiSnapshot {
  at: string
  store_key: number
  source: 'restaurants' | 'supermarket'
  performance_score: number
  competitive_index: number
  coverage_index: number
  pricing_index: number
}

const STORAGE_KEY = 'dash_kpi_snapshots_v1'
const MAX_SNAPSHOTS = 60

function read(): KpiSnapshot[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const p = JSON.parse(raw) as KpiSnapshot[]
    return Array.isArray(p) ? p : []
  } catch {
    return []
  }
}

function write(list: KpiSnapshot[]) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(-MAX_SNAPSHOTS)))
  } catch {
    /* ignore */
  }
}

/** Call after successful dashboard load; dedupes if same minute + same store + same source. */
export function pushKpiSnapshot(s: Omit<KpiSnapshot, 'at'> & { at?: string }) {
  const list = read()
  const at = s.at ?? new Date().toISOString()
  const last = list[list.length - 1]
  if (
    last
    && last.store_key === s.store_key
    && last.source === s.source
    && Math.abs(new Date(last.at).getTime() - new Date(at).getTime()) < 60_000
    && last.performance_score === s.performance_score
  ) {
    return
  }
  list.push({
    at,
    store_key: s.store_key,
    source: s.source,
    performance_score: s.performance_score,
    competitive_index: s.competitive_index,
    coverage_index: s.coverage_index,
    pricing_index: s.pricing_index,
  })
  write(list)
}

export function getKpiSnapshots(): KpiSnapshot[] {
  return read()
}

export function getPreviousSnapshot(current: KpiSnapshot): KpiSnapshot | null {
  const list = read().filter(
    x => x.store_key === current.store_key && x.source === current.source,
  )
  if (list.length < 2) return null
  return list[list.length - 2] ?? null
}
