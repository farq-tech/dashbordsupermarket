# UI / UX handoff — Supermarket Intelligence Platform

**Audience:** Product designers, UX researchers, and visual designers who will redesign screens, components, and interaction patterns.  
**Stack:** Next.js (App Router), React 19, Tailwind CSS v4, Zustand, Recharts, Lucide icons.  
**Default language:** Arabic (`ar`), RTL; users can switch to English (`en`) from the top bar.

**Related document:** **[Product Design Document v3.0](PRODUCT_DESIGN_DOCUMENT.md)** — product vision, IA naming (Overview / Diagnosis / Action), design principles, page framework, terminology, and success criteria. This handoff file maps **what exists in code** (routes, tokens, components) to support engineering and visual redesign execution.

---

## 1. Product in one sentence

A **B2B analytics dashboard** for Saudi retail chains: compare pricing, coverage, and competitiveness vs the market, surface **alerts** and **recommended actions**, and support a **Decision Center** workflow (queue, scenarios, exports).

---

## 2. Screen map (information architecture)

Navigation is **grouped** in the sidebar (v3): **Overview** → **Diagnosis** → **Action** → **Business context**. Labels and routes are defined in **`lib/navConfig.ts`** (`NAV_SECTIONS`, `PAGE_TITLES`).

All screens live under the **same app shell**: fixed **right sidebar** (`w-64`) + **main** (`mr-64`) with a **sticky top bar** per page.

| Route | Arabic title (v3) | English title | Primary purpose |
|--------|---------------------|---------------|-----------------|
| `/` | — | — | Redirects to `/dashboard` |
| `/dashboard` | نظرة عامة على الأداء | Business Overview | KPIs, **insight summary** card, charts, alerts |
| `/pricing` | استراتيجية التسعير | Pricing Strategy | Scatter, segments, gap distribution |
| `/coverage` | تغطية السوق | Market Coverage | Coverage by category / regions |
| `/competitors` | تحليل المنافسين | Competitive Analysis | Competitive landscape |
| `/categories` | أداء الأقسام | Category Performance | Category KPIs and charts |
| `/products` | تحليل المنتجات | Product Intelligence | Searchable table, tags, CSV; `?fid=<id>` deep link |
| `/recommendations` | التوصيات التشغيلية | Action Recommendations | Recommendations + alerts |
| `/decisions` | مركز اتخاذ القرار | Decision Hub | Queue, scenarios, workflow, export, print |
| `/profile` | ملف الشركة | Business Profile | Chain / retailer profile |

**Sidebar order** (top → bottom) matches user mental model: Overview → Decisions → Profile → Products → Pricing → Coverage → Competitors → Categories → Recommendations.

---

## 3. Global layout (current implementation)

| Region | Behavior | Approx. size |
|--------|----------|----------------|
| **Sidebar** | Fixed, `right: 0`, full viewport height, scrollable nav | **240px** (`w-60`) |
| **Main** | Content column; offset for sidebar | `margin-inline-end: 240px` (`mr-60` in RTL) |
| **Top bar** | Sticky under browser chrome, per page | **80px** tall (`h-20`) |
| **Background** | Page background token | `--color-bg` |

**Shell components**

- `Sidebar` — logo block, **data source** segment (Supermarket vs Delivery apps), **chain/retailer list**, primary **nav links**, optional **alerts** footer strip, version line.
- `Topbar` — page **H1** + optional subtitle, retailer chip (sm+), **data source** toggle (duplicate of sidebar for quick access), **last updated**, **Refresh** (outline button), **language** toggle (EN / عر).  
  - Stable hook for QA/automation: `data-testid="app-topbar"`.

---

## 4. Global actions (appear in almost every screen)

| Action | Where | Arabic | English | Notes |
|--------|--------|--------|---------|--------|
| Data source | Sidebar + Top bar | سوبرماركت / تطبيقات التوصيل | Supermarket / Delivery apps | Switching source **clears dashboard state** and refetches data |
| Language | Top bar | EN / عر | EN / عر | Sets `html[lang]` and `dir`; toggles all copy that uses the store |
| Retailer / chain | Sidebar | السلسلة | Chain | Selects store; **refetches** data for that retailer |
| Refresh | Top bar | تحديث | Refresh | Re-loads dashboard bundle from API |

---

## 5. Design tokens (current)

Defined in `app/globals.css` (`@theme inline`). Designers can treat these as **starting points** for a re-skin.

### Brand & surfaces

| Token | Value | Usage |
|--------|--------|--------|
| `--color-brand` | `#043434` | Primary brand, logo tile |
| `--color-brand-hover` | `#065151` | Primary hover |
| `--color-accent` | `#75F0A8` | Accent on logo mark |
| `--color-text-primary` | `#2D2E2E` | Body / titles |
| `--color-text-secondary` | `#355273` | Secondary labels |
| `--color-border` | `#EAEDF1` | Dividers, outlines |
| `--color-bg` | `#FCFCFC` | Page background |
| `--color-surface` | `#FFFFFF` | Cards / panels |
| `--color-surface-muted` | `#F4F8FB` | Muted panels |
| `--color-surface-hover` | `#EFF8F2` | Hover / selected row |
| `--color-sidebar-bg` | surface | Sidebar background |
| `--color-topbar-bg` | surface | Top bar background |

### Typography

| Token | Value |
|--------|--------|
| `--font-sans` | Inter (via `next/font`) + system UI stack |
| `--font-brand` | Futura (if available) + Poppins + Inter |

Root layout loads **Inter** and **Poppins** through `next/font` (`app/layout.tsx`).

### Radius

| Token | Value |
|--------|--------|
| `--radius-sm` | 8px |
| `--radius-md` | 12px |
| `--radius-lg` | 20px |

### Semantic tag colors (product status)

Used for pricing/product tags (see also `TagBadge` / CSS classes):

- Overpriced — red tint  
- Underpriced — green tint  
- Competitive — blue tint  
- Opportunity — amber/yellow tint  
- Risk — orange tint  
- Not stocked — gray tint  

Exact hex pairs live under **“Tag colors”** in `globals.css` (`.tag-overpriced`, etc.).

---

## 6. Component library (in repo)

| Area | Path / name | Role |
|------|-------------|------|
| Buttons | `components/ui/button.tsx` | Variants: `primary`, `secondary`, `ghost`, `danger`, `outline`; sizes `sm`, `md`, `lg`; optional loading spinner |
| Cards | `components/ui/card.tsx` | Content containers |
| KPI blocks | `components/ui/kpi-card.tsx` | Title (AR/EN props), value, unit, trend |
| Badges | `components/ui/badge.tsx` | Pill status |
| Product tags | `components/ui/badge.tsx` (`TagBadge`) | Maps `tag` string → **Arabic label + color class** (English tag labels in table views are handled elsewhere on some pages) |
| Spinner / loading | `components/ui/spinner.tsx` | Full-page style loading block |
| Logos | `components/ui/RetailerLogo.tsx` | Chain avatars / initials |
| Charts | `components/charts/*` | Bar, scatter, pie, etc. (Recharts) |

**Radix** is used for dialogs, dropdowns, select, tabs, tooltip (`package.json`) — good reference if you change interaction patterns.

---

## 7. UX patterns to preserve (or consciously replace)

1. **Heavy data load:** First paint often shows **Topbar + loading overlay** until `/api/data` returns. Any redesign should keep a clear **loading** and **error/empty** state for retailer lists and dashboard.
2. **Two data universes:** “Supermarket” vs “Delivery apps” is a **mode switch**, not a cosmetic filter; changing it reloads the world.
3. **Retailer switch:** Changing chain **reloads** KPIs and tables — consider preserving explicit feedback (skeleton, progress).
4. **Decision Center:** Supports **print** and export; print hides elements marked `.no-print`.
5. **Products deep link:** `/products?fid=<numeric>` is used to open one SKU when search/filters are empty — keep URL contract if marketing or emails link here.
6. **Bilingual:** Copy is split **per screen** via `lang` from Zustand; new strings should be added in **both** languages in code (or future CMS).

---

## 8. Icons

**Lucide React** (`lucide-react`) — sidebar and actions use small **16–20px** icons next to labels.

---

## 9. Automated UI coverage (for regression after redesign)

From `platform/`:

- `npm run test:ui` — Playwright smoke (shell, nav, language, data source, main heading).
- `npm run test:consistency` — Data pipeline invariants (not visual).

Designers don’t need to run these; engineering can use them after UI swaps.

---

## 10. What a redesign project typically delivers back

- Updated **Figma** (or similar): all routes above, **both** AR and EN, **mobile/tablet** if in scope (today layout is **desktop-first**; sidebar is fixed width).
- **Token spec** if replacing `--color-*` / typography.
- **Component specs** for buttons, cards, tables, charts (or chart styling guidelines).
- **Interaction notes** for data source, retailer list, refresh, and Decision Center exports.

---

## 11. File pointers for engineers pairing with design

| Topic | Location |
|--------|----------|
| Theme / tokens | `app/globals.css` |
| Fonts | `app/layout.tsx` |
| App shell | `app/(app)/layout.tsx`, `components/layout/Sidebar.tsx`, `components/layout/Topbar.tsx` |
| Nav labels & routes | `NAV_ITEMS` in `Sidebar.tsx` |
| Global state (lang, retailer, data source) | `store/useAppStore.ts` |

---

*Document generated to match the codebase structure; after major UI changes, ask engineering to refresh this file or attach Figma links.*
