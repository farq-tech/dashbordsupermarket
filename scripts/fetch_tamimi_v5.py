#!/usr/bin/env python3
"""Tamimi: Extract full product data from category page layouts"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import os
import csv
import re
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
# STEP 1: Fetch a category page and dump FULL layout data
# ============================================================
print("=" * 60)
print("STEP 1: Get full ProductCollection data from category page")
print("=" * 60)

# Try a small category first
r = client.get(f"{BASE}/category/camel", headers=html_headers, timeout=15)
print(f"  Status: {r.status_code}, Size: {len(r.content)}")

if r.status_code == 200 and "__NEXT_DATA__" in r.text:
    html = r.text
    nd_start = html.index('__NEXT_DATA__')
    sc_start = html.rfind('<script', 0, nd_start)
    sc_end = html.find('</script>', nd_start)
    j_start = html.index('>', sc_start) + 1
    nd = json.loads(html[j_start:sc_end].strip())
    pp = nd.get("props", {}).get("pageProps", {})

    layouts_resp = pp.get("layouts", {})
    if isinstance(layouts_resp, dict):
        page_data = layouts_resp.get("data", {}).get("page", {})
        entity = page_data.get("entity", {})
        print(f"  Category: {entity.get('name')} (id={entity.get('id')}, slug={entity.get('slug')})")

        page_layouts = page_data.get("layouts", [])
        print(f"  Layouts count: {len(page_layouts)}")

        for i, layout in enumerate(page_layouts):
            name = layout.get("name", "")
            print(f"\n  Layout {i}: {name}")

            if name == "ProductCollection":
                value = layout.get("value", {})
                collection = value.get("collection", {})
                print(f"    collection keys: {list(collection.keys())}")
                count = collection.get("count", 0)
                print(f"    count: {count}")

                # Check if products are here
                products = collection.get("products", [])
                items = collection.get("items", [])
                print(f"    products: {len(products) if isinstance(products, list) else type(products)}")
                print(f"    items: {len(items) if isinstance(items, list) else type(items)}")

                if products and isinstance(products, list) and isinstance(products[0], dict):
                    print(f"    Product keys: {list(products[0].keys())}")
                    print(f"    First product: {json.dumps(products[0], ensure_ascii=False)[:1000]}")
                elif items and isinstance(items, list) and isinstance(items[0], dict):
                    print(f"    Item keys: {list(items[0].keys())}")
                    print(f"    First item: {json.dumps(items[0], ensure_ascii=False)[:1000]}")

                # Full collection dump
                with open("data/tamimi_collection_debug.json", "w", encoding="utf-8") as f:
                    json.dump(collection, f, ensure_ascii=False, indent=2)
                print(f"    Saved collection to data/tamimi_collection_debug.json")

                # Check filters
                filters = collection.get("filters", {})
                if filters:
                    print(f"    Filters keys: {list(filters.keys())}")

# ============================================================
# STEP 2: Larger category page
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Try a larger category")
print("=" * 60)

r = client.get(f"{BASE}/category/rice-1", headers=html_headers, timeout=15)
print(f"  Rice category: Status={r.status_code}, Size={len(r.content)}")

if r.status_code == 200 and "__NEXT_DATA__" in r.text:
    html = r.text
    nd_start = html.index('__NEXT_DATA__')
    sc_start = html.rfind('<script', 0, nd_start)
    sc_end = html.find('</script>', nd_start)
    j_start = html.index('>', sc_start) + 1
    nd = json.loads(html[j_start:sc_end].strip())
    pp = nd.get("props", {}).get("pageProps", {})
    layouts_resp = pp.get("layouts", {})

    if isinstance(layouts_resp, dict):
        page_data = layouts_resp.get("data", {}).get("page", {})
        page_layouts = page_data.get("layouts", [])

        for layout in page_layouts:
            if layout.get("name") == "ProductCollection":
                collection = layout.get("value", {}).get("collection", {})
                products = collection.get("products", [])
                print(f"  Products found: {len(products)}")
                if products and isinstance(products[0], dict):
                    print(f"  Product keys: {list(products[0].keys())}")
                    print(f"  First: {json.dumps(products[0], ensure_ascii=False)[:1500]}")

# ============================================================
# STEP 3: Try search page (might list all products)
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Try search page")
print("=" * 60)

search_urls = [
    f"{BASE}/search?q=rice",
    f"{BASE}/search?q=milk",
    f"{BASE}/search/rice",
]

for url in search_urls:
    try:
        r = client.get(url, headers=html_headers, timeout=15)
        print(f"\n  [{r.status_code}] {url.replace(BASE, '')} size={len(r.content)}")

        if r.status_code == 200 and "__NEXT_DATA__" in r.text:
            html = r.text
            nd_start = html.index('__NEXT_DATA__')
            sc_start = html.rfind('<script', 0, nd_start)
            sc_end = html.find('</script>', nd_start)
            j_start = html.index('>', sc_start) + 1
            nd = json.loads(html[j_start:sc_end].strip())
            pp = nd.get("props", {}).get("pageProps", {})
            print(f"    pageProps keys: {list(pp.keys())}")

            # Look for products in all structures
            def find_prods(obj, depth=0, path=""):
                if depth > 5: return
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k in ("products", "items", "results") and isinstance(v, list) and v:
                            if isinstance(v[0], dict) and any(pk in v[0] for pk in ["price", "name", "sku", "id"]):
                                print(f"    FOUND {k} at {path}.{k}: {len(v)} items")
                                print(f"      Keys: {list(v[0].keys())[:15]}")
                                print(f"      Sample: {json.dumps(v[0], ensure_ascii=False)[:800]}")
                                return v
                        if isinstance(v, (dict, list)):
                            r = find_prods(v, depth+1, f"{path}.{k}")
                            if r: return r
                    if "collection" in obj:
                        coll = obj["collection"]
                        if isinstance(coll, dict):
                            print(f"    Collection at {path}: count={coll.get('count')}, keys={list(coll.keys())[:10]}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj[:5]):
                        r = find_prods(item, depth+1, f"{path}[{i}]")
                        if r: return r

            find_prods(pp)
    except Exception as e:
        print(f"  [ERR] -> {type(e).__name__}: {e}")

client.close()
print("\n=== DONE ===")
