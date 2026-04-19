/**
 * Fareeq design tokens (SVG kit palette, typography anchors, CTAs).
 * RGB tuples are space-separated for `rgb(var(--token-rgb) / <alpha>)` in Tailwind/CSS.
 * Keep in sync with `app/globals.css` @theme.
 */

export const fareeqHex = {
  primary: '#043434',
  mint: '#83F1B1',
  ink: '#063B37',
  ice: '#D3E7EF',
  purple: '#22162B',
  black: '#040403',
  blue: '#22577A',
  coral: '#EF8354',
  amber: '#FFCA3A',
  glass: '#283939',
  icon: '#0F172A',
} as const

/** `r g b` triplets for CSS variables */
export const fareeqRgb = {
  primary: '4 52 52',
  mint: '131 241 177',
  ink: '6 59 55',
  ice: '211 231 239',
  purple: '34 22 43',
  black: '4 4 3',
  blue: '34 87 122',
  coral: '239 131 84',
  amber: '255 202 58',
  glass: '40 57 57',
  icon: '15 23 42',
} as const

export type FareeqHexKey = keyof typeof fareeqHex

/** Glass CTA: ~21.3px radius on the reference artboard */
export const fareeqRadius = {
  ctaPx: 21.33,
  ctaRem: '1.33rem',
} as const

export const fareeqGlass = {
  fillOpacity: 0.46,
  border: '255 255 255',
  borderOpacity: 0.24,
} as const

/** Chart / KPI / gauge defaults — matches `app/globals.css` semantic aliases */
export const fareeqChart = {
  blue: '#22577a',
  green: '#16a34a',
  coral: '#ef8354',
  orange: '#f97316',
  deepBlue: '#143c54',
  iceTintBg: '#e8f3f7',
  iceTintBorder: '#7eb3c8',
} as const
