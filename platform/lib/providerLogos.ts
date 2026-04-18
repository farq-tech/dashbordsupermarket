/** Matches `RetailersSourceMode` in kpis — kept here to avoid circular imports. */
export type LogoSourceMode = 'restaurants' | 'supermarket'

/** Static paths under /public/logos — one per provider (delivery apps + grocery chains). */
export function getRetailerLogoUrl(
  storeKey: number,
  source: LogoSourceMode,
): string | undefined {
  if (source === 'supermarket') {
    const map: Record<number, string> = {
      1: '/logos/carrefour.svg',
      2: '/logos/panda.svg',
      3: '/logos/danube.svg',
      4: '/logos/tamimi.svg',
      5: '/logos/othaim.svg',
      6: '/logos/lulu.svg',
    }
    return map[storeKey]
  }
  const map: Record<number, string> = {
    1: '/logos/official-app.svg',
    2: '/logos/hungerstation.svg',
    3: '/logos/jahez.svg',
    4: '/logos/chefz.svg',
    5: '/logos/keeta.svg',
    6: '/logos/toyou.svg',
    7: '/logos/ninja.svg',
  }
  return map[storeKey]
}
