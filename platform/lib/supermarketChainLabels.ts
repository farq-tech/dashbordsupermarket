/**
 * Fustog Riyadh compare: StoreKey 1..6 في البحث الحي يقابل ست سلاسل.
 * تُستخدم لعرض اسم السلسلة في الواجهة بدل اسم الفرع (حي/كود مثل الملقا V152).
 * عدّل هنا إذا تغيّر ترتيب المتاجر في مصدر البيانات.
 */
export const SUPERMARKET_CHAIN_BY_STORE_KEY: Record<
  number,
  { brand_ar: string; brand_en: string; logo_letter: string; color: string }
> = {
  1: { brand_ar: 'كارفور', brand_en: 'Carrefour', logo_letter: 'C', color: '#004d99' },
  2: { brand_ar: 'بنده', brand_en: 'Panda', logo_letter: 'P', color: '#E53E3E' },
  3: { brand_ar: 'الدانوب', brand_en: 'Danube', logo_letter: 'D', color: '#1565c0' },
  4: { brand_ar: 'التميمي', brand_en: 'Tamimi Markets', logo_letter: 'T', color: '#2e7d32' },
  5: { brand_ar: 'أسواق العثيم', brand_en: 'Othaim Markets', logo_letter: 'O', color: '#2B6CB0' },
  6: { brand_ar: 'لولو', brand_en: 'LuLu', logo_letter: 'L', color: '#276749' },
}

export function getSupermarketChainDisplay(store_key: number) {
  return SUPERMARKET_CHAIN_BY_STORE_KEY[store_key]
}
