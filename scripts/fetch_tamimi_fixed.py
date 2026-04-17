#!/usr/bin/env python3
"""Fetch Tamimi products - 1 page per category (SSR only gives first page)"""
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

# Load categories
with open("data/tamimi_categories.json", "r", encoding="utf-8") as f:
    all_cats = json.load(f)

# Get leaf categories only (no children with products)
leaf_only = []
slug_set = set()
for c in all_cats:
    if c.get("productsCount", 0) <= 0:
        continue
    has_children = any(
        c2.get("parent") == c["name"] and c2.get("productsCount", 0) > 0
        for c2 in all_cats if c2["slug"] != c["slug"]
    )
    if not has_children and c["slug"] not in slug_set:
        slug_set.add(c["slug"])
        leaf_only.append(c)

print(f"Leaf categories: {len(leaf_only)}")
leaf_only.sort(key=lambda x: x.get("productsCount", 0), reverse=True)

all_products = []
seen_ids = set()

for i, cat in enumerate(leaf_only):
    slug = cat["slug"]
    name = cat["name"]
    try:
        r = client.get(f"{BASE}/category/{slug}", headers=html_headers, timeout=15)
        if r.status_code != 200 or "__NEXT_DATA__" not in r.text:
            continue

        html = r.text
        nd_start = html.index('__NEXT_DATA__')
        sc_start = html.rfind('<script', 0, nd_start)
        sc_end = html.find('</script>', nd_start)
        j_start = html.index('>', sc_start) + 1
        nd = json.loads(html[j_start:sc_end].strip())

        layouts = nd.get("props", {}).get("pageProps", {}).get("layouts", {})
        if not isinstance(layouts, dict):
            continue
        page_layouts = layouts.get("data", {}).get("page", {}).get("layouts", [])

        for layout in page_layouts:
            if layout.get("name") == "ProductCollection":
                collection = layout.get("value", {}).get("collection", {})
                products = collection.get("product", [])
                if products:
                    new = 0
                    for p in products:
                        pid = p.get("id")
                        if pid and pid not in seen_ids:
                            seen_ids.add(pid)
                            p["_category"] = name
                            p["_category_slug"] = slug
                            p["_parent"] = cat.get("parent", "")
                            all_products.append(p)
                            new += 1
                    print(f"  [{i+1}/{len(leaf_only)}] {name}: +{new} (total: {len(all_products)})")
                else:
                    print(f"  [{i+1}/{len(leaf_only)}] {name}: 0 products")
                break
        time.sleep(0.3)
    except Exception as e:
        print(f"  [{i+1}/{len(leaf_only)}] {name}: ERR {e}")

print(f"\nTOTAL: {len(all_products)} unique products")

# Normalize
normalized = []
for p in all_products:
    variants = p.get("variants", [])
    pcat = p.get("primaryCategory", {}) or {}
    parent_cat = pcat.get("parentCategory", {}) or {}
    brand = p.get("brand")
    brand_name = brand.get("name", "") if isinstance(brand, dict) else (brand or "")

    base = {
        "product_id": p.get("id", ""),
        "sku": p.get("clientItemId", ""),
        "name_ar": p.get("name", ""),
        "name_en": "",
        "category_id": pcat.get("id", ""),
        "category_name": pcat.get("name", p.get("_category", "")),
        "parent_category": parent_cat.get("name", p.get("_parent", "")),
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
            sd = (var.get("storeSpecificData") or [{}])[0] if var.get("storeSpecificData") else {}
            imgs = var.get("images") or []
            bcs = var.get("barcodes") or []
            row = dict(base)
            row["variety_id"] = var.get("id", "")
            row["barcode"] = bcs[0] if bcs else ""
            row["image_url"] = imgs[0] if imgs else ""
            row["price"] = sd.get("mrp", "")
            disc = float(sd.get("discount", "0") or "0")
            mrp = float(sd.get("mrp", "0") or "0")
            row["sale_price"] = str(round(mrp - disc, 2)) if disc > 0 else ""
            row["currency"] = "SAR"
            row["size"] = var.get("name", "")
            row["unit"] = ""
            row["in_stock"] = 1 if sd.get("stock", 0) > 0 else 0
            normalized.append(row)
    else:
        base.update({"variety_id":"","barcode":"","image_url":"","price":"","sale_price":"","currency":"SAR","size":"","unit":"","in_stock":1})
        normalized.append(base)

print(f"Normalized: {len(normalized)} rows")

if normalized:
    fn = list(normalized[0].keys())
    for path in [f"data/tamimi_products_{timestamp}.csv", "data/tamimi_products.csv"]:
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fn)
            w.writeheader()
            w.writerows(normalized)
    print(f"CSV: data/tamimi_products.csv ({len(normalized)} rows)")

    with open("data/tamimi_products.json", "w", encoding="utf-8") as f:
        json.dump({"metadata":{"fetched_at":datetime.now().isoformat(),"total":len(all_products),"rows":len(normalized),"store":"Tamimi"},"products":normalized}, f, ensure_ascii=False, indent=2)
    with open(f"data/tamimi_raw_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"JSON: data/tamimi_products.json")

    prices = [float(r["price"]) for r in normalized if r.get("price") and str(r["price"]).replace(".","").isdigit()]
    if prices:
        print(f"Price range: {min(prices):.2f} - {max(prices):.2f} SAR")
    brands = set(r["brand_name"] for r in normalized if r.get("brand_name"))
    print(f"Brands: {len(brands)}, Categories: {len(set(r['category_name'] for r in normalized if r.get('category_name')))}")

client.close()
print("=== DONE ===")
