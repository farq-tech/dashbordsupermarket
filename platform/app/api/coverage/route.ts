import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export const dynamic = 'force-dynamic'

export interface BranchLocation {
  name_ar: string
  name_en: string
  city_en: string
  city_ar: string
  lat: number
  lng: number
}

export interface CityBreakdown {
  city_en: string
  city_ar: string
  count: number
}

export interface SupermarketBrand {
  brand_ar: string
  brand_en: string
  logo: string | null
  total_branches: number
  cities: CityBreakdown[]
  cities_count: number
  with_territory: number
  territory_count: number
  coverage_pct: number
  with_media_pct: number
  branches: BranchLocation[]
}

export interface CoverageData {
  total_grocery_pois: number
  identified_brand_pois: number
  generic_pois: number
  brands: SupermarketBrand[]
}

let cached: CoverageData | null = null

function load(): CoverageData | null {
  if (cached) return cached
  const file = path.join(process.cwd(), 'data', 'supermarket_coverage.json')
  try {
    const raw = fs.readFileSync(file, 'utf-8')
    cached = JSON.parse(raw) as CoverageData
    return cached
  } catch {
    return null
  }
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const brandFilter = searchParams.get('brand')
  const cityFilter = searchParams.get('city')

  const data = load()
  if (!data) {
    return NextResponse.json({ error: 'Coverage data not found' }, { status: 503 })
  }

  if (brandFilter) {
    const match = data.brands.find(
      b => b.brand_en === brandFilter || b.brand_ar === brandFilter,
    )
    if (!match) {
      return NextResponse.json({ error: 'Brand not found' }, { status: 404 })
    }
    return NextResponse.json(match)
  }

  let brands = data.brands
  if (cityFilter) {
    brands = brands
      .filter(b => b.cities.some(c => c.city_en === cityFilter || c.city_ar === cityFilter))
      .map(b => ({
        ...b,
        branches: b.branches.filter(br => br.city_en === cityFilter || br.city_ar === cityFilter),
        total_branches: b.cities.find(c => c.city_en === cityFilter || c.city_ar === cityFilter)?.count ?? 0,
      }))
      .sort((a, b) => b.total_branches - a.total_branches)
  }

  const allCities = new Map<string, { city_ar: string; city_en: string; brands: number; pois: number }>()
  for (const b of data.brands) {
    for (const c of b.cities) {
      const existing = allCities.get(c.city_en)
      if (existing) {
        existing.brands += 1
        existing.pois += c.count
      } else {
        allCities.set(c.city_en, { city_ar: c.city_ar, city_en: c.city_en, brands: 1, pois: c.count })
      }
    }
  }

  return NextResponse.json({
    total_grocery_pois: data.total_grocery_pois,
    identified_brand_pois: data.identified_brand_pois,
    generic_pois: data.generic_pois,
    brands_count: brands.length,
    brands: brands.map(({ branches: _, ...rest }) => rest),
    cities: Array.from(allCities.values()).sort((a, b) => b.pois - a.pois),
  })
}
