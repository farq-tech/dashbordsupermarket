export type BusinessPersona = 'supermarket_owner' | 'delivery_platform'

export const PERSONA_STORAGE_KEY = 'dash_business_persona'

export function readStoredPersona(): BusinessPersona | null {
  if (typeof window === 'undefined') return null
  try {
    const v = localStorage.getItem(PERSONA_STORAGE_KEY)
    if (v === 'supermarket_owner' || v === 'delivery_platform') return v
  } catch {
    /* ignore */
  }
  return null
}

export function personaJourneyIntro(persona: BusinessPersona, isAr: boolean): string {
  if (persona === 'supermarket_owner') {
    return isAr
      ? 'كمالك سلسلة: ابدأ من اللوحة، ثم افهم السعر والمنافس، ركّز على المنتجات الحساسة، ثم نفّذ التوصيات.'
      : 'As a retail chain owner: start with the overview, diagnose price vs competitors, drill into sensitive SKUs, then execute recommendations.'
  }
  return isAr
    ? 'كمنصة توصيل: راقب موضعك مقابل السوق، حدد الفجوات السعرية، راجع المنتجات ذات التأثير، ثم حوّل التوصيات إلى قرارات.'
    : 'As a delivery platform: monitor your position vs the market, find pricing gaps, review high-impact SKUs, then turn recommendations into decisions.'
}
