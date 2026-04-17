#!/usr/bin/env python3
"""
Extract ALL products from Panda API (the working retailer)
+ Fustog categories for mapping

Outputs:
  data/all_products_full.csv
  data/all_products_full.json
"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import json
import os
import csv
import time
from datetime import datetime
import httpx

# ===== LZ-String decompressor for Fustog categories =====
_LZ_KEY = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
_LZ_REV = {}
def _lz_val(ch):
    if _LZ_KEY not in _LZ_REV:
        _LZ_REV[_LZ_KEY] = {c: i for i, c in enumerate(_LZ_KEY)}
    return _LZ_REV[_LZ_KEY][ch]
def lz_decompress(s):
    if not s: return ""
    s = "".join(s.split())
    length = len(s)
    def gnv(i): return _lz_val(s[i])
    d = {0: chr(0), 1: chr(1), 2: chr(2)}
    ei = 4; ds = 4; nb = 3; w = ""; r = []
    dv = gnv(0); dp = 32; di = 1
    bits = 0; mp = 4; pw = 1
    while pw != mp:
        resb = dv & dp; dp >>= 1
        if dp == 0: dp = 32; dv = gnv(di); di += 1
        bits |= (1 if resb > 0 else 0) * pw; pw <<= 1
    nx = bits
    if nx == 2: return ""
    bw = 8 if nx == 0 else 16
    bits = 0; mp = 2**bw; pw = 1
    while pw != mp:
        resb = dv & dp; dp >>= 1
        if dp == 0: dp = 32; dv = gnv(di); di += 1
        bits |= (1 if resb > 0 else 0) * pw; pw <<= 1
    c = chr(bits); d[3] = c; w = c; r.append(c)
    while True:
        if di > length: return "".join(r)
        bits = 0; mp = 2**nb; pw = 1
        while pw != mp:
            resb = dv & dp; dp >>= 1
            if dp == 0:
                dp = 32
                if di < length: dv = gnv(di); di += 1
                else: dv = 0
            bits |= (1 if resb > 0 else 0) * pw; pw <<= 1
        cc = bits
        if cc == 0 or cc == 1:
            bw = 8 if cc == 0 else 16
            bits = 0; mp = 2**bw; pw = 1
            while pw != mp:
                resb = dv & dp; dp >>= 1
                if dp == 0: dp = 32; dv = gnv(di); di += 1
                bits |= (1 if resb > 0 else 0) * pw; pw <<= 1
            d[ds] = chr(bits); cc = ds; ds += 1; ei -= 1
        elif cc == 2:
            return "".join(r)
        if ei == 0: ei = 2**nb; nb += 1
        if cc in d: entry = d[cc]
        elif cc == ds: entry = w + w[0]
        else: return ""
        r.append(entry); d[ds] = w + entry[0]; ds += 1; ei -= 1; w = entry
        if ei == 0: ei = 2**nb; nb += 1


os.makedirs("data", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

PANDA_HEADERS = {
    "Accept": "application/json;charset=UTF-8",
    "User-Agent": "okhttp/5.0.0-alpha.6",
    "x-language": "ar",
    "x-pandaclick-agent": "4",
    "x-panda-source": "PandaClick",
}

FUSTOG_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16)",
    "Accept": "application/json, */*;q=0.5",
    "Accept-Encoding": "identity",
}

client = httpx.Client(timeout=30.0, follow_redirects=True)

# ============================================================
# STEP 1: Fetch Fustog categories (for reference mapping)
# ============================================================
print("=" * 60)
print("STEP 1: Fustog Categories")
print("=" * 60)
r = client.get("https://api.fustog.app/api/v2/category/Categories", headers=FUSTOG_HEADERS)
fustog_cats = r.json()
print(f"  Fustog categories: {len(fustog_cats)}")

# ============================================================
# STEP 2: Fetch Panda categories
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Panda Categories")
print("=" * 60)
r = client.get("https://api.panda.sa/v3/categories", headers=PANDA_HEADERS)
panda_cat_resp = r.json()
panda_categories = panda_cat_resp.get("data", {}).get("categories", [])
print(f"  Panda categories: {len(panda_categories)}")

# Build category tree
cat_map = {}  # id -> {name, parent_name}
def collect_cats(cats, parent_name=""):
    for cat in cats:
        cid = cat.get("id")
        name = cat.get("name", "")
        cat_map[cid] = {"name": name, "parent": parent_name}
        children = cat.get("children", cat.get("sub_categories", []))
        if children:
            collect_cats(children, name)
collect_cats(panda_categories)
print(f"  Total category tree: {len(cat_map)} categories")

# ============================================================
# STEP 3: Fetch ALL Panda products (paginated)
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Fetching ALL Panda Products (paginated)")
print("=" * 60)

# First, get total count
r = client.get("https://api.panda.sa/v3/products",
    headers=PANDA_HEADERS, params={"page": 1, "per_page": 1})
first_resp = r.json()
total_records = first_resp.get("data", {}).get("total_records", 0)
print(f"  Total products available: {total_records}")

PER_PAGE = 50
all_products = []
page = 1
max_pages = (total_records // PER_PAGE) + 2 if total_records else 200

while page <= max_pages:
    try:
        r = client.get("https://api.panda.sa/v3/products",
            headers=PANDA_HEADERS,
            params={"page": page, "per_page": PER_PAGE},
            timeout=20)

        if r.status_code != 200:
            print(f"  Page {page}: HTTP {r.status_code}, stopping")
            break

        data = r.json().get("data", {})
        products = data.get("products", [])

        if not products:
            print(f"  Page {page}: empty, done!")
            break

        all_products.extend(products)
        next_page = data.get("next_page")

        if page % 10 == 0 or page <= 3:
            print(f"  Page {page}: +{len(products)} products (total: {len(all_products)})")

        if not next_page:
            print(f"  No more pages after {page}")
            break

        page += 1
        time.sleep(0.3)  # Be polite

    except Exception as e:
        print(f"  Page {page}: ERROR {e}")
        time.sleep(2)
        page += 1

print(f"\n  TOTAL PRODUCTS FETCHED: {len(all_products)}")

# ============================================================
# STEP 4: Normalize and flatten product data
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: Normalizing product data")
print("=" * 60)

normalized = []
seen_ids = set()

for p in all_products:
    pid = p.get("id")
    if pid in seen_ids:
        continue
    seen_ids.add(pid)

    brand = p.get("brand", {}) or {}
    category = p.get("category", {}) or {}
    varieties = p.get("varieties", []) or []

    # Get first variety for price/size info
    first_var = varieties[0] if varieties else {}

    # Get image URL
    image_url = ""
    if first_var.get("imagePaths"):
        paths = first_var["imagePaths"]
        if isinstance(paths, list) and paths:
            image_url = paths[0]
        elif isinstance(paths, str):
            image_url = paths
    elif first_var.get("imageAr") and isinstance(first_var["imageAr"], str):
        image_url = first_var["imageAr"]

    row = {
        "product_id": pid,
        "sku": first_var.get("barcode", ""),
        "name_ar": p.get("name", ""),
        "name_en": "",  # Panda API is Arabic
        "category_id": category.get("id", ""),
        "category_name": category.get("name", ""),
        "parent_category": category.get("parent", ""),
        "brand_id": brand.get("id", ""),
        "brand_name": brand.get("name", ""),
        "description": "",
        "image_url": image_url,
        "price": first_var.get("price", ""),
        "sale_price": first_var.get("offer_price", first_var.get("sale_price", "")),
        "currency": "SAR",
        "size": first_var.get("size", ""),
        "unit": first_var.get("unit_name", first_var.get("unit", "")),
        "in_stock": 1 if first_var.get("available", True) else 0,
        "variety_id": first_var.get("id", ""),
        "barcode": first_var.get("barcode", ""),
        "store": "panda",
        "store_name": "Panda",
        "city": "Riyadh",
        "source_endpoint": "api.panda.sa/v3/products",
        "fetched_at": datetime.now().isoformat(),
        "varieties_count": len(varieties),
    }

    # Add all variety prices as separate rows if multiple
    if len(varieties) > 1:
        for vi, var in enumerate(varieties):
            var_row = dict(row)
            var_row["variety_id"] = var.get("id", "")
            var_row["price"] = var.get("price", "")
            var_row["sale_price"] = var.get("offer_price", var.get("sale_price", ""))
            var_row["size"] = var.get("size", "")
            var_row["unit"] = var.get("unit_name", var.get("unit", ""))
            var_row["barcode"] = var.get("barcode", "")
            var_row["in_stock"] = 1 if var.get("available", True) else 0
            normalized.append(var_row)
    else:
        normalized.append(row)

print(f"  Unique products: {len(seen_ids)}")
print(f"  Total rows (with variants): {len(normalized)}")

# ============================================================
# STEP 5: Export to CSV and JSON
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: Exporting data")
print("=" * 60)

# CSV
csv_path = f"data/all_products_full_{timestamp}.csv"
if normalized:
    fieldnames = list(normalized[0].keys())
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized)
    print(f"  CSV: {csv_path} ({len(normalized)} rows)")

# Also create a simple version
csv_simple = f"data/all_products_full.csv"
if normalized:
    with open(csv_simple, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized)
    print(f"  CSV (latest): {csv_simple}")

# JSON (full raw data)
json_path = f"data/all_products_full_{timestamp}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({
        "metadata": {
            "fetched_at": datetime.now().isoformat(),
            "total_products": len(seen_ids),
            "total_rows": len(normalized),
            "source": "api.panda.sa/v3",
            "store": "Panda",
        },
        "fustog_categories": fustog_cats,
        "panda_categories": panda_categories,
        "products": normalized,
    }, f, ensure_ascii=False, indent=2)
print(f"  JSON: {json_path}")

# JSON (latest)
json_simple = "data/all_products_full.json"
with open(json_simple, "w", encoding="utf-8") as f:
    json.dump({
        "metadata": {
            "fetched_at": datetime.now().isoformat(),
            "total_products": len(seen_ids),
            "total_rows": len(normalized),
            "source": "api.panda.sa/v3",
            "store": "Panda",
        },
        "fustog_categories": fustog_cats,
        "panda_categories": panda_categories,
        "products": normalized,
    }, f, ensure_ascii=False, indent=2)
print(f"  JSON (latest): {json_simple}")

# Raw API response
raw_path = f"data/panda_raw_products_{timestamp}.json"
with open(raw_path, "w", encoding="utf-8") as f:
    json.dump(all_products, f, ensure_ascii=False, indent=2)
print(f"  Raw JSON: {raw_path}")

client.close()

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Total unique products: {len(seen_ids)}")
print(f"  Total rows (with variants): {len(normalized)}")
print(f"  Categories: {len(cat_map)}")
if normalized:
    prices = [float(r["price"]) for r in normalized if r.get("price")]
    if prices:
        print(f"  Price range: {min(prices):.2f} - {max(prices):.2f} SAR")
    brands = set(r.get("brand_name", "") for r in normalized if r.get("brand_name"))
    print(f"  Unique brands: {len(brands)}")
    categories = set(r.get("category_name", "") for r in normalized if r.get("category_name"))
    print(f"  Unique categories: {len(categories)}")
print(f"\nFiles:")
print(f"  {csv_simple}")
print(f"  {json_simple}")
print(f"  {raw_path}")
print("\n=== DONE ===")
