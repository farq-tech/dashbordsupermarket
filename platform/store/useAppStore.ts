'use client'
import { create } from 'zustand'
import type { RetailerKPIs, ProductComparison, Recommendation, Alert, Retailer } from '@/lib/types'

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
}

interface AppState {
  lang: 'ar' | 'en'
  dir: 'rtl' | 'ltr'
  selectedRetailer: Retailer | null
  dashboardData: DashboardData | null
  loading: boolean
  refreshing: boolean
  error: string | null
  lastUpdated: string | null
  filters: { category: string; brand: string; tag: string }

  setLang: (lang: 'ar' | 'en') => void
  setRetailer: (retailer: Retailer) => void
  setDashboardData: (data: DashboardData) => void
  setLoading: (loading: boolean) => void
  setFilter: (key: 'category' | 'brand' | 'tag', value: string) => void
  resetFilters: () => void
  fetchData: (storeKey?: number) => Promise<void>
  forceRefresh: () => Promise<void>
}

export const RETAILER_LIST: Retailer[] = [
  { store_key: 2, rid: 2, name_ar: 'الرياض - العالية بلازا', name_en: 'Riyadh - Alia Plaza', brand_ar: 'بنده', brand_en: 'Panda', color: '#E53E3E', logo_letter: 'P' },
  { store_key: 5, rid: 5, name_ar: 'أسواق العثيم - الرياض', name_en: 'Othaim Markets - Riyadh', brand_ar: 'أسواق العثيم', brand_en: 'Othaim', color: '#2B6CB0', logo_letter: 'E' },
  { store_key: 6, rid: 6, name_ar: 'لولو هايبر ماركت - الرياض', name_en: 'LuLu Hyper Market - Riyadh', brand_ar: 'لولو', brand_en: 'LuLu', color: '#276749', logo_letter: 'L' },
]

export const useAppStore = create<AppState>((set, get) => ({
  lang: 'ar',
  dir: 'rtl',
  selectedRetailer: RETAILER_LIST[0],
  dashboardData: null,
  loading: false,
  refreshing: false,
  error: null,
  lastUpdated: null,
  filters: { category: '', brand: '', tag: '' },

  setLang: (lang) => {
    set({ lang, dir: lang === 'ar' ? 'rtl' : 'ltr' })
    if (typeof document !== 'undefined') {
      document.documentElement.lang = lang
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
    }
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
    const key = storeKey ?? get().selectedRetailer?.store_key ?? 2
    set({ loading: true, error: null })
    try {
      const res = await fetch(`/api/data?store_key=${key}&section=all`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: DashboardData = await res.json()
      set({ dashboardData: data, loading: false, lastUpdated: data.last_updated })
    } catch (e) {
      set({ loading: false, error: (e as Error).message })
    }
  },

  forceRefresh: async () => {
    set({ refreshing: true })
    try {
      await fetch('/api/refresh', { method: 'POST' })
      await get().fetchData()
    } finally {
      set({ refreshing: false })
    }
  },
}))
