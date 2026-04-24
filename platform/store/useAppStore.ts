'use client'
import { create } from 'zustand'
import type { RetailerKPIs, ProductComparison, Recommendation, Alert, Retailer, DecisionBrief } from '@/lib/types'
import { pushKpiSnapshot } from '@/lib/kpiSnapshotHistory'
import { PERSONA_STORAGE_KEY, type BusinessPersona } from '@/lib/businessPersona'

const DATA_SOURCE_STORAGE_KEY = 'dash_data_source'
const DENSITY_STORAGE_KEY = 'dash_ui_density'

export type UiDensity = 'comfortable' | 'compact'

export function readStoredDensity(): UiDensity | null {
  if (typeof window === 'undefined') return null
  try {
    const v = localStorage.getItem(DENSITY_STORAGE_KEY)
    if (v === 'comfortable' || v === 'compact') return v
  } catch {
    /* ignore */
  }
  return null
}

export function applyDensityToDom(density: UiDensity) {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.density = density === 'compact' ? 'compact' : ''
}

export function readStoredDataSource(): 'restaurants' | 'supermarket' | null {
  if (typeof window === 'undefined') return null
  try {
    const v = localStorage.getItem(DATA_SOURCE_STORAGE_KEY)
    if (v === 'supermarket' || v === 'restaurants') return v
  } catch {
    /* ignore */
  }
  return null
}

export interface MarketRetailer {
  retailer: Retailer
  products: number
  avg_price: number
  cheapest_pct: number
  coverage_pct: number
}

export interface DashboardData {
  kpis: RetailerKPIs
  comparisons: ProductComparison[]
  recommendations: Recommendation[]
  alerts: Alert[]
  market: MarketRetailer[]
  all_kpis: RetailerKPIs[]
  retailers: Retailer[]
  last_updated: string
  /** Ranked decision queue + pillar snapshot (derived from same bundle). */
  decision_brief?: DecisionBrief
}

interface AppState {
  lang: 'ar' | 'en'
  dir: 'rtl' | 'ltr'
  /** B2B buyer persona — frames copy and journey hints (independent of data source). */
  businessPersona: BusinessPersona
  setBusinessPersona: (persona: BusinessPersona) => void
  dataSource: 'restaurants' | 'supermarket'
  retailers: Retailer[]
  selectedRetailer: Retailer | null
  dashboardData: DashboardData | null
  loading: boolean
  refreshing: boolean
  error: string | null
  lastUpdated: string | null
  filters: { category: string; brand: string; tag: string }
  /** Mobile slide-out navigation (md+ uses fixed sidebar) */
  mobileNavOpen: boolean
  setMobileNavOpen: (open: boolean) => void

  /** Desktop sidebar visibility toggle */
  desktopSidebarHidden: boolean
  setDesktopSidebarHidden: (hidden: boolean) => void

  uiDensity: UiDensity
  setUiDensity: (density: UiDensity) => void

  setLang: (lang: 'ar' | 'en') => void
  setDataSource: (source: 'restaurants' | 'supermarket') => void
  setRetailer: (retailer: Retailer) => void
  setDashboardData: (data: DashboardData) => void
  setLoading: (loading: boolean) => void
  setFilter: (key: 'category' | 'brand' | 'tag', value: string) => void
  resetFilters: () => void
  fetchData: (storeKey?: number) => Promise<void>
  forceRefresh: () => Promise<void>
}

export const useAppStore = create<AppState>((set, get) => ({
  lang: 'ar',
  dir: 'rtl',
  businessPersona: 'supermarket_owner',
  setBusinessPersona: (persona) => {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem(PERSONA_STORAGE_KEY, persona)
      }
    } catch {
      /* ignore */
    }
    set({ businessPersona: persona })
  },
  dataSource: 'restaurants',
  retailers: [],
  selectedRetailer: null,
  dashboardData: null,
  loading: false,
  refreshing: false,
  error: null,
  lastUpdated: null,
  filters: { category: '', brand: '', tag: '' },
  mobileNavOpen: false,
  setMobileNavOpen: open => set({ mobileNavOpen: open }),
  desktopSidebarHidden: false,
  setDesktopSidebarHidden: hidden => set({ desktopSidebarHidden: hidden }),

  uiDensity: 'comfortable',
  setUiDensity: (density) => {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem(DENSITY_STORAGE_KEY, density)
      }
    } catch {
      /* ignore */
    }
    applyDensityToDom(density)
    set({ uiDensity: density })
  },

  setLang: (lang) => {
    set({ lang, dir: lang === 'ar' ? 'rtl' : 'ltr' })
    if (typeof document !== 'undefined') {
      document.documentElement.lang = lang
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
    }
  },

  setDataSource: (source) => {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem(DATA_SOURCE_STORAGE_KEY, source)
      }
    } catch {
      /* ignore */
    }
    set({
      dataSource: source,
      dashboardData: null,
      retailers: [],
      selectedRetailer: null,
      error: null,
    })
    // Re-fetch with the new source
    get().fetchData()
  },

  setRetailer: (retailer) => {
    set({ selectedRetailer: retailer, dashboardData: null })
    get().fetchData(retailer.store_key)
  },

  setDashboardData: (data) => set({ dashboardData: data, lastUpdated: data.last_updated }),
  setLoading: (loading) => set({ loading }),

  setFilter: (key, value) =>
    set(state => ({ filters: { ...state.filters, [key]: value } })),

  resetFilters: () => set({ filters: { category: '', brand: '', tag: '' } }),

  fetchData: async (storeKey?: number) => {
    const key = storeKey ?? get().selectedRetailer?.store_key ?? get().retailers?.[0]?.store_key ?? 1
    const source = get().dataSource
    set({ loading: true, error: null })
    try {
      const res = await fetch(`/api/data?store_key=${key}&section=all&source=${source}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: DashboardData = await res.json()
      const retailers = data.retailers || []
      const selected = retailers.find(r => r.store_key === key) || retailers[0] || null
      if (data.kpis) {
        pushKpiSnapshot({
          store_key: key,
          source,
          performance_score: data.kpis.performance_score,
          competitive_index: data.kpis.competitive_index,
          coverage_index: data.kpis.coverage_index,
          pricing_index: data.kpis.pricing_index,
        })
      }
      set({
        dashboardData: data,
        retailers,
        selectedRetailer: selected,
        loading: false,
        lastUpdated: data.last_updated,
      })
    } catch (e) {
      set({ loading: false, error: (e as Error).message })
    }
  },

  forceRefresh: async () => {
    set({ refreshing: true })
    try {
      const source = get().dataSource
      await fetch(`/api/refresh?source=${source}`, { method: 'POST' })
      await get().fetchData()
    } finally {
      set({ refreshing: false })
    }
  },
}))
