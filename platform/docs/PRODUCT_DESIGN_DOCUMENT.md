# Product Design Document  
## Retail Business Intelligence Platform  
### منصة ذكاء الأعمال للتجزئة

| Field | Value |
|--------|--------|
| **Version** | 3.0 (Final Design & UX Alignment) |
| **Audience** | Product, Design, UX, Engineering |

---

## 1. Product Vision

**English**

A business intelligence and decision platform that enables retail businesses to understand market performance, identify risks and opportunities, and take data-driven decisions with confidence.

**العربية**

منصة ذكاء أعمال تمكّن شركات التجزئة من فهم أداءها في السوق، واكتشاف الفرص والمخاطر، واتخاذ قرارات مدروسة بثقة.

---

## 2. Product Purpose

The platform is designed to help businesses:

- Monitor market performance  
- Understand competitive position  
- Identify risks and opportunities  
- Prioritize actions  
- Execute decisions  

**Core idea**

This is not a dashboard.  
**This is a decision system.**

---

## 3. Design Principles

1. **Clarity over complexity** — Users should understand the page within seconds.

2. **Insight-first** — Always show:
   - What is happening  
   - Why it matters  
   - What to do next  

3. **Decision-driven UX** — Every screen must guide toward action.

4. **Professional & trustworthy** — The experience must feel structured, calm, enterprise-grade.

5. **Arabic-first experience** — Arabic is the default; RTL is native (not mirrored); language must feel natural, not translated.

---

## 4. Product Experience Flow

The platform should feel like a guided workflow:

**Monitor → Diagnose → Prioritize → Decide → Export**

---

## 5. Information Architecture

### Navigation Structure

**1. Overview**

| EN | AR |
|----|-----|
| Business Overview | نظرة عامة على الأداء |

**2. Diagnosis**

| EN | AR |
|----|-----|
| Pricing Strategy | استراتيجية التسعير |
| Market Coverage | تغطية السوق |
| Competitive Analysis | تحليل المنافسين |
| Category Performance | أداء الأقسام |
| Product Intelligence | تحليل المنتجات |

**3. Action**

| EN | AR |
|----|-----|
| Action Recommendations | التوصيات التشغيلية |
| Decision Hub | مركز اتخاذ القرار |

**4. Business Context**

| EN | AR |
|----|-----|
| Business Profile | ملف الشركة |

---

## 6. Global Context & Controls

| English | العربية |
|---------|---------|
| Data Source | مصدر البيانات |
| Retail Market | متاجر التجزئة |
| Delivery Apps | تطبيقات التوصيل |
| Business | الشركة |
| Refresh | تحديث البيانات |
| Last Updated | آخر تحديث |
| Language | اللغة |

**UX requirements**

- Must be visually grouped  
- Must clearly indicate global impact  
- Must show loading state when changed  

---

## 7. Page Design Framework

Every page must follow this structure.

### A. Page header

- Title  
- Short description  
- Context (business + data source)  

### B. Insight summary (critical)

Must answer:

- What is happening  
- Why it matters  
- What to do  

**Example (Arabic)**

يوجد عدد من المنتجات بأسعار أعلى من السوق، مما قد يؤثر على القدرة التنافسية.  
يُنصح بمراجعة الأسعار المقترحة.

### C. Content sections

- Critical alerts (if any)  
- Opportunities  
- Supporting analysis (charts/tables)  

### D. Actions

Clear CTAs, e.g.:

- View recommendations  
- Add to decision hub  
- Export / print  

---

## 8. Key Screens

### 8.1 Business Overview (Dashboard) — نظرة عامة على الأداء

**Goal:** Executive summary  

**Structure:** KPI summary · Key insight · Alerts · Opportunities · Supporting charts  

### 8.2 Pricing Strategy — استراتيجية التسعير

**Goal:** Identify pricing gaps  

**Structure:** Pricing gap summary · Impacted products · Recommendations · Charts  

### 8.3 Product Intelligence — تحليل المنتجات

**Goal:** SKU-level analysis  

**Features:** Search & filters · Tag indicators · Deep linking support  

### 8.4 Market Coverage — تغطية السوق

**Goal:** Identify assortment gaps  

### 8.5 Competitive Analysis — تحليل المنافسين

**Goal:** Understand positioning  

### 8.6 Action Recommendations — التوصيات التشغيلية

**Goal:** Action queue  

Each item includes: Insight · Impact · Priority · Action  

### 8.7 Decision Hub — مركز اتخاذ القرار

**Core experience of the product**

**Structure:** Decision queue · Scenario analysis · Impact estimation · Export / print  

---

## 9. Visual Design System

**Style:** Clean · Minimal · Structured · Professional  

### Color principles

Use color only for meaning:

| Meaning | Color |
|---------|--------|
| Risk | Red |
| Opportunity | Green |
| Neutral | Blue |
| Attention | Amber |

### Typography

**Hierarchy**

- Titles → strong  
- Insights → clear  
- Metrics → large  
- Labels → subtle  

Arabic typography must feel natural and balanced.

### Component types

| Component | Role |
|-----------|------|
| KPI Card | Key metrics |
| Insight Card | Narrative insight |
| Alert Card | Risk / attention |
| Analysis Card | Supporting data |
| Decision Card | Decision items |

Each has a clear role.

---

## 10. Interaction & States

**Required states**

- Loading (skeleton preferred)  
- Updating (after switching context)  
- Empty  
- Error  

**Transitions**

- Smooth and minimal  
- Maintain layout stability  

---

## 11. Layout System

**Sidebar**

- Fixed (RTL)  
- Grouped navigation  
- Active state  
- Alert indicators  

**Top bar**

- Page title  
- Context (chips)  
- Actions  

Clean and focused.

---

## 12. Bilingual Experience

**Requirements**

- Full Arabic + English support  
- RTL / LTR switching  
- No layout breaking  
- Consistent spacing  

---

## 13. Terminology System

### Business vocabulary

| English | العربية |
|---------|---------|
| Performance | الأداء |
| Growth | النمو |
| Risk | المخاطر |
| Opportunity | الفرص |
| Impact | التأثير |
| Trend | الاتجاه |
| Competitiveness | القدرة التنافسية |

### Product tags

| English | العربية |
|---------|---------|
| Overpriced | سعر أعلى من السوق |
| Underpriced | سعر أقل من السوق |
| Competitive | سعر تنافسي |
| Opportunity | فرصة تحسين |
| Risk | مخاطر محتملة |
| Not Available | غير متوفر |

---

## 14. Decision Language

Use strong business wording:

- توصية (Recommendation)  
- قرار (Decision)  
- تأثير متوقع (Expected impact)  
- مستوى الثقة (Confidence level)  
- المخاطر المحتملة (Potential risks)  

---

## 15. Success Criteria

The redesign is successful if users can:

- Understand pages within seconds  
- Identify key insights immediately  
- Know what action to take  
- Navigate easily  
- Use Decision Hub as a core workflow  

---

## 16. Deliverables

Design team should provide:

1. **Screens** — All pages, Arabic + English  
2. **Design system** — Colors, typography, components  
3. **Interaction specs** — States, transitions, workflows  
4. **Developer handoff** — Tokens, components, edge cases  

---

## Final positioning

**English**

A decision platform for retail business performance.

**العربية**

منصة لاتخاذ القرارات لتعزيز أداء أعمال التجزئة.

---

## Engineering & implementation map

For current routes, design tokens, component paths, and automated UI checks, see **[DESIGN_HANDOFF.md](DESIGN_HANDOFF.md)**.
