#!/usr/bin/env python3
"""Tamimi: Use session cookies to access product API"""
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

# Use a session that maintains cookies
client = httpx.Client(timeout=30.0, follow_redirects=True)

# Step 1: Hit the home page first to get cookies
print("=" * 60)
print("STEP 1: Get session cookies from home page")
print("=" * 60)
r = client.get(f"{BASE}/", headers={
    "Accept": "text/html",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "ar,en;q=0.9",
}, timeout=15)
print(f"  Status: {r.status_code}, Cookies: {dict(client.cookies)}")

# Step 2: Now try API with session
print("\n" + "=" * 60)
print("STEP 2: Try product API with session cookies")
print("=" * 60)

api_headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "ar,en;q=0.9",
    "Referer": f"{BASE}/category/pets",
    "X-Requested-With": "XMLHttpRequest",
}

# Try various product listing endpoints
test_paths = [
    "/api/products?categorySlug=pets&limit=5",
    "/api/products?slug=pets&limit=5",
    "/api/products?category=pets&limit=5",
    "/api/catalogue/products?categorySlug=pets&limit=5",
    "/api/catalogue/products?slug=pets&limit=5",
    "/api/catalogue/products?category=pets&limit=5",
    "/api/categories/pets/products?limit=5",
    "/api/category/pets/products?limit=5",
    "/api/categories/247/products?limit=5",
    "/api/category/247/products?limit=5",
    "/api/products?categoryId=247&limit=5",
    "/api/search/products?category=pets&limit=5",
    "/api/products?filters[category]=pets&limit=5",
    "/api/products?filter=category:pets&limit=5",
]

for path in test_paths:
    try:
        r = client.get(f"{BASE}{path}", headers=api_headers, timeout=10)
        has = r.status_code == 200 and len(r.content) > 50
        if r.status_code not in (404,):
            print(f"  [{r.status_code}] {path} size={len(r.content)} {'DATA!' if has else ''}")
            if has:
                d = r.json()
                print(f"       {json.dumps(d, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"  [ERR] {path} -> {type(e).__name__}")

# Step 3: Check the home page _next/data for product data
print("\n" + "=" * 60)
print("STEP 3: Extract products from home page _next/data (480KB!)")
print("=" * 60)

build_id = "KKet2UOH4fkWP9Kag2Bbl"
r = client.get(f"{BASE}/_next/data/{build_id}/index.json", headers=api_headers, timeout=20)
if r.status_code == 200:
    data = r.json()
    pp = data.get("pageProps", {})
    print(f"  pageProps keys: {list(pp.keys())[:20]}")

    # Search for products in all nested structures
    def find_products(obj, path=""):
        if isinstance(obj, dict):
            if "products" in obj:
                prods = obj["products"]
                if isinstance(prods, list) and prods:
                    print(f"  FOUND products at {path}.products - {len(prods)} items")
                    if isinstance(prods[0], dict):
                        print(f"    Keys: {list(prods[0].keys())[:15]}")
                        print(f"    Sample: {json.dumps(prods[0], ensure_ascii=False)[:500]}")
                    return prods
            if "items" in obj:
                items = obj["items"]
                if isinstance(items, list) and items and isinstance(items[0], dict):
                    if any(k in items[0] for k in ["price", "name", "sku", "brand"]):
                        print(f"  FOUND items at {path}.items - {len(items)} items")
                        print(f"    Keys: {list(items[0].keys())[:15]}")
                        return items
            if "collection" in obj:
                coll = obj["collection"]
                if isinstance(coll, dict) and "products" in coll:
                    prods = coll["products"]
                    if isinstance(prods, list) and prods:
                        print(f"  FOUND products at {path}.collection.products - {len(prods)} items")
                        if isinstance(prods[0], dict):
                            print(f"    Keys: {list(prods[0].keys())[:15]}")
                            print(f"    Sample: {json.dumps(prods[0], ensure_ascii=False)[:500]}")
                        return prods

            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    result = find_products(v, f"{path}.{k}")
                    if result:
                        return result
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    result = find_products(item, f"{path}[{i}]")
                    if result:
                        return result
        return None

    products = find_products(pp)
    if not products:
        # Save for debugging
        with open("data/tamimi_home_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("  No products found in home data, saved for inspection")

# Step 4: Check the categories _next/data
print("\n" + "=" * 60)
print("STEP 4: Extract from categories _next/data")
print("=" * 60)

r = client.get(f"{BASE}/_next/data/{build_id}/categories.json", headers=api_headers, timeout=20)
if r.status_code == 200:
    data = r.json()
    pp = data.get("pageProps", {})
    print(f"  pageProps keys: {list(pp.keys())[:20]}")
    products = find_products(pp)

# Step 5: Try the category page and look for XHR API in network
print("\n" + "=" * 60)
print("STEP 5: Search JS for fetch/XHR patterns")
print("=" * 60)

# Get the main JS chunks
r = client.get(f"{BASE}/", headers={
    "Accept": "text/html",
    "User-Agent": "Mozilla/5.0",
}, timeout=15)

# Find the main app chunk
js_files = re.findall(r'/_next/static/chunks/pages/_app-[^"\']+\.js', r.text)
js_files += re.findall(r'/_next/static/chunks/[a-f0-9]+-[^"\']+\.js', r.text)
js_files += re.findall(r'/_next/static/chunks/framework-[^"\']+\.js', r.text)
js_files += re.findall(r'/_next/static/chunks/main-[^"\']+\.js', r.text)
js_files += re.findall(r'/_next/static/chunks/pages/category/\[\.\.\.slug\]-[^"\']+\.js', r.text)

# Also look for the category page chunk specifically
all_chunks = re.findall(r'/_next/static/[^"\']+\.js', r.text)
print(f"  Found {len(all_chunks)} JS chunks total")
print(f"  App/category chunks: {len(js_files)}")

# Look specifically in app and category chunks for API patterns
for js_url in js_files[:5]:
    try:
        r = client.get(f"{BASE}{js_url}", timeout=10)
        if r.status_code == 200:
            js = r.text
            # Look for fetch patterns with product/catalogue in the URL
            patterns = re.findall(r'["\'](/api/[^"\']*(?:product|catalogue|catalog|search|category)[^"\']*)["\']', js, re.IGNORECASE)
            patterns += re.findall(r'["\'](https?://[^"\']*(?:product|catalogue|catalog|search)[^"\']*)["\']', js, re.IGNORECASE)
            patterns += re.findall(r'concat\(["\']([^"\']+)["\'].*?(?:product|categ)', js, re.IGNORECASE)

            # Also look for getProducts or fetchProducts function patterns
            prod_funcs = re.findall(r'(?:get|fetch|load)(?:Products?|Catalogue|Catalog|Items)\s*[=(]', js)

            if patterns or prod_funcs:
                short_name = js_url.split('/')[-1][:40]
                print(f"\n  In {short_name}:")
                for p in patterns[:10]:
                    print(f"    API: {p}")
                for p in prod_funcs[:5]:
                    print(f"    Func: {p}")
    except:
        pass

# Search ALL chunks for the specific API call pattern
print("\n  Searching all chunks for product fetch patterns...")
found_apis = set()
for js_url in all_chunks:
    try:
        r = client.get(f"{BASE}{js_url}", timeout=5)
        if r.status_code == 200:
            js = r.text
            # Look for the specific pattern: /api + products or categories
            matches = re.findall(r'["\'](/api/[a-zA-Z0-9/_-]*)["\']', js)
            for m in matches:
                if m not in ('/api', '/api/'):
                    found_apis.add(m)
    except:
        pass

print(f"\n  All /api/* patterns found in JS:")
for a in sorted(found_apis):
    print(f"    {a}")

# Try all discovered APIs
print("\n  Testing discovered API paths...")
for api_path in sorted(found_apis):
    try:
        r = client.get(f"{BASE}{api_path}", headers=api_headers, timeout=5)
        has = r.status_code == 200 and len(r.content) > 50
        if r.status_code not in (404, 301, 302):
            print(f"    [{r.status_code}] {api_path} size={len(r.content)} {'DATA!' if has else ''}")
            if has:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"         Keys: {list(d.keys())[:10]}")
                except:
                    pass
    except:
        pass

client.close()
print("\n=== DONE ===")
