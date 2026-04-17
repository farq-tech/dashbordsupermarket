#!/usr/bin/env python3
"""Scrape Tamimi products from shop.tamimimarkets.com via __NEXT_DATA__"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import os
import csv
import time
import re
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

client = httpx.Client(timeout=30.0, follow_redirects=True)
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "ar,en;q=0.9",
}

# ============================================================
# STEP 1: Get categories from main categories page
# ============================================================
print("=" * 60)
print("STEP 1: Get Tamimi categories from __NEXT_DATA__")
print("=" * 60)

r = client.get("https://shop.tamimimarkets.com/categories", headers=headers, timeout=20)
print(f"  Status: {r.status_code}, Size: {len(r.content)}")

html = r.text
categories = []

if "__NEXT_DATA__" in html:
    start = html.index('__NEXT_DATA__')
    # Find the JSON between <script> tags
    script_start = html.rfind('<script', 0, start)
    script_end = html.find('</script>', start)
    json_start = html.index('>', script_start) + 1
    json_text = html[json_start:script_end].strip()

    try:
        next_data = json.loads(json_text)
        # Save raw __NEXT_DATA__
        with open("data/tamimi_next_data.json", "w", encoding="utf-8") as f:
            json.dump(next_data, f, ensure_ascii=False, indent=2)
        print("  Saved __NEXT_DATA__ to data/tamimi_next_data.json")

        # Navigate the structure to find categories
        page_props = next_data.get("props", {}).get("pageProps", {})
        print(f"  pageProps keys: {list(page_props.keys())}")

        cats = page_props.get("categories", page_props.get("data", {}).get("categories", []))
        if not cats:
            # Try other possible paths
            for key in page_props:
                val = page_props[key]
                if isinstance(val, list) and val and isinstance(val[0], dict):
                    if "name" in val[0] or "slug" in val[0]:
                        cats = val
                        print(f"  Found categories in pageProps.{key}")
                        break
                elif isinstance(val, dict):
                    for k2 in val:
                        v2 = val[k2]
                        if isinstance(v2, list) and v2 and isinstance(v2[0], dict):
                            if "name" in v2[0] or "slug" in v2[0]:
                                cats = v2
                                print(f"  Found categories in pageProps.{key}.{k2}")
                                break

        if cats:
            print(f"  Found {len(cats)} top-level categories")

            def collect_categories(cat_list, parent=""):
                for cat in cat_list:
                    slug = cat.get("slug", "")
                    name = cat.get("name", "")
                    cat_id = cat.get("id", "")
                    count = cat.get("productsCount", 0)
                    categories.append({
                        "id": cat_id,
                        "name": name,
                        "slug": slug,
                        "parent": parent,
                        "productsCount": count,
                    })
                    subs = cat.get("subCategories", cat.get("children", []))
                    if subs:
                        collect_categories(subs, name)

            collect_categories(cats)
            print(f"  Total categories (with subs): {len(categories)}")
            for cat in categories[:10]:
                print(f"    {cat['name']} ({cat['slug']}) - {cat['productsCount']} products")
        else:
            print("  Could not find categories in __NEXT_DATA__")
            print(f"  Full pageProps keys: {json.dumps(list(page_props.keys()))}")
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
else:
    print("  No __NEXT_DATA__ found!")

if not categories:
    print("\nTrying alternative: fetch API endpoints...")
    # Try common Next.js API routes
    api_paths = [
        "/_next/data/*/categories.json",
        "/api/categories",
        "/api/v1/categories",
    ]
    # Try to find buildId
    build_id_match = re.search(r'"buildId":"([^"]+)"', html)
    if build_id_match:
        build_id = build_id_match.group(1)
        print(f"  Build ID: {build_id}")
        r2 = client.get(f"https://shop.tamimimarkets.com/_next/data/{build_id}/categories.json", headers=headers)
        print(f"  _next/data categories: {r2.status_code}, size={len(r2.content)}")
        if r2.status_code == 200:
            try:
                data = r2.json()
                with open("data/tamimi_categories_api.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except:
                pass

# ============================================================
# STEP 2: Fetch products from each category page
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Fetching Tamimi products from category pages")
print("=" * 60)

all_products = []
seen_ids = set()

# Filter to categories that have products
cats_with_products = [c for c in categories if c.get("productsCount", 0) > 0]
print(f"  Categories with products: {len(cats_with_products)}")

# Try getting buildId for _next/data API
build_id = None
build_id_match = re.search(r'"buildId":"([^"]+)"', html)
if build_id_match:
    build_id = build_id_match.group(1)
    print(f"  Build ID: {build_id}")

for i, cat in enumerate(cats_with_products):
    slug = cat["slug"]
    cat_name = cat["name"]
    expected = cat.get("productsCount", 0)

    print(f"\n  [{i+1}/{len(cats_with_products)}] {cat_name} ({slug}) - expect {expected} products")

    page = 1
    cat_products = []

    while True:
        try:
            # Method 1: Try _next/data API (faster, JSON)
            if build_id:
                url = f"https://shop.tamimimarkets.com/_next/data/{build_id}/categories/{slug}.json"
                params = {"page": page} if page > 1 else {}
                if slug:
                    params["slug"] = slug
                r = client.get(url, headers=headers, params=params, timeout=15)

                if r.status_code == 200:
                    try:
                        data = r.json()
                        page_props = data.get("pageProps", {})
                        products = page_props.get("products", page_props.get("data", {}).get("products", []))

                        if not products:
                            # Try other keys
                            for key in page_props:
                                val = page_props[key]
                                if isinstance(val, list) and val and isinstance(val[0], dict):
                                    if any(k in val[0] for k in ["price", "name", "sku", "barcode"]):
                                        products = val
                                        break
                                elif isinstance(val, dict):
                                    for k2, v2 in val.items():
                                        if isinstance(v2, list) and v2 and isinstance(v2[0], dict):
                                            if any(k in v2[0] for k in ["price", "name", "sku"]):
                                                products = v2
                                                break

                        if products:
                            new = 0
                            for p in products:
                                pid = p.get("id", p.get("sku", p.get("barcode", "")))
                                if pid and pid not in seen_ids:
                                    seen_ids.add(pid)
                                    p["_category"] = cat_name
                                    p["_category_id"] = cat.get("id", "")
                                    cat_products.append(p)
                                    new += 1

                            print(f"    Page {page}: +{new} products (cat total: {len(cat_products)})")

                            # Check pagination
                            pagination = page_props.get("pagination", page_props.get("meta", {}))
                            total_pages = pagination.get("totalPages", pagination.get("last_page", 1))
                            if page >= total_pages or not products:
                                break
                            page += 1
                            time.sleep(0.5)
                            continue
                        else:
                            if page == 1:
                                # Fall through to HTML scraping
                                pass
                            else:
                                break
                    except json.JSONDecodeError:
                        pass

            # Method 2: Scrape HTML page
            url = f"https://shop.tamimimarkets.com/categories/{slug}"
            params = {"page": page} if page > 1 else {}
            r = client.get(url, headers=headers, params=params, timeout=15)

            if r.status_code != 200:
                print(f"    Page {page}: HTTP {r.status_code}")
                break

            cat_html = r.text
            if "__NEXT_DATA__" not in cat_html:
                print(f"    Page {page}: No __NEXT_DATA__")
                break

            # Extract __NEXT_DATA__
            nd_start = cat_html.index('__NEXT_DATA__')
            sc_start = cat_html.rfind('<script', 0, nd_start)
            sc_end = cat_html.find('</script>', nd_start)
            j_start = cat_html.index('>', sc_start) + 1
            nd_json = cat_html[j_start:sc_end].strip()

            try:
                nd = json.loads(nd_json)
                pp = nd.get("props", {}).get("pageProps", {})

                products = pp.get("products", [])
                if not products:
                    # Search in all keys
                    for key in pp:
                        val = pp[key]
                        if isinstance(val, list) and val and isinstance(val[0], dict):
                            if any(k in val[0] for k in ["price", "name", "sku", "barcode", "title"]):
                                products = val
                                break
                        elif isinstance(val, dict) and "products" in val:
                            products = val["products"]
                            break

                if products:
                    new = 0
                    for p in products:
                        pid = p.get("id", p.get("sku", p.get("barcode", "")))
                        if pid and pid not in seen_ids:
                            seen_ids.add(pid)
                            p["_category"] = cat_name
                            p["_category_id"] = cat.get("id", "")
                            cat_products.append(p)
                            new += 1

                    print(f"    Page {page}: +{new} products (cat total: {len(cat_products)})")

                    # Check for pagination info
                    pagination = pp.get("pagination", pp.get("meta", {}))
                    total_pages = pagination.get("totalPages", pagination.get("last_page", 1))
                    has_more = pp.get("hasMore", False)

                    if (page >= total_pages and total_pages > 0) or (not products and page > 1):
                        break
                    if not has_more and total_pages <= 1 and page > 1:
                        break

                    page += 1
                    time.sleep(0.5)
                else:
                    if page == 1:
                        print(f"    No products found in pageProps. Keys: {list(pp.keys())}")
                        # Save for debugging first failed category
                        if i < 3:
                            with open(f"data/tamimi_debug_{slug}.json", "w", encoding="utf-8") as f:
                                json.dump(pp, f, ensure_ascii=False, indent=2)
                            print(f"    Saved debug to data/tamimi_debug_{slug}.json")
                    break
            except json.JSONDecodeError:
                print(f"    Page {page}: JSON parse error")
                break

        except Exception as e:
            print(f"    Page {page}: ERROR {type(e).__name__}: {e}")
            break

    all_products.extend(cat_products)
    print(f"    Category done: {len(cat_products)} products")

    # Save progress every 10 categories
    if (i + 1) % 10 == 0:
        print(f"\n  --- Progress: {len(all_products)} total products from {i+1} categories ---")

print(f"\n  TOTAL: {len(all_products)} products from {len(cats_with_products)} categories")

# ============================================================
# STEP 3: Normalize and export
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Normalizing and exporting Tamimi products")
print("=" * 60)

normalized = []
for p in all_products:
    # Tamimi product structure may vary - adapt
    row = {
        "product_id": p.get("id", p.get("productId", "")),
        "sku": p.get("sku", p.get("barcode", "")),
        "name_ar": p.get("name", p.get("title", p.get("nameAr", ""))),
        "name_en": p.get("nameEn", p.get("englishName", "")),
        "category_id": p.get("_category_id", ""),
        "category_name": p.get("_category", ""),
        "parent_category": "",
        "brand_id": "",
        "brand_name": p.get("brand", p.get("brandName", "")),
        "description": p.get("description", ""),
        "image_url": p.get("image", p.get("imageUrl", p.get("thumbnail", ""))),
        "price": p.get("price", p.get("originalPrice", "")),
        "sale_price": p.get("salePrice", p.get("discountedPrice", p.get("offerPrice", ""))),
        "currency": "SAR",
        "size": p.get("size", p.get("weight", "")),
        "unit": p.get("unit", p.get("unitOfMeasure", "")),
        "in_stock": 1 if p.get("inStock", p.get("available", True)) else 0,
        "variety_id": "",
        "barcode": p.get("barcode", p.get("sku", "")),
        "store": "tamimi",
        "store_name": "Tamimi Markets",
        "city": "Riyadh",
        "source_endpoint": "shop.tamimimarkets.com",
        "fetched_at": datetime.now().isoformat(),
        "varieties_count": 1,
    }
    normalized.append(row)

print(f"  Normalized: {len(normalized)} rows")

if normalized:
    # CSV
    csv_path = f"data/tamimi_products_{timestamp}.csv"
    fieldnames = list(normalized[0].keys())
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized)
    print(f"  CSV: {csv_path}")

    # JSON
    json_path = f"data/tamimi_products_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "total_products": len(normalized),
                "source": "shop.tamimimarkets.com",
                "store": "Tamimi Markets",
            },
            "categories": categories,
            "products": normalized,
        }, f, ensure_ascii=False, indent=2)
    print(f"  JSON: {json_path}")

    # Raw
    raw_path = f"data/tamimi_raw_{timestamp}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"  Raw: {raw_path}")

# Save categories
with open("data/tamimi_categories.json", "w", encoding="utf-8") as f:
    json.dump(categories, f, ensure_ascii=False, indent=2)
print(f"  Categories: data/tamimi_categories.json ({len(categories)} categories)")

client.close()

print("\n" + "=" * 60)
print("TAMIMI SUMMARY")
print("=" * 60)
print(f"  Total products: {len(normalized)}")
if normalized:
    prices = [float(r["price"]) for r in normalized if r.get("price") and str(r["price"]).replace(".", "").isdigit()]
    if prices:
        print(f"  Price range: {min(prices):.2f} - {max(prices):.2f} SAR")
    brands = set(r.get("brand_name") for r in normalized if r.get("brand_name"))
    print(f"  Unique brands: {len(brands)}")
    cats_set = set(r.get("category_name") for r in normalized if r.get("category_name"))
    print(f"  Unique categories: {len(cats_set)}")
print("\n=== DONE ===")
