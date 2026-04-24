import type { NavSectionId } from '@/lib/navConfig'

/**
 * All UX copy that must diverge between retail chains (supermarket data)
 * and delivery platforms (restaurants / apps data).
 */
export type ExperienceMode = 'supermarket' | 'restaurants'

export interface JourneyStepCopy {
  title_ar: string
  title_en: string
  desc_ar: string
  desc_en: string
}

export interface ExperienceBundle {
  /** Sidebar product name under logo */
  productTitle_ar: string
  productTitle_en: string
  tagline_ar: string
  tagline_en: string
  /** Journey card main heading */
  journeyHeading_ar: string
  journeyHeading_en: string
  journeySub_ar: string
  journeySub_en: string
  /** Intro paragraph under journey heading */
  journeyIntro_ar: string
  journeyIntro_en: string
  /** Four steps — same routes, different framing */
  steps: JourneyStepCopy[]
  /** Quick link labels (hrefs fixed in component) */
  quick1_ar: string
  quick1_en: string
  quick2_ar: string
  quick2_en: string
  quick3_ar: string
  quick3_en: string
  /** Topbar hint under phase pill */
  topbarFlow_ar: string
  topbarFlow_en: string
  /** Data source toggle — short hint under buttons */
  dataSourceHint_ar: string
  dataSourceHint_en: string
  /** Sidebar section hints (same structure as NAV_SECTIONS ids) */
  navHints: Record<NavSectionId, { ar: string; en: string }>
}

const RETAIL: ExperienceBundle = {
  productTitle_ar: 'ذكاء السلاسل التجارية',
  productTitle_en: 'Chain retail intelligence',
  tagline_ar: 'فروع، رفوف، ومقارنة الأسعار مع السلاسل المجاورة',
  tagline_en: 'Stores, shelves, and price benchmarks vs nearby chains',
  journeyHeading_ar: 'مسار مالك السلسلة',
  journeyHeading_en: 'Retail chain workflow',
  journeySub_ar: '٤ خطوات — من الرف إلى القرار',
  journeySub_en: '4 steps — shelf to decision',
  journeyIntro_ar:
    'ركّز على تشكيلتك، هوامش الفروع، والمنافسين المباشرين على نفس الرف. ابدأ باللوحة، ثم التسعير والمنافسين، ثم المنتجات الحساسة، وأخيراً التوصيات.',
  journeyIntro_en:
    'Focus on your assortment, branch-level margins, and head-to-head chains on the same shelf. Overview → pricing & competitors → sensitive SKUs → recommendations.',
  steps: [
    {
      title_ar: 'لوحة السلسلة',
      title_en: 'Chain overview',
      desc_ar: 'الأداء، الترتيب في السوق، والتنبيهات',
      desc_en: 'Performance, market rank, and alerts',
    },
    {
      title_ar: 'الرف والمنافس',
      title_en: 'Shelf & rivals',
      desc_ar: 'التسعير، التغطية، المنافسين، والأقسام',
      desc_en: 'Pricing, coverage, competitors, categories',
    },
    {
      title_ar: 'تنفيذ على الأرض',
      title_en: 'Store execution',
      desc_ar: 'توصيات تشغيلية وقرارات قابلة للمتابعة',
      desc_en: 'Operational recs and trackable decisions',
    },
    {
      title_ar: 'هوية السلسلة',
      title_en: 'Chain profile',
      desc_ar: 'العلامة ومصدر بيانات التجزئة',
      desc_en: 'Brand & retail data source',
    },
  ],
  quick1_ar: 'مقارنة مباشرة مع منافس',
  quick1_en: 'Head-to-head vs a chain',
  quick2_ar: 'حساسية المنتجات على الرف',
  quick2_en: 'Shelf-sensitive SKUs',
  quick3_ar: 'قرارات الفروع',
  quick3_en: 'Branch-ready decisions',
  topbarFlow_ar: 'وضع التجزئة: رف — سعر — منافس — تنفيذ',
  topbarFlow_en: 'Retail mode: shelf → price → rival → execute',
  dataSourceHint_ar: 'بيانات مقارنة بين سلاسل السوبرماركت',
  dataSourceHint_en: 'Supermarket chain comparison data',
  navHints: {
    overview: {
      ar: '١ — أداء السلسلة والترتيب أمام السلاسل الأخرى',
      en: '1 — Chain performance vs other retail brands',
    },
    diagnosis: {
      ar: '٢ — الرف: السعر، التغطية، والمنافس على نفس الفئة',
      en: '2 — Shelf: price, coverage, and same-category rivals',
    },
    action: {
      ar: '٣ — قرارات الفروع والتسعير التشغيلي',
      en: '3 — Branch-level pricing & ops decisions',
    },
    context: {
      ar: '٤ — هوية السلسلة وإعدادات العرض',
      en: '4 — Chain identity & display settings',
    },
  },
}

const DELIVERY: ExperienceBundle = {
  productTitle_ar: 'ذكاء منصات التوصيل',
  productTitle_en: 'Delivery marketplace intelligence',
  tagline_ar: 'سلة المستخدم، العمولة، والمنافسة بين تطبيقات التوصيل',
  tagline_en: 'User basket, take-rate, and cross-app competition',
  journeyHeading_ar: 'مسار منصة التوصيل',
  journeyHeading_en: 'Delivery platform workflow',
  journeySub_ar: '٤ خطوات — من الطلب إلى الميزة التنافسية',
  journeySub_en: '4 steps — demand to competitive edge',
  journeyIntro_ar:
    'ركّز على موضعك أمام التطبيقات الأخرى، فجوات السلة، والمنتجات التي يختارها المستخدم بين المنصات. نظرة عامة → تسعير وتنافس → منتجات مؤثرة → توصيات وتنفيذ.',
  journeyIntro_en:
    'Focus on your position vs other apps, basket gaps, and SKUs users compare across platforms. Overview → pricing & rivalry → high-impact SKUs → recommendations.',
  steps: [
    {
      title_ar: 'موضع المنصة',
      title_en: 'Platform position',
      desc_ar: 'الحصة النسبية، التنبيهات، ومؤشرات السلة',
      desc_en: 'Share signals, alerts, and basket KPIs',
    },
    {
      title_ar: 'التطبيقات والأسعار',
      title_en: 'Apps & pricing',
      desc_ar: 'مقارنة الأسعار، المنتجات، والمنافسين المباشرين',
      desc_en: 'Price comparison, SKUs, and direct app rivals',
    },
    {
      title_ar: 'التحسين والإطلاق',
      title_en: 'Ship improvements',
      desc_ar: 'توصيات للعروض، الفئات، والتسعير الديناميكي',
      desc_en: 'Promo, category, and dynamic pricing actions',
    },
    {
      title_ar: 'هوية المنصة',
      title_en: 'Platform profile',
      desc_ar: 'العلامة ومصدر بيانات التوصيل',
      desc_en: 'Brand & delivery-market data source',
    },
  ],
  quick1_ar: 'منافس تطبيق مباشر',
  quick1_en: 'Head-to-head vs an app',
  quick2_ar: 'منتجات تُقارن بين التطبيقات',
  quick2_en: 'Cross-app compared SKUs',
  quick3_ar: 'قرارات المنتج والعروض',
  quick3_en: 'SKU & promo decisions',
  topbarFlow_ar: 'وضع التوصيل: سلة — تطبيق — سعر — تنفيذ',
  topbarFlow_en: 'Delivery mode: basket → app → price → ship',
  dataSourceHint_ar: 'بيانات سوق تطبيقات التوصيل والمطاعم',
  dataSourceHint_en: 'Delivery & restaurant marketplace data',
  navHints: {
    overview: {
      ar: '١ — موضع التطبيق في السلة مقابل المنصات الأخرى',
      en: '1 — Your app’s basket position vs competitors',
    },
    diagnosis: {
      ar: '٢ — أسعار السلة، المنتجات المتقاطعة، والمنافس المباشر',
      en: '2 — Basket prices, cross-app SKUs, and direct rivals',
    },
    action: {
      ar: '٣ — عروض، عمولات، وتحسينات تُطلق بسرعة',
      en: '3 — Promos, fees, and fast-shipping improvements',
    },
    context: {
      ar: '٤ — علامة التطبيق ومصدر بيانات السوق',
      en: '4 — App brand & marketplace data source',
    },
  },
}

export function getExperience(mode: ExperienceMode): ExperienceBundle {
  return mode === 'supermarket' ? RETAIL : DELIVERY
}
