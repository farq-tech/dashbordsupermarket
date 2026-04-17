#!/usr/bin/env python3
"""Continue fetching remaining products from page 298+"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import os
import csv
import time
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

PANDA_HEADERS = {
    "Accept": "application/json;charset=UTF-8",
    "User-Agent": "okhttp/5.0.0-alpha.6",
    "x-language": "ar",
    "x-pandaclick-agent": "4",
    "x-panda-source": "PandaClick",
}

client = httpx.Client(timeout=30.0, follow_redirects=True)

# Load existing products
print("Loading existing products...")
with open("data/panda_raw_products_20260314_172817.json", "r", encoding="utf-8") as f:
    all_products = json.load(f)
print(f"  Existing: {len(all_products)}")

existing_ids = {p.get("id") for p in all_products}

# Continue from page 298
print(f"\nContinuing from page 298...")
page = 298
empty_streak = 0

while page <= 600:
    try:
        r = client.get("https://api.panda.sa/v3/products",
            headers=PANDA_HEADERS,
            params={"page": page, "per_page": 50},
            timeout=20)

        if r.status_code != 200:
            print(f"  Page {page}: HTTP {r.status_code}, stopping")
            break

        data = r.json().get("data", {})
        products = data.get("products", [])

        if not products:
            empty_streak += 1
            if empty_streak >= 3:
                print(f"  Page {page}: 3 empty pages in a row, done!")
                break
            page += 1
            continue

        empty_streak = 0
        new_count = 0
        for p in products:
            if p.get("id") not in existing_ids:
                all_products.append(p)
                existing_ids.add(p.get("id"))
                new_count += 1

        if page % 10 == 0 or page <= 300:
            print(f"  Page {page}: +{new_count} new (total: {len(all_products)})")

        next_page = data.get("next_page")
        if not next_page:
            print(f"  No more pages after {page}")
            break

        page += 1
        time.sleep(0.3)

    except Exception as e:
        print(f"  Page {page}: ERROR {e}")
        time.sleep(2)
        page += 1

print(f"\n  TOTAL: {len(all_products)} products ({len(existing_ids)} unique)")

# Normalize
print("\nNormalizing...")
normalized = []
seen = set()

for p in all_products:
    pid = p.get("id")
    if pid in seen:
        continue
    seen.add(pid)

    brand = p.get("brand", {}) or {}
    category = p.get("category", {}) or {}
    varieties = p.get("varieties", []) or []
    first_var = varieties[0] if varieties else {}

    image_url = ""
    if first_var.get("imagePaths"):
        paths = first_var["imagePaths"]
        if isinstance(paths, list) and paths:
            image_url = paths[0]

    row = {
        "product_id": pid,
        "sku": first_var.get("barcode", ""),
        "name_ar": p.get("name", ""),
        "name_en": "",
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

    if len(varieties) > 1:
        for var in varieties:
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

print(f"  Unique: {len(seen)}, Rows: {len(normalized)}")

# Export
print("\nExporting...")
csv_path = "data/all_products_full.csv"
fieldnames = list(normalized[0].keys()) if normalized else []
with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(normalized)
print(f"  CSV: {csv_path} ({len(normalized)} rows)")

# Load Fustog categories for the JSON
FUSTOG_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16)",
    "Accept": "application/json, */*;q=0.5",
    "Accept-Encoding": "identity",
}
r = client.get("https://api.fustog.app/api/v2/category/Categories", headers=FUSTOG_HEADERS)
fustog_cats = r.json()

r = client.get("https://api.panda.sa/v3/categories", headers=PANDA_HEADERS)
panda_cats = r.json().get("data", {}).get("categories", [])

json_path = "data/all_products_full.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({
        "metadata": {
            "fetched_at": datetime.now().isoformat(),
            "total_products": len(seen),
            "total_rows": len(normalized),
            "source": "api.panda.sa/v3",
            "store": "Panda",
        },
        "fustog_categories": fustog_cats,
        "panda_categories": panda_cats,
        "products": normalized,
    }, f, ensure_ascii=False, indent=2)
print(f"  JSON: {json_path}")

# Raw
raw_path = f"data/panda_raw_all_{timestamp}.json"
with open(raw_path, "w", encoding="utf-8") as f:
    json.dump(all_products, f, ensure_ascii=False, indent=2)
print(f"  Raw: {raw_path}")

client.close()

# Summary
print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)
print(f"  Total unique products: {len(seen)}")
print(f"  Total rows (with variants): {len(normalized)}")
prices = [float(r["price"]) for r in normalized if r.get("price")]
if prices:
    print(f"  Price range: {min(prices):.2f} - {max(prices):.2f} SAR")
brands = set(r.get("brand_name") for r in normalized if r.get("brand_name"))
print(f"  Unique brands: {len(brands)}")
categories = set(r.get("category_name") for r in normalized if r.get("category_name"))
print(f"  Unique categories: {len(categories)}")
print(f"\nOutput files:")
print(f"  data/all_products_full.csv")
print(f"  data/all_products_full.json")
print("\n=== DONE ===")
