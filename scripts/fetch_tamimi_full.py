#!/usr/bin/env python3
"""Fetch ALL Tamimi products by scraping category pages via __NEXT_DATA__"""
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
BASE = "https://shop.tamimimarkets.com"

client = httpx.Client(timeout=30.0, follow_redirects=True)
html_headers = {
    "Accept": "text/html,application/xhtml+xml",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "ar,en;q=0.9",
}

# ============================================================
# STEP 1: Get all leaf categories
# ============================================================
print("=" * 60)
print("STEP 1: Get leaf categories (deepest level with products)")
print("=" * 60)

with open("data/tamimi_categories.json", "r", encoding="utf-8") as f:
    all_cats = json.load(f)

# We want leaf categories (no children) that have products
# From the categories JSON, find ones that are at the deepest level
leaf_cats = [c for c in all_cats if c.get("productsCount", 0) > 0]

# Check for parent/child overlap - prefer children over parents
parent_names = set()
for c in all_cats:
    if c.get("parent"):
        parent_names.add(c["parent"])

# Remove parent categories that have children with products
# (to avoid double-counting)
leaf_only = []
slug_set = set()
for c in leaf_cats:
    # Skip if this category's name appears as a parent of another category
    has_children = any(
        c2.get("parent") == c["name"] and c2.get("productsCount", 0) > 0
        for c2 in all_cats if c2["slug"] != c["slug"]
    )
    if not has_children:
        if c["slug"] not in slug_set:
            slug_set.add(c["slug"])
            leaf_only.append(c)

print(f"  Total categories with products: {len(leaf_cats)}")
print(f"  Leaf categories (no children): {len(leaf_only)}")
total_expected = sum(c.get("productsCount", 0) for c in leaf_only)
print(f"  Total expected products: {total_expected}")

# Sort by productsCount descending to get big categories first
leaf_only.sort(key=lambda x: x.get("productsCount", 0), reverse=True)
for c in leaf_only[:10]:
    print(f"    {c['name']} ({c['slug']}): {c['productsCount']} products")

# ============================================================
# STEP 2: Fetch products from each leaf category
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Fetching products from all leaf categories")
print("=" * 60)

all_products = []
seen_ids = set()
failed_cats = []

def extract_products_from_page(html_text):
    """Extract products from __NEXT_DATA__ in HTML"""
    if "__NEXT_DATA__" not in html_text:
        return [], 0, 0, 0
    nd_start = html_text.index('__NEXT_DATA__')
    sc_start = html_text.rfind('<script', 0, nd_start)
    sc_end = html_text.find('</script>', nd_start)
    j_start = html_text.index('>', sc_start) + 1
    nd = json.loads(html_text[j_start:sc_end].strip())
    pp = nd.get("props", {}).get("pageProps", {})
    layouts_resp = pp.get("layouts", {})

    if not isinstance(layouts_resp, dict):
        return [], 0, 0, 0

    page_data = layouts_resp.get("data", {}).get("page", {})
    page_layouts = page_data.get("layouts", [])

    for layout in page_layouts:
        if layout.get("name") == "ProductCollection":
            collection = layout.get("value", {}).get("collection", {})
            products = collection.get("product", [])  # Note: singular "product"
            count = collection.get("count", 0)
            limit = collection.get("limit", 20)
            offset = collection.get("offset", 0)
            return products, count, limit, offset

    return [], 0, 0, 0

for i, cat in enumerate(leaf_only):
    slug = cat["slug"]
    name = cat["name"]
    expected = cat.get("productsCount", 0)

    cat_products = []
    offset = 0
    limit = 20
    page_num = 1

    while True:
        try:
            url = f"{BASE}/category/{slug}"
            params = {}
            if offset > 0:
                params["offset"] = offset
                params["limit"] = limit

            r = client.get(url, headers=html_headers, params=params, timeout=20)

            if r.status_code != 200:
                if page_num == 1:
                    failed_cats.append((slug, name, f"HTTP {r.status_code}"))
                break

            products, total_count, page_limit, page_offset = extract_products_from_page(r.text)

            if not products:
                if page_num == 1:
                    # Try without params
                    pass
                break

            new = 0
            for p in products:
                pid = p.get("id")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    p["_category"] = name
                    p["_category_slug"] = slug
                    p["_parent_category"] = cat.get("parent", "")
                    cat_products.append(p)
                    new += 1

            if page_num == 1 or page_num % 5 == 0:
                print(f"  [{i+1}/{len(leaf_only)}] {name} p{page_num}: +{new} (total: {len(cat_products)}/{total_count})")

            # Check if we need more pages
            if len(products) < page_limit or len(cat_products) >= total_count:
                break

            offset += page_limit
            page_num += 1
            time.sleep(0.3)

        except Exception as e:
            if page_num == 1:
                failed_cats.append((slug, name, str(e)))
            print(f"  [{i+1}/{len(leaf_only)}] {name}: ERROR {e}")
            break

    all_products.extend(cat_products)

    if (i + 1) % 20 == 0:
        print(f"\n  === Progress: {len(all_products)} unique products from {i+1}/{len(leaf_only)} categories ===\n")

print(f"\n  TOTAL: {len(all_products)} unique products from {len(leaf_only)} categories")
if failed_cats:
    print(f"  Failed categories: {len(failed_cats)}")

# ============================================================
# STEP 3: Normalize and export
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Normalizing and exporting")
print("=" * 60)

normalized = []
for p in all_products:
    variants = p.get("variants", [])
    primary_cat = p.get("primaryCategory", {}) or {}
    parent_cat = primary_cat.get("parentCategory", {}) or {}

    # Get brand
    brand_name = ""
    brand = p.get("brand")
    if isinstance(brand, dict):
        brand_name = brand.get("name", "")
    elif isinstance(brand, str):
        brand_name = brand

    # Base row
    base = {
        "product_id": p.get("id", ""),
        "sku": p.get("clientItemId", ""),
        "name_ar": p.get("name", ""),
        "name_en": "",
        "category_id": primary_cat.get("id", p.get("_category_slug", "")),
        "category_name": primary_cat.get("name", p.get("_category", "")),
        "parent_category": parent_cat.get("name", p.get("_parent_category", "")),
        "brand_id": "",
        "brand_name": brand_name,
        "description": "",
        "store": "tamimi",
        "store_name": "Tamimi Markets",
        "city": "Riyadh",
        "source_endpoint": "shop.tamimimarkets.com",
        "fetched_at": datetime.now().isoformat(),
        "varieties_count": len(variants),
    }

    if variants:
        for var in variants:
            store_data = var.get("storeSpecificData", [])
            first_store = store_data[0] if store_data else {}
            images = var.get("images", [])
            barcodes = var.get("barcodes", [])

            row = dict(base)
            row["variety_id"] = var.get("id", "")
            row["barcode"] = barcodes[0] if barcodes else ""
            row["image_url"] = images[0] if images else ""
            row["price"] = first_store.get("mrp", "")
            row["sale_price"] = ""
            discount = first_store.get("discount", "0")
            if discount and float(discount) > 0:
                mrp = float(first_store.get("mrp", 0))
                row["sale_price"] = str(round(mrp - float(discount), 2))
            row["currency"] = "SAR"
            row["size"] = var.get("name", "")
            row["unit"] = ""
            row["in_stock"] = 1 if first_store.get("stock", 0) > 0 else 0
            normalized.append(row)
    else:
        base["variety_id"] = ""
        base["barcode"] = ""
        base["image_url"] = ""
        base["price"] = ""
        base["sale_price"] = ""
        base["currency"] = "SAR"
        base["size"] = ""
        base["unit"] = ""
        base["in_stock"] = 1
        normalized.append(base)

print(f"  Normalized: {len(normalized)} rows from {len(all_products)} products")

if normalized:
    # CSV
    csv_path = f"data/tamimi_products_{timestamp}.csv"
    fieldnames = list(normalized[0].keys())
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized)
    print(f"  CSV: {csv_path} ({len(normalized)} rows)")

    # Also save as latest
    csv_latest = "data/tamimi_products.csv"
    with open(csv_latest, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized)
    print(f"  CSV (latest): {csv_latest}")

    # JSON
    json_path = f"data/tamimi_products_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "total_products": len(all_products),
                "total_rows": len(normalized),
                "source": "shop.tamimimarkets.com",
                "store": "Tamimi Markets",
            },
            "categories": all_cats,
            "products": normalized,
        }, f, ensure_ascii=False, indent=2)
    print(f"  JSON: {json_path}")

    # Raw
    raw_path = f"data/tamimi_raw_{timestamp}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"  Raw: {raw_path}")

# Summary
print("\n" + "=" * 60)
print("TAMIMI SUMMARY")
print("=" * 60)
print(f"  Total unique products: {len(all_products)}")
print(f"  Total rows (with variants): {len(normalized)}")
if normalized:
    prices = [float(r["price"]) for r in normalized if r.get("price") and str(r["price"]).replace(".", "").isdigit()]
    if prices:
        print(f"  Price range: {min(prices):.2f} - {max(prices):.2f} SAR")
    brands = set(r.get("brand_name") for r in normalized if r.get("brand_name"))
    print(f"  Unique brands: {len(brands)}")
    cats_set = set(r.get("category_name") for r in normalized if r.get("category_name"))
    print(f"  Unique categories: {len(cats_set)}")
if failed_cats:
    print(f"\n  Failed categories ({len(failed_cats)}):")
    for slug, name, err in failed_cats[:10]:
        print(f"    {name} ({slug}): {err}")
print("\n=== DONE ===")

client.close()
