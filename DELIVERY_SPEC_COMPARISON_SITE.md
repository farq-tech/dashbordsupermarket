# مستند تسليم شامل لمطور موقع مقارنة منتجات (مثل فستق)

هذا المستند يحدد **كل الملفات والمعلومات المطلوبة** لبناء نظام مقارنة منتجات/أسعار بين السوبرماركت، بحيث يكون عند المطور “عقد بيانات” واضح وسهل التنفيذ.

---

## 1) الهدف (What we are building)

موقع/تطبيق يعرض:
- **منتجات موحّدة** (قائمة منتجات + تفاصيلها).
- **أسعار نفس المنتج** عبر **عدة متاجر/فروع** (مع العروض، التوفر، تاريخ الالتقاط).
- **مقارنات**: الأرخص، الفرق السعري، عدد المتاجر التي لديها المنتج، تتبع سعر عبر الزمن.

---

## 2) مخرجات التسليم (Delivery artifacts)

سلّم للمطور هذه الملفات (يفضل CSV أو Parquet):

### 2.1 ملفات البيانات الأساسية (MVP)
1) `products.csv`  
2) `stores.csv`  
3) `prices.csv`

### 2.2 ملفات مفيدة (Strongly recommended)
4) `retailers.csv` (براند/سوبرماركت)  
5) `product_match.csv` (ربط/توحيد المنتجات بين المصادر إن وجدت)  
6) `bundle.json` (ميتا + روابط للملفات + أرقام تحقق)
7) `DATA_DICTIONARY.md` (تعريف الأعمدة والقواعد)

> **ملاحظة**: في بياناتك الحالية داخل `f:\\fustog\\data\\` أنت بالفعل قريب جدًا من هذا الشكل عبر:
> - `fustog_live_products_*.csv`
> - `fustog_live_prices_*.csv`
> - `fustog_stores_lookup_*.csv`
> - `fustog_matching_summary_*.csv`

---

## 3) المفاتيح الأساسية (Primary Keys) — أهم نقطة للمطور

### 3.1 تعريف الكيانات
- **Retailer (البراند/السوبرماركت)**: مثل Panda / Othaim / LuLu  
  - المفتاح: `retailer_id`
- **Store/Branch (فرع/موقع)**: فرع محدد داخل مدينة  
  - المفتاح: `store_id`
  - يرتبط بـ: `retailer_id`
- **Product (المنتج)**: كيان المنتج في كتالوج موحّد  
  - المفتاح: `product_id` (ثابت)
- **Price Observation (رصد سعر)**: سعر منتج في فرع/متجر في وقت محدد  
  - المفتاح المركب: `(product_id, store_id, captured_at)`

### 3.2 قواعد فريدة البيانات
- `products.csv`: `product_id` فريد.
- `stores.csv`: `store_id` فريد.
- `retailers.csv`: `retailer_id` فريد.
- `prices.csv`: لا يوجد صفّان متطابقان لنفس `(product_id, store_id, captured_at)`.

---

## 4) مواصفات الملفات (Schemas)

### 4.1 `products.csv` — جدول المنتجات

**الغرض**: معلومات ثابتة نسبيًا عن المنتج (اسم، ماركة، حجم…).

**أعمدة مطلوبة (Minimum):**
- `product_id` (string|int): معرف ثابت.
- `title_ar` (string)
- `title_en` (string, optional)
- `brand_ar` (string, optional)
- `brand_en` (string, optional)
- `category_id` (string|int, optional)
- `category_name` (string, optional)
- `unit` (string, optional): مثل `g`,`kg`,`ml`,`l`,`pcs`
- `unit_value` (number, optional): مثل 1800
- `image_url` (string, optional)
- `source` (string): مثل `fustog`
- `last_updated` (datetime ISO8601)

**أعمدة اختيارية (Recommended):**
- `barcode_gtin` (string): أفضل مفتاح توحيد.
- `description_ar` / `description_en`
- `is_active` (bool)

**قواعد تطبيع مهمة:**
- توحيد الوحدة إلى قاموس ثابت (g, kg, ml, l, pcs).
- توحيد `unit_value` إلى رقم.
- عدم الاعتماد على الاسم وحده في التوحيد.

---

### 4.2 `retailers.csv` — جدول البراند/السوبرماركت

**الغرض**: اسم السوبرماركت ككيان مستقل عن الفرع.

**أعمدة مطلوبة:**
- `retailer_id` (int|string)
- `retailer_name_ar` (string)
- `retailer_name_en` (string, optional)
- `source` (string)

**أعمدة اختيارية:**
- `logo_url` (string)
- `website` (string)

> إذا لم يتوفر هذا الملف من المصدر، يمكن استخراج البراند من أسماء الفروع أو من endpoints خاصة بالـ retailers.

---

### 4.3 `stores.csv` — جدول الفروع/المواقع

**الغرض**: تعريف الفرع/الموقع الذي يأتي منه السعر.

**أعمدة مطلوبة:**
- `store_id` (int|string): معرف فرع.
- `retailer_id` (int|string): يربط للبراند.
- `store_name_ar` (string): اسم الفرع كما في المصدر.
- `store_name_en` (string, optional)
- `city` (string, optional)
- `lat` (number, optional)
- `lon` (number, optional)
- `is_integration_ready` (bool, optional)
- `source` (string)
- `last_updated` (datetime ISO8601)

**مهم**:
- لا تخلط “اسم البراند” مع “اسم الفرع”. الفرع يكون مثل: “النفل”، “الملقا V152”… بينما البراند: “العثيم”، “لولو”، “بنده”.

---

### 4.4 `prices.csv` — جدول الأسعار (Long format)

**الغرض**: كل سطر يمثل سعر منتج في فرع/متجر في وقت معين.

**أعمدة مطلوبة (Minimum):**
- `product_id`
- `store_id`
- `price` (number): السعر الأساسي.
- `currency` (string): مثل `SAR`
- `available` (bool): متاح/غير متاح (إن توفر).
- `captured_at` (datetime ISO8601): وقت الالتقاط.
- `source` (string)

**أعمدة اختيارية مهمة (Recommended):**
- `sale_price` (number): سعر العرض إن وجد.
- `promo_text` (string): وصف العرض.
- `offer_end` (datetime ISO8601)
- `min_qty` / `max_qty`
- `is_online_price` (bool)

**قواعد مهمة للأسعار:**
- إن كان المصدر يعطي قيمًا سالبة أو 0 لعدم التوفر: يجب تحويلها إلى:
  - `available=false` وترك `price` فارغ (NULL) أو حذف السطر.

---

### 4.5 `product_match.csv` — توحيد المنتجات (إذا عندك أكثر من مصدر)

**الغرض**: ربط المنتجات من عدة مصادر إلى منتج موحّد (canonical).

**أعمدة مقترحة:**
- `canonical_product_id`
- `source` (مثل: `fustog`, `panda`, `lulu`)
- `source_product_id`
- `match_method` (barcode|name_brand_size|manual|ml)
- `confidence` (0..1)
- `matched_at` (datetime)

**بدونه**: ستظهر نفس السلعة كمنتجات متعددة ويصعب المقارنة عبر مصادر مختلفة.

---

## 5) ملف الحزمة `bundle.json` (للتسليم السريع)

ملف واحد يختصر على المطور وقت كبير:

**محتوى مقترح:**
- `metadata`:
  - `captured_at`
  - `source`
  - `products_count`
  - `stores_count`
  - `prices_count`
  - `cities_covered`
- `files`:
  - مسارات `products.csv`, `stores.csv`, `retailers.csv`, `prices.csv`, `product_match.csv` (إن وجد)
- `checks`:
  - `primary_keys_ok: true/false`
  - `null_rates`
  - `price_min/max`

---

## 6) متطلبات الـ Backend (باختصار مفيد للمطور)

### 6.1 Queries أساسية يجب دعمها
- `GET /products?search=&category=&brand=&page=`
- `GET /products/{id}`
- `GET /products/{id}/prices?city=&retailer=&sort=`
- `GET /compare?product_ids=...&retailers=...`
- `GET /retailers`
- `GET /stores?retailer_id=&city=`

### 6.2 حسابات (Derived metrics)
- `min_price`, `max_price`, `spread`
- `cheapest_store_id`, `cheapest_retailer_id`
- `stores_count` (عدد المتاجر التي لديها المنتج)
- `price_history` (إذا لديك time-series)

---

## 7) متطلبات واجهة المستخدم (UI) للمقارنة

- البحث (Arabic + English) + فلترة (مدينة/براند/تصنيف).
- صفحة منتج:
  - صورة + حجم + ماركة
  - قائمة أسعار حسب المتجر
  - “الأرخص” مميز
- صفحة مقارنة متعددة:
  - صفوف = منتجات
  - أعمدة = retailers أو stores
  - إبراز الفروقات

---

## 8) “Check-list” تحقق سريع قبل التسليم

قبل تسليم الحزمة للمطور:
- [ ] `products_count` منطقي (ليس صفر).
- [ ] `prices_count` منطقي (ليس صفر).
- [ ] كل `product_id` في `prices.csv` موجود في `products.csv`.
- [ ] كل `store_id` في `prices.csv` موجود في `stores.csv`.
- [ ] `price > 0` لكل صف سعر.
- [ ] الترميز `utf-8`.
- [ ] زمن الالتقاط `captured_at` موجود.

---

## 9) مثال ربط مباشر من بيانات فستق الحالية عندك (Reference)

عندك بالفعل ملف long جاهز للمقارنة (منتج + متجر + سعر) شبيه بـ `prices.csv`:
- `f:\\fustog\\data\\fustog_prices_enriched_long_*.csv`

وعندك ملف ملخص per product شبيه بحسابات المقارنة:
- `f:\\fustog\\data\\fustog_matching_summary_*.csv`

وعندك lookup للمتاجر/الفروع + (إن أمكن) البراند:
- `f:\\fustog\\data\\fustog_stores_lookup_*.csv`

---

## 10) ملاحق (اختياري)

### 10.1 أفضل صيغة للتسليم (Zip)
اقترح تسليم ملف zip يحتوي:
```
delivery/
  bundle.json
  DATA_DICTIONARY.md
  products.csv
  retailers.csv
  stores.csv
  prices.csv
  product_match.csv   (اختياري)
```

### 10.2 لماذا “Long format” أفضل؟
لأنه:
- أسهل للتحديث (append-only).
- أسهل للفلترة وaggregation.
- مناسب لأي قاعدة بيانات وتحليلات.

