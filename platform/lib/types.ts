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
  /** Path under /public, e.g. /logos/jahez.svg — shown when set */
  logo_url?: string
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
  overpriced_count: number
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
  price_spread?: number   // max_price - min_price across all stores
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
  attr_unit?: string   // e.g. "جرام", "مل", "كجم"
  attr_val?: string    // e.g. "500", "1000", "6"
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
  competitor_hint_ar?: string
  competitor_hint_en?: string
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

export interface DecisionEvidence {
  label_ar: string
  label_en: string
  value: string
}

export interface DecisionItem {
  id: string
  score: number
  kind: 'sku_price' | 'portfolio_pricing' | 'portfolio_coverage' | 'competitive' | 'alert'
  title_ar: string
  title_en: string
  context_ar: string
  context_en: string
  impact: 'high' | 'medium' | 'low'
  suggested_action_ar: string
  suggested_action_en: string
  evidence: DecisionEvidence[]
  fid?: number
  recommendation_id?: string
  alert_id?: string
}

export interface DecisionPillarScore {
  key: 'price_competitiveness' | 'assortment_coverage' | 'market_position'
  label_ar: string
  label_en: string
  score: number
  hint_ar: string
  hint_en: string
}

export interface DecisionBrief {
  headline_ar: string
  headline_en: string
  subline_ar: string
  subline_en: string
  pillars: DecisionPillarScore[]
  queue: DecisionItem[]
  data_as_of: string
  market_rank: number
  market_participants: number
}

export interface DataBundle {
  stores: StoreRow[]
  prices: PriceRow[]
  matching: MatchingRow[]
  last_updated: string
}
