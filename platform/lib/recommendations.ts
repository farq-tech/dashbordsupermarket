import type { Recommendation, Alert, RetailerKPIs, ProductComparison } from './types'

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function median(values: number[]) {
  if (values.length === 0) return 0
  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
}

function formatSar(n: number) {
  const v = Math.round(n * 100) / 100
  return v.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

export function generateRecommendations(
  kpis: RetailerKPIs,
  comparisons: ProductComparison[],
): Recommendation[] {
  const recs: Recommendation[] = []
  let idCounter = 0
  const id = () => `rec-${++idCounter}`

  const priced = comparisons.filter(c => c.your_price !== null)
  const overpriced = comparisons.filter(c => c.tag === 'overpriced' || c.tag === 'risk')
  const underpriced = comparisons.filter(c => c.tag === 'underpriced')
  const notStocked = comparisons.filter(c => c.tag === 'not_stocked')

  // ---------------------------
  // Pricing intelligence
  // ---------------------------

  // 1) Cheapest competitor by name + estimated SAR impact
  if (overpriced.length > 0) {
    const cheapestNameCounts = new Map<string, { ar: string; en: string; count: number; gapSar: number }>()
    overpriced.forEach(p => {
      const key = `${p.cheapest_store_key}:${p.cheapest_store_name_en}`
      const prev = cheapestNameCounts.get(key) ?? {
        ar: p.cheapest_store_name_ar,
        en: p.cheapest_store_name_en,
        count: 0,
        gapSar: 0,
      }
      prev.count += 1
      prev.gapSar += Math.max(0, p.price_gap_sar)
      cheapestNameCounts.set(key, prev)
    })
    const topCheapest = Array.from(cheapestNameCounts.values()).sort((a, b) => b.count - a.count)[0]
    if (topCheapest) {
      const est = clamp(topCheapest.gapSar * 15, 500, 250000)
      recs.push({
        id: id(),
        title_ar: `${topCheapest.en} الأرخص في ${topCheapest.count} منتج لديك`,
        title_en: `${topCheapest.en} is cheapest in ${topCheapest.count} of your overpriced items`,
        impact: topCheapest.count > 60 ? 'high' : 'medium',
        category_ar: 'تسعير',
        category_en: 'Pricing',
        action_ar: 'مواءمة مع الأرخص',
        action_en: 'Match the cheapest competitor',
        reason_ar: `تقدير فجوة السعر الإجمالية ≈ ${formatSar(topCheapest.gapSar)} ريال. ابدأ بالمنتجات الأعلى فجوة.`,
        reason_en: `Estimated total price gap ≈ ${formatSar(topCheapest.gapSar)} SAR. Start with the biggest gaps.`,
        priority: 1,
        type: 'pricing',
        value_estimate: Math.round(est),
      })
    }
  }

  // 2) Worst single product (by SAR gap, then %)
  const worst = overpriced
    .filter(p => p.your_price !== null)
    .slice()
    .sort((a, b) => (b.price_gap_sar - a.price_gap_sar) || (b.price_gap_pct - a.price_gap_pct))[0]
  if (worst) {
    const est = clamp(Math.max(0, worst.price_gap_sar) * 40, 200, 100000)
    recs.push({
      id: id(),
      title_ar: `أسوأ فجوة سعر: ${worst.title_ar}`,
      title_en: `Worst price gap: ${worst.title_en}`,
      impact: worst.price_gap_pct >= 20 ? 'high' : 'medium',
      category_ar: worst.category_ar,
      category_en: worst.category_en,
      action_ar: 'خفض السعر لهذا المنتج',
      action_en: 'Decrease this product price',
      reason_ar: `أعلى من الأرخص (${worst.cheapest_store_name_en}) بـ ${formatSar(worst.price_gap_sar)} ريال (${worst.price_gap_pct.toFixed(1)}%).`,
      reason_en: `${formatSar(worst.price_gap_sar)} SAR above cheapest (${worst.cheapest_store_name_en}) (${worst.price_gap_pct.toFixed(1)}%).`,
      priority: 1,
      type: 'pricing',
      value_estimate: Math.round(est),
    })
  }

  // 3) Systematic overpriced brands (e.g., Al Marai, Nido...)
  const overpricedByBrand = new Map<string, { ar: string; en: string; items: ProductComparison[] }>()
  overpriced.forEach(p => {
    const key = p.brand_en || p.brand_ar
    if (!key) return
    if (!overpricedByBrand.has(key)) overpricedByBrand.set(key, { ar: p.brand_ar, en: p.brand_en, items: [] })
    overpricedByBrand.get(key)!.items.push(p)
  })
  Array.from(overpricedByBrand.values())
    .filter(b => b.items.length >= 3)
    .map(b => {
      const avgGap = b.items.reduce((s, x) => s + Math.max(0, x.price_gap_pct), 0) / b.items.length
      const gapSar = b.items.reduce((s, x) => s + Math.max(0, x.price_gap_sar), 0)
      return { ...b, avgGap, gapSar }
    })
    .sort((a, b) => (b.avgGap - a.avgGap) || (b.items.length - a.items.length))
    .slice(0, 2)
    .forEach(b => {
      const est = clamp(b.gapSar * 10, 300, 150000)
      recs.push({
        id: id(),
        title_ar: `براند مرتفع السعر بشكل ممنهج: ${b.ar}`,
        title_en: `Systematically overpriced brand: ${b.en}`,
        impact: b.avgGap > 15 ? 'high' : 'medium',
        category_ar: 'تسعير',
        category_en: 'Pricing',
        action_ar: 'مراجعة تسعير البراند',
        action_en: 'Review brand pricing',
        reason_ar: `${b.items.length} منتجات من هذا البراند أعلى من الأرخص بمتوسط ${b.avgGap.toFixed(1)}% (فجوة ≈ ${formatSar(b.gapSar)} ريال).`,
        reason_en: `${b.items.length} items above cheapest by ${b.avgGap.toFixed(1)}% on average (gap ≈ ${formatSar(b.gapSar)} SAR).`,
        priority: 2,
        type: 'pricing',
        value_estimate: Math.round(est),
      })
    })

  // Group overpriced by category
  const overpricedByCat = new Map<string, ProductComparison[]>()
  overpriced.forEach(c => {
    const k = c.category_en
    if (!overpricedByCat.has(k)) overpricedByCat.set(k, [])
    overpricedByCat.get(k)!.push(c)
  })

  overpricedByCat.forEach((products, catEn) => {
    const catAr = products[0].category_ar
    if (products.length >= 3) {
      const avgGap = products.reduce((s, p) => s + p.price_gap_pct, 0) / products.length
      recs.push({
        id: id(),
        title_ar: `خفض أسعار ${products.length} منتج في ${catAr}`,
        title_en: `Reduce prices on ${products.length} products in ${catEn}`,
        impact: avgGap > 15 ? 'high' : 'medium',
        category_ar: catAr,
        category_en: catEn,
        action_ar: 'خفض السعر',
        action_en: 'Decrease Price',
        reason_ar: `أسعارك أعلى من السوق بـ ${avgGap.toFixed(1)}% في المتوسط`,
        reason_en: `Your prices are ${avgGap.toFixed(1)}% above market average`,
        priority: avgGap > 15 ? 1 : 2,
        type: 'pricing',
        value_estimate: products.length * 500,
      })
    }
  })

  // Underpriced - opportunity to increase price
  const underpricedByCat = new Map<string, ProductComparison[]>()
  underpriced.forEach(c => {
    const k = c.category_en
    if (!underpricedByCat.has(k)) underpricedByCat.set(k, [])
    underpricedByCat.get(k)!.push(c)
  })

  underpricedByCat.forEach((products, catEn) => {
    const catAr = products[0].category_ar
    if (products.length >= 2) {
      recs.push({
        id: id(),
        title_ar: `رفع أسعار ${products.length} منتج في ${catAr} (تحت السعر)`,
        title_en: `Increase prices on ${products.length} underpriced products in ${catEn}`,
        impact: 'medium',
        category_ar: catAr,
        category_en: catEn,
        action_ar: 'رفع السعر',
        action_en: 'Increase Price',
        reason_ar: `أسعارك أقل من السوق، فرصة لتحسين الهامش`,
        reason_en: 'Prices below market — margin improvement opportunity',
        priority: 3,
        type: 'pricing',
        value_estimate: products.length * 300,
      })
    }
  })

  // Not stocked - expansion
  const notStockedByCat = new Map<string, ProductComparison[]>()
  notStocked.forEach(c => {
    const k = c.category_en
    if (!notStockedByCat.has(k)) notStockedByCat.set(k, [])
    notStockedByCat.get(k)!.push(c)
  })

  // Coverage intelligence: "Category X: 83% missing vs best competitor"
  // Pick the best-covered competitor per category (by count of priced items) then compute missing %
  const competitorByCat = new Map<string, Map<number, number>>() // cat -> storeKey -> count
  comparisons.forEach(p => {
    const cat = p.category_en
    if (!competitorByCat.has(cat)) competitorByCat.set(cat, new Map())
    const m = competitorByCat.get(cat)!
    Object.entries(p.prices_by_store).forEach(([storeKey, price]) => {
      if (price === undefined || price === null) return
      const sk = Number(storeKey)
      m.set(sk, (m.get(sk) ?? 0) + 1)
    })
  })
  const myByCat = new Map<string, number>()
  priced.forEach(p => myByCat.set(p.category_en, (myByCat.get(p.category_en) ?? 0) + 1))

  const coverageInsights = Array.from(competitorByCat.entries())
    .map(([catEn, storeCounts]) => {
      const catAr = (comparisons.find(x => x.category_en === catEn)?.category_ar) ?? catEn
      const myCount = myByCat.get(catEn) ?? 0
      const best = Array.from(storeCounts.entries())
        .filter(([sk]) => sk !== kpis.retailer.store_key)
        .sort((a, b) => b[1] - a[1])[0]
      if (!best) return null
      const [bestStoreKey, bestCount] = best
      if (bestCount < 10) return null
      const missing = Math.max(0, bestCount - myCount)
      const missingPct = bestCount > 0 ? (missing / bestCount) * 100 : 0
      // Try to infer competitor name from cheapest_store fields in this category
      const sample = comparisons.find(p => p.category_en === catEn && p.cheapest_store_key === bestStoreKey)
      const bestNameEn = sample?.cheapest_store_name_en ?? `Store ${bestStoreKey}`
      const bestNameAr = sample?.cheapest_store_name_ar ?? `Store ${bestStoreKey}`
      return { catEn, catAr, bestStoreKey, bestNameEn, bestNameAr, myCount, bestCount, missingPct, missing }
    })
    .filter(Boolean) as Array<{
      catEn: string; catAr: string; bestStoreKey: number; bestNameEn: string; bestNameAr: string
      myCount: number; bestCount: number; missingPct: number; missing: number
    }>

  coverageInsights
    .sort((a, b) => b.missingPct - a.missingPct)
    .slice(0, 2)
    .forEach(ins => {
      if (ins.missingPct < 35 || ins.missing < 8) return
      const est = clamp(ins.missing * 250, 500, 150000)
      recs.push({
        id: id(),
        title_ar: `${ins.catAr}: ${ins.missingPct.toFixed(0)}% ناقص مقارنة بـ ${ins.bestNameAr}`,
        title_en: `${ins.catEn}: ${ins.missingPct.toFixed(0)}% missing vs ${ins.bestNameEn}`,
        impact: ins.missingPct >= 70 ? 'high' : 'medium',
        category_ar: ins.catAr,
        category_en: ins.catEn,
        action_ar: 'سد فجوة التغطية',
        action_en: 'Close coverage gap',
        reason_ar: `لديك ${ins.myCount} منتج مقابل ${ins.bestCount} لدى ${ins.bestNameAr}. ابدأ بأكثر المنتجات طلباً في هذا التصنيف.`,
        reason_en: `You carry ${ins.myCount} vs ${ins.bestCount} at ${ins.bestNameEn}. Start with the highest-impact SKUs in this category.`,
        priority: 2,
        type: 'coverage',
        value_estimate: Math.round(est),
      })
    })

  // Classic not-stocked recommendations (kept)
  notStockedByCat.forEach((products, catEn) => {
    const catAr = products[0].category_ar
    if (products.length >= 5) {
      recs.push({
        id: id(),
        title_ar: `توسيع التغطية في ${catAr} (${products.length} منتج غير متوفر)`,
        title_en: `Expand coverage in ${catEn} (${products.length} products not stocked)`,
        impact: products.length > 20 ? 'high' : 'medium',
        category_ar: catAr,
        category_en: catEn,
        action_ar: 'إضافة للمخزون',
        action_en: 'Add to Inventory',
        reason_ar: `المنافسون يعرضون هذه المنتجات ولديك غياب في هذا التصنيف`,
        reason_en: 'Competitors carry these products — you have coverage gap',
        priority: products.length > 20 ? 3 : 5,
        type: 'coverage',
        value_estimate: products.length * 200,
      })
    }
  })

  // ---------------------------
  // Competitive intelligence
  // ---------------------------
  // Category rank: "Ranked #6/7 on price"
  const rankByCat = new Map<string, { catAr: string; catEn: string; ranks: number[]; outOf: number[]; cheapest: number }>()
  priced.forEach(p => {
    if (p.price_rank <= 0 || p.price_rank_out_of <= 0) return
    const entry = rankByCat.get(p.category_en) ?? { catAr: p.category_ar, catEn: p.category_en, ranks: [], outOf: [], cheapest: 0 }
    entry.ranks.push(p.price_rank)
    entry.outOf.push(p.price_rank_out_of)
    if (p.price_rank === 1) entry.cheapest += 1
    rankByCat.set(p.category_en, entry)
  })
  const weakestRankCats = Array.from(rankByCat.values())
    .filter(x => x.ranks.length >= 12)
    .map(x => {
      const medRank = median(x.ranks)
      const medOutOf = median(x.outOf)
      const score = medOutOf > 0 ? medRank / medOutOf : 0
      return { ...x, medRank, medOutOf, score }
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 2)

  weakestRankCats.forEach(c => {
    if (c.medOutOf < 4) return
    const impact = c.score >= 0.75 ? 'high' : 'medium'
    recs.push({
      id: id(),
      title_ar: `تنافسية ضعيفة في ${c.catAr}: المرتبة #${Math.round(c.medRank)}/${Math.round(c.medOutOf)} سعرياً`,
      title_en: `Weak competitiveness in ${c.catEn}: ranked #${Math.round(c.medRank)}/${Math.round(c.medOutOf)} on price`,
      impact,
      category_ar: c.catAr,
      category_en: c.catEn,
      action_ar: 'تحسين أسعار سلة مختارة',
      action_en: 'Improve a targeted price basket',
      reason_ar: `التركيز على 10–20 SKU الأكثر تكراراً في الشراء داخل هذا التصنيف يحسن المركز بسرعة.`,
      reason_en: `Target the 10–20 most frequent SKUs in this category to improve rank quickly.`,
      priority: impact === 'high' ? 1 : 3,
      type: 'competitive',
    })
  })

  // Strength callout: "You're cheapest in 59 Milk products"
  const strongest = Array.from(rankByCat.values())
    .filter(x => x.ranks.length >= 12)
    .sort((a, b) => b.cheapest - a.cheapest)[0]
  if (strongest && strongest.cheapest >= 25) {
    recs.push({
      id: id(),
      title_ar: `نقطة قوة: الأرخص في ${strongest.cheapest} منتج ضمن ${strongest.catAr}`,
      title_en: `Strength: cheapest in ${strongest.cheapest} products in ${strongest.catEn}`,
      impact: 'medium',
      category_ar: strongest.catAr,
      category_en: strongest.catEn,
      action_ar: 'استثمار الميزة',
      action_en: 'Capitalize on the advantage',
      reason_ar: `ارفع الظهور/العروض لهذه المجموعة لأنها بالفعل تنافسية سعرياً لديك.`,
      reason_en: `Increase visibility/promotions for these SKUs — you already win on price.`,
      priority: 4,
      type: 'competitive',
    })
  }

  // Low competitive index
  if (kpis.competitive_index < 50) {
    recs.push({
      id: id(),
      title_ar: `مراجعة استراتيجية التسعير (مؤشر تنافسية: ${kpis.competitive_index.toFixed(0)}%)`,
      title_en: `Review pricing strategy (competitive index: ${kpis.competitive_index.toFixed(0)}%)`,
      impact: 'high',
      category_ar: 'عام',
      category_en: 'General',
      action_ar: 'مراجعة شاملة للأسعار',
      action_en: 'Full Pricing Review',
      reason_ar: 'مؤشر التنافسية منخفض مقارنة بالسوق',
      reason_en: 'Competitive index is below market benchmark',
      priority: 1,
      type: 'competitive',
    })
  }

  // Coverage gap / Expansion trigger (always for low-coverage stores)
  if (kpis.coverage_index < 60) {
    recs.push({
      id: id(),
      title_ar: `توسع الآن: تغطية منخفضة (${kpis.coverage_index.toFixed(0)}%)`,
      title_en: `Expand now: low coverage (${kpis.coverage_index.toFixed(0)}%)`,
      impact: 'high',
      category_ar: 'تغطية',
      category_en: 'Coverage',
      action_ar: 'توسيع المحفظة',
      action_en: 'Expand Portfolio',
      reason_ar: `التغطية الحالية ${kpis.coverage_index.toFixed(0)}% — رفعها إلى 55–65% عادةً يعطي أثر سريع على المبيعات والولاء.`,
      reason_en: `Current coverage is ${kpis.coverage_index.toFixed(0)}% — lifting it to ~55–65% typically drives fast gains.`,
      priority: 1,
      type: 'expansion',
    })
  }

  // Keep variety: cap to ~12 pricing, 5 coverage, 4 competitive, 2 expansion
  const byType = (t: Recommendation['type']) => recs.filter(r => r.type === t).sort((a, b) => a.priority - b.priority)
  const limited = [
    ...byType('pricing').slice(0, 12),
    ...byType('coverage').slice(0, 5),
    ...byType('competitive').slice(0, 4),
    ...byType('expansion').slice(0, 2),
  ]
  return limited.sort((a, b) => a.priority - b.priority).slice(0, 25)
}

export function generateAlerts(
  kpis: RetailerKPIs,
  comparisons: ProductComparison[],
): Alert[] {
  const alerts: Alert[] = []
  const now = new Date().toISOString()

  const highRisk = comparisons.filter(c => c.tag === 'risk' || c.tag === 'overpriced')
  const priced = comparisons.filter(c => c.your_price !== null)

  if (highRisk.length > 0) {
    alerts.push({
      id: 'alert-overpriced',
      type: 'risk',
      title_ar: `${highRisk.length} منتج بأسعار مرتفعة عن السوق`,
      title_en: `${highRisk.length} products priced above market`,
      description_ar: 'خطر فقدان العملاء للمنافسين — راجع أولاً المنتجات الأعلى فجوة بالريال.',
      description_en: 'Risk of customer loss — start with the largest SAR gaps.',
      severity: highRisk.length > 50 ? 'high' : 'medium',
      created_at: now,
    })
  }

  const lowCoverage = comparisons.filter(c => c.tag === 'not_stocked')
  if (lowCoverage.length > 100) {
    alerts.push({
      id: 'alert-coverage',
      type: 'opportunity',
      title_ar: `${lowCoverage.length} منتج غير متوفر في متجرك`,
      title_en: `${lowCoverage.length} products not in your store`,
      description_ar: 'فرصة لتوسيع المحفظة — ركّز على التصنيفات التي لديك فيها أعلى نسبة نقص مقارنة بأفضل منافس.',
      description_en: 'Expansion opportunity — focus on categories with highest missing % vs the best competitor.',
      severity: 'medium',
      created_at: now,
    })
  }

  if (kpis.pricing_index > 110) {
    alerts.push({
      id: 'alert-pricing',
      type: 'competitor_move',
      title_ar: `مؤشر الأسعار مرتفع: ${kpis.pricing_index.toFixed(0)}%`,
      title_en: `Pricing index high: ${kpis.pricing_index.toFixed(0)}%`,
      description_ar: 'أسعارك أعلى من متوسط السوق بشكل ملحوظ',
      description_en: 'Your prices are significantly above market average',
      severity: 'high',
      created_at: now,
    })
  }

  // Add 1-2 detail alerts (3-5 total target)
  const worst = highRisk
    .filter(p => p.your_price !== null)
    .slice()
    .sort((a, b) => (b.price_gap_sar - a.price_gap_sar) || (b.price_gap_pct - a.price_gap_pct))[0]
  if (worst) {
    alerts.push({
      id: 'alert-worst-product',
      type: 'price_change',
      title_ar: `أعلى فجوة سعر: ${worst.title_ar}`,
      title_en: `Top price gap: ${worst.title_en}`,
      description_ar: `أعلى من الأرخص (${worst.cheapest_store_name_en}) بـ ${formatSar(worst.price_gap_sar)} ريال (${worst.price_gap_pct.toFixed(1)}%).`,
      description_en: `${formatSar(worst.price_gap_sar)} SAR above cheapest (${worst.cheapest_store_name_en}) (${worst.price_gap_pct.toFixed(1)}%).`,
      severity: worst.price_gap_pct >= 20 ? 'high' : 'medium',
      created_at: now,
    })
  }

  const cheapestWins = priced.filter(p => p.price_rank === 1).length
  if (cheapestWins >= 40) {
    alerts.push({
      id: 'alert-strength',
      type: 'opportunity',
      title_ar: `نقطة قوة: الأرخص في ${cheapestWins} منتج`,
      title_en: `Strength: cheapest in ${cheapestWins} products`,
      description_ar: 'استثمر الميزة عبر إبراز هذه المنتجات في الواجهة والعروض.',
      description_en: 'Capitalize by boosting visibility and bundling/promotions.',
      severity: 'low',
      created_at: now,
    })
  }

  if (kpis.coverage_index < 45) {
    alerts.push({
      id: 'alert-expansion-now',
      type: 'opportunity',
      title_ar: `تغطية منخفضة جداً (${kpis.coverage_index.toFixed(0)}%)`,
      title_en: `Very low coverage (${kpis.coverage_index.toFixed(0)}%)`,
      description_ar: 'ابدأ خطة توسع سريعة: 50 SKU/أسبوع في أعلى 3 تصنيفات نقصاً.',
      description_en: 'Start a fast expansion plan: 50 SKUs/week in the top 3 missing categories.',
      severity: 'high',
      created_at: now,
    })
  }

  return alerts.slice(0, 5)
}
