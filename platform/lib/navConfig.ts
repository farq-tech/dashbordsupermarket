import type { LucideIcon } from 'lucide-react'
import {
  LayoutDashboard,
  DollarSign,
  Map,
  Users,
  Tag,
  BarChart2,
  Lightbulb,
  Scale,
  Store,
} from 'lucide-react'

/** v3 IA: Monitor → Diagnose → Prioritize → Decide — see docs/PRODUCT_DESIGN_DOCUMENT.md */
export type NavSectionId = 'overview' | 'diagnosis' | 'action' | 'context'

export interface NavItem {
  href: string
  icon: LucideIcon
  label_ar: string
  label_en: string
}

export interface NavSection {
  id: NavSectionId
  title_ar: string
  title_en: string
  items: NavItem[]
}

export const NAV_SECTIONS: NavSection[] = [
  {
    id: 'overview',
    title_ar: 'نظرة شاملة',
    title_en: 'Overview',
    items: [
      {
        href: '/dashboard',
        icon: LayoutDashboard,
        label_ar: 'نظرة عامة على الأداء',
        label_en: 'Business Overview',
      },
    ],
  },
  {
    id: 'diagnosis',
    title_ar: 'التشخيص',
    title_en: 'Diagnosis',
    items: [
      { href: '/pricing', icon: DollarSign, label_ar: 'استراتيجية التسعير', label_en: 'Pricing Strategy' },
      { href: '/coverage', icon: Map, label_ar: 'تغطية السوق', label_en: 'Market Coverage' },
      { href: '/competitors', icon: Users, label_ar: 'تحليل المنافسين', label_en: 'Competitive Analysis' },
      { href: '/categories', icon: Tag, label_ar: 'أداء الأقسام', label_en: 'Category Performance' },
      { href: '/products', icon: BarChart2, label_ar: 'تحليل المنتجات', label_en: 'Product Intelligence' },
    ],
  },
  {
    id: 'action',
    title_ar: 'الإجراءات',
    title_en: 'Action',
    items: [
      { href: '/recommendations', icon: Lightbulb, label_ar: 'التوصيات التشغيلية', label_en: 'Action Recommendations' },
      { href: '/decisions', icon: Scale, label_ar: 'مركز اتخاذ القرار', label_en: 'Decision Hub' },
    ],
  },
  {
    id: 'context',
    title_ar: 'سياق العمل',
    title_en: 'Business context',
    items: [
      { href: '/profile', icon: Store, label_ar: 'ملف الشركة', label_en: 'Business Profile' },
    ],
  },
]

export const PAGE_TITLES: Record<string, { ar: string; en: string }> = {
  '/dashboard': { ar: 'نظرة عامة على الأداء', en: 'Business Overview' },
  '/pricing': { ar: 'استراتيجية التسعير', en: 'Pricing Strategy' },
  '/coverage': { ar: 'تغطية السوق', en: 'Market Coverage' },
  '/competitors': { ar: 'تحليل المنافسين', en: 'Competitive Analysis' },
  '/categories': { ar: 'أداء الأقسام', en: 'Category Performance' },
  '/products': { ar: 'تحليل المنتجات', en: 'Product Intelligence' },
  '/recommendations': { ar: 'التوصيات التشغيلية', en: 'Action Recommendations' },
  '/decisions': { ar: 'مركز اتخاذ القرار', en: 'Decision Hub' },
  '/profile': { ar: 'ملف الشركة', en: 'Business Profile' },
}
