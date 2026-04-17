#!/usr/bin/env python3
"""Fetch Tamimi products via ZopSmart API (shop.tamimimarkets.com/api)"""
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

client = httpx.Client(timeout=30.0, follow_redirects=True)
BASE = "https://shop.tamimimarkets.com/api"

headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
    "Accept-Language": "ar,en;q=0.9",
}

# ============================================================
# STEP 1: Discover API endpoints
# ============================================================
print("=" * 60)
print("STEP 1: Discover Tamimi ZopSmart API")
print("=" * 60)

# Try common ZopSmart API patterns
test_paths = [
    "/categories",
    "/products",
    "/catalog",
    "/v1/categories",
    "/v1/products",
    "/v2/categories",
    "/v2/products",
    "/categories?limit=5",
    "/products?limit=5",
    "/products?categoryId=247",
    "/products?category=pets",
    "/search?q=milk",
    "/search/products?q=milk",
    "/home",
    "/store",
    "/stores",
    "/config",
]

working_endpoints = []
for path in test_paths:
    try:
        r = client.get(f"{BASE}{path}", headers=headers, timeout=10)
        has_data = r.status_code == 200 and len(r.content) > 20
        if r.status_code != 404:
            print(f"  [{r.status_code}] GET {path} size={len(r.content)} {'DATA!' if has_data else ''}")
            if has_data:
                working_endpoints.append(path)
                try:
                    data = r.json()
                    if isinstance(data, dict):
                        print(f"       Keys: {list(data.keys())[:15]}")
                        for k in ["data", "products", "items", "results", "categories", "count", "totalCount"]:
                            if k in data:
                                val = data[k]
                                if isinstance(val, list):
                                    print(f"       .{k} = List[{len(val)}]")
                                    if val and isinstance(val[0], dict):
                                        print(f"       First keys: {list(val[0].keys())[:12]}")
                                elif isinstance(val, (int, float)):
                                    print(f"       .{k} = {val}")
                                elif isinstance(val, dict):
                                    print(f"       .{k} keys = {list(val.keys())[:10]}")
                    elif isinstance(data, list):
                        print(f"       List[{len(data)}]")
                        if data and isinstance(data[0], dict):
                            print(f"       First keys: {list(data[0].keys())[:12]}")
                except:
                    pass
    except Exception as e:
        print(f"  [ERR] {path} -> {type(e).__name__}")

# Also try POST
print("\n--- POST endpoints ---")
for path in ["/products", "/categories", "/search", "/catalog"]:
    try:
        r = client.post(f"{BASE}{path}", json={}, headers=headers, timeout=10)
        if r.status_code not in (404, 405):
            has_data = r.status_code == 200 and len(r.content) > 20
            print(f"  [{r.status_code}] POST {path} size={len(r.content)} {'DATA!' if has_data else ''}")
            if has_data:
                try:
                    data = r.json()
                    print(f"       {json.dumps(data, ensure_ascii=False)[:500]}")
                except:
                    pass
    except:
        pass

# ============================================================
# STEP 2: Try ZopSmart specific API patterns
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: ZopSmart-specific API patterns")
print("=" * 60)

# ZopSmart typically uses these patterns
zopsmart_patterns = [
    "/catalogue/products",
    "/catalogue/categories",
    "/catalogue/products?limit=5",
    "/catalogue/products?categoryId=247",
    "/public/categories",
    "/public/products",
    "/public/catalogue",
    "/v1/catalogue/products",
    "/v1/catalogue/categories",
    "/category/247/products",
    "/categories/247/products",
    "/category/pets/products",
]
for path in zopsmart_patterns:
    try:
        r = client.get(f"{BASE}{path}", headers=headers, timeout=10)
        has_data = r.status_code == 200 and len(r.content) > 20
        if r.status_code not in (404,):
            print(f"  [{r.status_code}] {path} size={len(r.content)} {'DATA!' if has_data else ''}")
            if has_data:
                working_endpoints.append(path)
                try:
                    data = r.json()
                    if isinstance(data, dict):
                        print(f"       Keys: {list(data.keys())[:15]}")
                except:
                    pass
    except Exception as e:
        print(f"  [ERR] {path} -> {type(e).__name__}")

# ============================================================
# STEP 3: Try fetching from category page HTML directly
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Fetch category pages for product data")
print("=" * 60)

# Load categories
with open("data/tamimi_categories.json", "r", encoding="utf-8") as f:
    categories = json.load(f)

# Get leaf categories (ones with products, prefer deep ones)
leaf_cats = [c for c in categories if c.get("productsCount", 0) > 0]
# Sort by productsCount ascending (try small ones first for testing)
leaf_cats.sort(key=lambda x: x.get("productsCount", 0))

print(f"  {len(leaf_cats)} categories with products")
print(f"  Testing with smallest categories first...")

html_headers = {
    "Accept": "text/html,application/xhtml+xml",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "ar,en;q=0.9",
}

# Test a few categories to understand URL structure
test_cats = leaf_cats[:5]
for cat in test_cats:
    slug = cat["slug"]
    name = cat["name"]
    cat_id = cat["id"]

    # Try different URL patterns
    urls_to_try = [
        f"https://shop.tamimimarkets.com/categories/{slug}",
        f"https://shop.tamimimarkets.com/category/{slug}",
        f"https://shop.tamimimarkets.com/c/{slug}",
        f"https://shop.tamimimarkets.com/categories/{cat_id}",
        f"https://shop.tamimimarkets.com/{slug}",
    ]

    print(f"\n  --- {name} (slug={slug}, id={cat_id}) ---")
    for url in urls_to_try:
        try:
            r = client.get(url, headers=html_headers, timeout=10)
            has_nd = "__NEXT_DATA__" in r.text if r.status_code == 200 else False
            print(f"    [{r.status_code}] {url.replace('https://shop.tamimimarkets.com', '')} {'HAS __NEXT_DATA__' if has_nd else ''}")

            if has_nd:
                # Extract and analyze __NEXT_DATA__
                html = r.text
                nd_start = html.index('__NEXT_DATA__')
                sc_start = html.rfind('<script', 0, nd_start)
                sc_end = html.find('</script>', nd_start)
                j_start = html.index('>', sc_start) + 1
                nd_json = html[j_start:sc_end].strip()
                nd = json.loads(nd_json)
                pp = nd.get("props", {}).get("pageProps", {})
                print(f"      pageProps keys: {list(pp.keys())}")
                data = pp.get("data", {})
                if isinstance(data, dict):
                    print(f"      data keys: {list(data.keys())[:15]}")
                    products = data.get("products", data.get("items", []))
                    if products:
                        print(f"      PRODUCTS FOUND: {len(products)}")
                        if products and isinstance(products[0], dict):
                            print(f"      Product keys: {list(products[0].keys())[:15]}")
                            print(f"      Sample: {json.dumps(products[0], ensure_ascii=False)[:500]}")
                    else:
                        # Show all data contents
                        for k, v in data.items():
                            if isinstance(v, list):
                                print(f"      .{k} = List[{len(v)}]")
                            elif isinstance(v, dict):
                                print(f"      .{k} = Dict({list(v.keys())[:8]})")
                            elif isinstance(v, (int, float)):
                                print(f"      .{k} = {v}")
                break  # Stop after first successful URL
        except Exception as e:
            print(f"    [ERR] {url.replace('https://shop.tamimimarkets.com', '')} -> {type(e).__name__}")

# ============================================================
# STEP 4: Try the /public path from runtimeConfig
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: Try /public paths")
print("=" * 60)

public_paths = [
    "/public/categories",
    "/public/products",
    "/public/products?limit=5",
    "/public/catalogue/products",
    "/public/catalogue/categories",
    "/public/search?q=milk",
]
for path in public_paths:
    try:
        url = f"https://shop.tamimimarkets.com{path}"
        r = client.get(url, headers=headers, timeout=10)
        has_data = r.status_code == 200 and len(r.content) > 20
        if r.status_code not in (404,):
            print(f"  [{r.status_code}] {path} size={len(r.content)} {'DATA!' if has_data else ''}")
            if has_data:
                try:
                    data = r.json()
                    if isinstance(data, dict):
                        print(f"       Keys: {list(data.keys())[:15]}")
                    print(f"       Preview: {json.dumps(data, ensure_ascii=False)[:500]}")
                except:
                    print(f"       Raw: {r.content[:300]}")
    except Exception as e:
        print(f"  [ERR] {path} -> {type(e).__name__}")

client.close()
print("\n=== DONE ===")
