/**
 * Reference layouts from the Fareeq v10 SVG kit (`public/design/fareeq-v10`).
 * Copy kit assets into that folder to enable previews; URLs stay valid with an empty base path.
 */

function publicFareeqV10Url(filename: string): string {
  const raw = process.env.NEXT_PUBLIC_BASE_PATH ?? ''
  const trimmed = raw.replace(/\/$/, '')
  const prefix = trimmed ? `${trimmed}/` : '/'
  return `${prefix}design/fareeq-v10/${encodeURIComponent(filename)}`
}

const filenames = {
  locationEnabling: 'Location Enabling.svg',
  locationEnabling1: 'Location Enabling-1.svg',
  locationSet: 'Location Set.svg',
  locationSet1: 'Location Set-1.svg',
  masonryLayout: 'Masonry Layout.svg',
  /** Filename matches design export (typo: Subscribtion) */
  premiumSubscription: 'Premium Subscribtion.svg',
  priceLists: 'Price Lists.svg',
  priceLists1: 'Price Lists-1.svg',
  screen: 'Screen.svg',
  screen1: 'Screen-1.svg',
  screen2: 'Screen-2.svg',
  screen3: 'Screen-3.svg',
  scrolledState: 'Scrolled State.svg',
  section1: 'Section 1.svg',
  wip: 'WIP.svg',
  wishlist: 'Wishlist.svg',
  wishlist1: 'Wishlist-1.svg',
  category: 'Category.svg',
  desktop: 'Desktop.svg',
  filters: 'Filters.svg',
  filters1: 'Filters-1.svg',
  loading: 'Loading.svg',
  loading1: 'Loading-1.svg',
} as const

export type FareeqV10Key = keyof typeof filenames

export function fareeqV10Asset(key: FareeqV10Key): string {
  return publicFareeqV10Url(filenames[key])
}

/** All public URLs; useful for galleries or Storybook. */
export const fareeqV10Assets: Record<FareeqV10Key, string> = Object.fromEntries(
  (Object.keys(filenames) as FareeqV10Key[]).map((k) => [k, fareeqV10Asset(k)]),
) as Record<FareeqV10Key, string>
