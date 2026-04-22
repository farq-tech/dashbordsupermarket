/** Matches `RetailersSourceMode` in kpis — kept here to avoid circular imports. */
export type LogoSourceMode = 'restaurants' | 'supermarket'

/**
 * Static paths under /public/logos — one per provider (delivery apps + grocery chains).
 * Raster/WebP assets live alongside legacy SVGs; swap filenames here when updating artwork.
 */
export function getRetailerLogoUrl(
  storeKey: number,
  source: LogoSourceMode,
): string | undefined {
  if (source === 'supermarket') {
    const map: Record<number, string> = {
      1: '/logos/farq.png',
      2: '/logos/panda.jpg',
      3: '/logos/danube.jpg',
      4: '/logos/tamimi.png',
      5: '/logos/othaim.jpg',
      6: '/logos/lulu.png',
    }
    return map[storeKey]
  }
  const map: Record<number, string> = {
    1: '/logos/farq.png',
    2: '/logos/hungerstation.png',
    3: '/logos/jahez.png',
    4: '/logos/chefz.png',
    5: '/logos/keeta.png',
    6: '/logos/toyou.jpg',
    7: '/logos/ninja.png',
  }
  return map[storeKey]
}
