#!/usr/bin/env python3
"""Deep dive into Tamimi API - find product endpoints"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import os
import re
import time
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)

client = httpx.Client(timeout=30.0, follow_redirects=True)
BASE = "https://shop.tamimimarkets.com"

headers_json = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
    "Accept-Language": "ar,en;q=0.9",
}
headers_html = {
    "Accept": "text/html,application/xhtml+xml",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "ar,en;q=0.9",
}

# ============================================================
# STEP 1: Inspect layouts structure from category page
# ============================================================
print("=" * 60)
print("STEP 1: Inspect category page layouts")
print("=" * 60)

r = client.get(f"{BASE}/category/pets", headers=headers_html, timeout=15)
html = r.text

if "__NEXT_DATA__" in html:
    nd_start = html.index('__NEXT_DATA__')
    sc_start = html.rfind('<script', 0, nd_start)
    sc_end = html.find('</script>', nd_start)
    j_start = html.index('>', sc_start) + 1
    nd = json.loads(html[j_start:sc_end].strip())
    pp = nd.get("props", {}).get("pageProps", {})

    # Save layouts
    layouts = pp.get("layouts", [])
    print(f"  Layouts count: {len(layouts)}")
    with open("data/tamimi_layouts_debug.json", "w", encoding="utf-8") as f:
        json.dump(pp, f, ensure_ascii=False, indent=2)

    for i, layout in enumerate(layouts):
        print(f"\n  Layout {i}:")
        if isinstance(layout, dict):
            print(f"    Keys: {list(layout.keys())[:15]}")
            ltype = layout.get("type", layout.get("component", layout.get("name", "")))
            print(f"    Type/Component: {ltype}")
            # Look for API URLs or data sources
            layout_str = json.dumps(layout, default=str)
            api_refs = re.findall(r'(?:api|url|endpoint|src|href)["\s:]+([^"}\s,]+)', layout_str, re.IGNORECASE)
            if api_refs:
                print(f"    API refs: {api_refs[:5]}")

    # Check query
    query = pp.get("query", {})
    print(f"\n  Query: {json.dumps(query, ensure_ascii=False)}")

# ============================================================
# STEP 2: Look for JavaScript API calls in the page source
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Find API calls in JS bundles")
print("=" * 60)

# Find JS bundle URLs
js_urls = set(re.findall(r'/_next/static/[^"\']+\.js', html))
print(f"  Found {len(js_urls)} JS bundles")

# Download and search a few for API endpoint patterns
api_patterns = set()
for js_url in sorted(js_urls)[:15]:  # Check first 15 bundles
    try:
        r = client.get(f"{BASE}{js_url}", timeout=10)
        if r.status_code == 200:
            js = r.text
            # Look for API patterns
            matches = re.findall(r'["\'](?:/api/[^"\']{3,80})["\']', js)
            matches += re.findall(r'["\'](?:api/[^"\']{3,80})["\']', js)
            matches += re.findall(r'fetch\(["\']([^"\']+)["\']', js)
            matches += re.findall(r'axios[^(]*\(["\']([^"\']+)["\']', js)
            matches += re.findall(r'\.get\(["\']([^"\']+)["\']', js)
            matches += re.findall(r'\.post\(["\']([^"\']+)["\']', js)
            # ZopSmart specific
            matches += re.findall(r'(?:catalogue|catalog|products?|categories)[^"\']*["\']', js)

            for m in matches:
                m = m.strip('"\'')
                if len(m) > 3 and not m.startswith('//') and 'webpack' not in m:
                    api_patterns.add(m)
    except:
        pass

print(f"\n  Found API patterns:")
for p in sorted(api_patterns):
    print(f"    {p}")

# ============================================================
# STEP 3: Try discovered API endpoints
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Try API endpoints from JS analysis + ZopSmart defaults")
print("=" * 60)

# Common ZopSmart API patterns
endpoints_to_try = [
    # From runtimeConfig API_URL = /api
    "/api/categories",
    "/api/categories?limit=100",
    "/api/products",
    "/api/products?limit=5",
    "/api/products?limit=5&categoryId=247",
    "/api/products?limit=5&category=pets",
    "/api/catalogue/products",
    "/api/catalogue/products?limit=5",
    "/api/catalogue/categories",
    "/api/store",
    "/api/store/categories",
    "/api/store/products",
    "/api/search?q=milk",
    "/api/search?q=milk&limit=5",
    # ZopSmart specific patterns
    "/api/v1/products",
    "/api/v1/categories",
    "/api/v1/search?q=milk",
    "/api/v1/products?categoryId=247&limit=5",
    "/api/v1/catalogue/products?limit=5",
    "/api/v2/products",
    "/api/v2/categories",
    # Direct paths
    "/products",
    "/products?limit=5",
]

# Add any discovered patterns
for p in api_patterns:
    if p.startswith('/'):
        endpoints_to_try.append(p)

seen = set()
for path in endpoints_to_try:
    if path in seen:
        continue
    seen.add(path)
    try:
        r = client.get(f"{BASE}{path}", headers=headers_json, timeout=10)
        has_data = r.status_code == 200 and len(r.content) > 50
        if r.status_code not in (404, 301, 302) or has_data:
            print(f"  [{r.status_code}] {path} size={len(r.content)} {'DATA!' if has_data else ''}")
            if has_data:
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
                                        print(f"       First keys: {list(val[0].keys())[:15]}")
                                        sample = json.dumps(val[0], ensure_ascii=False)[:500]
                                        print(f"       Sample: {sample}")
                                elif isinstance(val, (int, float)):
                                    print(f"       .{k} = {val}")
                                elif isinstance(val, dict):
                                    print(f"       .{k} keys = {list(val.keys())[:10]}")
                    elif isinstance(data, list):
                        print(f"       List[{len(data)}]")
                except:
                    print(f"       Raw: {r.content[:200]}")
    except:
        pass

# ============================================================
# STEP 4: Try /api/store endpoint and explore response
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: Explore /api/store response")
print("=" * 60)

r = client.get(f"{BASE}/api/store", headers=headers_json, timeout=10)
if r.status_code == 200:
    data = r.json()
    store_data = data.get("data", {}).get("store", {})
    if isinstance(store_data, dict):
        print(f"  Store keys: {list(store_data.keys())[:20]}")
        for k in ["id", "name", "storeId", "apiUrl", "baseUrl"]:
            if k in store_data:
                print(f"  .{k} = {store_data[k]}")

    # Save for reference
    with open("data/tamimi_store.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("  Saved to data/tamimi_store.json")

# ============================================================
# STEP 5: Try Smash API (Tamimi uses Smash platform per retailer settings)
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: Try Smash/ZopSmart product API patterns")
print("=" * 60)

# From retailer settings: tamimi uses "smash" platform
# Try with store-specific headers
smash_headers = {
    "Accept": "application/json",
    "User-Agent": "okhttp/5.0.0-alpha.6",
    "Accept-Language": "ar",
    "medium": "APP",
    "appversion": "5.1.0",
    "storeId": "2",  # Try common store IDs
}

smash_paths = [
    "/api/products?storeId=2&limit=5",
    "/api/products?store=2&limit=5",
    "/api/catalogue/products?storeId=2&limit=5",
    "/api/v1/products?storeId=2&limit=5",
    "/api/products?categoryId=247&storeId=2&limit=5",
    "/api/categories?storeId=2",
    "/api/store/2/products",
    "/api/store/2/categories",
]

for path in smash_paths:
    try:
        r = client.get(f"{BASE}{path}", headers=smash_headers, timeout=10)
        has_data = r.status_code == 200 and len(r.content) > 50
        if r.status_code not in (404,):
            print(f"  [{r.status_code}] {path} size={len(r.content)} {'DATA!' if has_data else ''}")
            if has_data:
                try:
                    data = r.json()
                    print(f"       {json.dumps(data, ensure_ascii=False)[:500]}")
                except:
                    pass
    except:
        pass

client.close()
print("\n=== DONE ===")
