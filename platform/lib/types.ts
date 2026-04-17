export interface StoreRow {
  store_key: number
  sid: number
  rid: number
  store_name_ar: string
  store_name_en: string
  retailer_brand_ar: string | null
  retailer_brand_en: string | null
  is_integration_ready: boolean
}

export interface PriceRow {
  FID: number
  TitleAr: string
  TitleEn: string
  BrandAR: string
  BrandEN: string
  CateguryAR: string
  CateguryEN: string
  AttrUnit: string
  AttrVal: number | null
  ImageURL: string
  StoreKey: number
  Price: number
  retailer_brand_ar: string | null
  retailer_brand_en: string | null
}

export interface MatchingRow {
  FID: number
  TitleAr: string
  TitleEn: string
  BrandAR: string
  BrandEN: string
  CateguryAR: string
  CateguryEN: string
  min_price: number
  max_price: number
  price_spread: number
  stores_count: number
  price_rows: number
  cheapest_price: number
  cheapest_store_key: number
  cheapest_store_name_ar: string
  cheapest_store_name_en: string
  cheapest_sid: number
  cheapest_rid: number
}

export interface Retailer {
  store_key: number
  rid: number
  name_ar: string
  name_en: string
  brand_ar: string
  brand_en: string
  color: string
  logo_letter: string
}

export interface RetailerKPIs {
  retailer: Retailer
  pricing_index: number
  competitive_index: number
  coverage_index: number
  performance_score: number
  avg_price: number
  market_avg_price: number
  cheapest_count: number
  overpriced_count: number
  underpriced_count: number
  competitive_count: number
  total_products: number
  covered_products: number
  categories: CategoryKPI[]
}

export interface CategoryKPI {
  name_ar: string
  name_en: string
  product_count: number
  avg_price: number
  market_avg_price: number
  pricing_index: number
  cheapest_count: number
  competitive_count: number
}

export interface ProductComparison {
  FID: number
  title_ar: string
  title_en: string
  brand_ar: string
  brand_en: string
  category_ar: string
  category_en: string
  your_price: number | null
  market_avg: number
  min_price: number
  max_price: number
  cheapest_price: number
  cheapest_store_key: number
  cheapest_store_name_ar: string
  cheapest_store_name_en: string
  price_gap_pct: number
  price_gap_sar: number
  price_rank: number
  price_rank_out_of: number
  availability_pct: number
  stores_with_price_count: number
  tag: 'overpriced' | 'underpriced' | 'competitive' | 'opportunity' | 'risk' | 'not_stocked'
  recommended_action: 'increase' | 'decrease' | 'keep' | 'expand' | 'stock'
  prices_by_store: Record<number, number>
}

export interface Recommendation {
  id: string
  title_ar: string
  title_en: string
  impact: 'high' | 'medium' | 'low'
  category_ar: string
  category_en: string
  action_ar: string
  action_en: string
  reason_ar: string
  reason_en: string
  priority: number
  type: 'pricing' | 'coverage' | 'expansion' | 'competitive'
  value_estimate?: number
}

export interface Alert {
  id: string
  type: 'price_change' | 'competitor_move' | 'opportunity' | 'risk'
  title_ar: string
  title_en: string
  description_ar: string
  description_en: string
  severity: 'high' | 'medium' | 'low'
  created_at: string
}

export interface DataBundle {
  stores: StoreRow[]
  prices: PriceRow[]
  matching: MatchingRow[]
  last_updated: string
}
