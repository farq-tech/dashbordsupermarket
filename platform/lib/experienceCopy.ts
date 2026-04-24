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

/** Per-page Topbar descriptions (and optional subtitles) by data source. */
export interface PageTopbarCopy {
  description_ar: string
  description_en: string
  subtitle_ar?: string
  subtitle_en?: string
}

export type AppTopbarRoute =
  | '/dashboard'
  | '/pricing'
  | '/coverage'
  | '/competitors'
  | '/categories'
  | '/products'
  | '/recommendations'
  | '/decisions'
  | '/profile'

const PAGE_TOPBAR: Record<
  AppTopbarRoute,
  { supermarket: PageTopbarCopy; restaurants: PageTopbarCopy }
> = {
  '/dashboard': {
    supermarket: {
      description_ar: 'ماذا يحدث على مستوى السلسلة، لماذا يهم، وما الخطوة التالية — مقارنة مباشرة مع سلاسل التجزئة الأخرى.',
      description_en: 'What is happening at chain level, why it matters, and what to do next — benchmarked against other retail brands.',
    },
    restaurants: {
      description_ar: 'موضع تطبيقك في السلة والسعر مقابل تطبيقات التوصيل الأخرى — ثم أين تركّز التحسين.',
      description_en: 'Your app’s basket and price position vs other delivery platforms — then where to focus improvements.',
    },
  },
  '/pricing': {
    supermarket: {
      description_ar: 'توزيع تسعير الرف: أين سلسلتك أغلى أو أرخص من السلاسل المجاورة على نفس المنتجات.',
      description_en: 'Shelf pricing distribution: where your chain is expensive or cheap vs peer chains on the same SKUs.',
    },
    restaurants: {
      description_ar: 'سلة المستخدم عبر التطبيقات: فجوات السعر، والفرص أمام المنافسين على نفس الأصناف.',
      description_en: 'User basket across apps: price gaps and opportunities vs rivals on the same items.',
    },
  },
  '/coverage': {
    supermarket: {
      description_ar: 'أين توجد فروع العلامات — كثافة السوق حسب المدينة لتوسيع الفروع أو مراقبة المنافس.',
      description_en: 'Where brands have branches — market density by city for expansion or competitive watch.',
    },
    restaurants: {
      description_ar: 'سياق جغرافي مستقل: كثافة السوبرماركت والعلامات يساعدك على فهم السوق خلف الطلب على التوصيل.',
      description_en: 'Independent geo context: grocery brand density helps you read the market behind delivery demand.',
    },
  },
  '/competitors': {
    supermarket: {
      description_ar: 'مقارنة رأساً برأس مع سلسلة منافسة: سلة مشتركة، فئات، وترتيب السعر على مستوى المنتج.',
      description_en: 'Head-to-head vs a rival chain: shared basket, categories, and SKU-level price outcomes.',
    },
    restaurants: {
      description_ar: 'منافس تطبيق واحد: أين تفوز السلة وأين تخسر أمام منصة أخرى على نفس الكتالوج.',
      description_en: 'One rival app: where you win or lose the basket against another platform on overlapping catalog.',
    },
  },
  '/categories': {
    supermarket: {
      description_ar: 'أداء الأقسام على الرف: حجم التشكيلة، التسعير، والضغط مقابل السلاسل الأخرى.',
      description_en: 'Category performance on shelf: assortment size, pricing pressure vs other chains.',
    },
    restaurants: {
      description_ar: 'أقسام تهم المستخدم في التطبيق: أين تتفوق منصتك أو تتأخر أمام التطبيقات المنافسة.',
      description_en: 'Categories that matter in-app: where your platform leads or trails competing apps.',
    },
  },
  '/products': {
    supermarket: {
      description_ar: 'كل SKU مع وحدة العرض والفجوة السعرية — لقرارات الرف والتوريد في الفروع.',
      description_en: 'Every SKU with pack size and price gap — for shelf and branch supply decisions.',
    },
    restaurants: {
      description_ar: 'منتجات تُقارن بين التطبيقات: أين السعر أو التوفر يحرك اختيار المستخدم.',
      description_en: 'Cross-app compared SKUs: where price or availability drives user choice.',
    },
  },
  '/recommendations': {
    supermarket: {
      description_ar: 'إجراءات مرتبة بالأولوية للفروع: تسعير، توريد، ومنافسة على الأصناف الحساسة.',
      description_en: 'Branch-prioritized actions: pricing, supply, and competition on sensitive SKUs.',
    },
    restaurants: {
      description_ar: 'تحسينات للعروض والسلة والعمولة — جاهزة للتنفيذ على كتالوج التطبيق.',
      description_en: 'Promo, basket, and fee improvements — ready to ship against your app catalog.',
    },
  },
  '/decisions': {
    supermarket: {
      description_ar: 'حوّل التحليل إلى قرارات مسجلة: سياسات، سيناريوهات، وسير عمل للفروع.',
      description_en: 'Turn analysis into logged decisions: policy, scenarios, and branch workflow.',
      subtitle_ar: 'طبقة قرار للسلسلة: سياسات، سيناريوهات، سير عمل، تصدير',
      subtitle_en: 'Retail chain decision layer: policy, scenarios, workflow, export',
    },
    restaurants: {
      description_ar: 'قرارات منتج وعروض مع أثر واضح على السلة — مع تتبع وسيناريوهات.',
      description_en: 'Product and promo decisions with clear basket impact — tracked with scenarios.',
      subtitle_ar: 'طبقة قرار للمنصة: سياسات، سيناريوهات، سير عمل، تصدير',
      subtitle_en: 'Platform decision layer: policy, scenarios, workflow, export',
    },
  },
  '/profile': {
    supermarket: {
      description_ar: 'هوية سلسلتك ومصدر بيانات التجزئة المستخدم في كل المقارنات.',
      description_en: 'Your chain identity and the retail data source powering all comparisons.',
    },
    restaurants: {
      description_ar: 'علامة التطبيق ومصدر بيانات سوق التوصيل المعتمد في اللوحة.',
      description_en: 'Your app brand and the delivery-market data source used across the dashboard.',
    },
  },
}

export function getPageTopbarCopy(path: string, mode: ExperienceMode): PageTopbarCopy {
  const key = path.split('?')[0] as AppTopbarRoute
  const row = PAGE_TOPBAR[key]
  if (!row) {
    return {
      description_ar: 'اتبع المسار من الشريط الجانبي: مراقبة ثم تشخيص ثم إجراء.',
      description_en: 'Follow the sidebar: monitor, then diagnose, then act.',
    }
  }
  return mode === 'supermarket' ? row.supermarket : row.restaurants
}
