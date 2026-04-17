#!/usr/bin/env python3
"""Fetch Carrefour products using discovered API endpoints"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time, re
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
BASE = "https://www.carrefourksa.com"

client = httpx.Client(timeout=25.0, follow_redirects=True)

# Browser-like headers
h = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.8",
    "Referer": "https://www.carrefourksa.com/mafsau/ar/",
    "Origin": "https://www.carrefourksa.com",
}

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# STEP 1: Test discovered API endpoints
# ============================================================
print("=" * 60)
print("STEP 1: Test Carrefour API endpoints")
print("=" * 60)

# From JS analysis: /api/v8/search, /api/v1/menu, /v1/auto-suggest
endpoints = [
    # Menu / Categories
    (f"{BASE}/api/v1/menu", {}),
    (f"{BASE}/api/v1/menu?storeId=mafsau&lang=ar", {}),
    # Search - this is the key one!
    (f"{BASE}/api/v8/search?keyword=rice&lang=ar&storeId=mafsau&pageSize=5", {}),
    (f"{BASE}/api/v8/search?keyword=milk&lang=ar&storeId=mafsau&pageSize=5", {}),
    (f"{BASE}/api/v8/search?keyword=&lang=ar&storeId=mafsau&pageSize=5", {}),
    (f"{BASE}/api/v8/search?q=rice&lang=ar&storeId=mafsau&pageSize=5", {}),
    # Auto-suggest
    (f"{BASE}/v1/auto-suggest?keyword=rice&lang=ar&storeId=mafsau", {}),
    (f"{BASE}/v1/auto-suggest?q=rice&lang=ar&storeId=mafsau", {}),
    # Relevance
    (f"{BASE}/api/v5/relevance?storeId=mafsau&lang=ar", {}),
    # Features
    (f"{BASE}/api/features/?storeId=mafsau", {}),
]

working = []
for url, params in endpoints:
    try:
        r = client.get(url, headers=h, params=params, timeout=10)
        has = r.status_code == 200 and len(r.content) > 100
        print(f"  [{r.status_code}] {url.replace(BASE,'')} size={len(r.content)} {'DATA!' if has else ''}")
        if has:
            try:
                d = r.json()
                if isinstance(d, dict):
                    print(f"    Keys: {list(d.keys())[:15]}")
                    for k in ["products", "items", "results", "data", "hits", "categories", "menu", "suggestions"]:
                        if k in d:
                            val = d[k]
                            if isinstance(val, list):
                                print(f"    .{k} = List[{len(val)}]")
                                if val and isinstance(val[0], dict):
                                    print(f"    First keys: {list(val[0].keys())[:15]}")
                                    print(f"    Sample: {json.dumps(val[0], ensure_ascii=False)[:500]}")
                            elif isinstance(val, dict):
                                print(f"    .{k} keys = {list(val.keys())[:10]}")
                            else:
                                print(f"    .{k} = {val}")
                    working.append(url)
                save(f"carrefour_test_{url.split('/')[-1].split('?')[0]}.json", d)
            except:
                print(f"    Raw: {r.content[:300]}")
    except Exception as e:
        print(f"  [ERR] {url.replace(BASE,'')} -> {type(e).__name__}")

# ============================================================
# STEP 2: Try search with category browsing
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Try category-based product listing")
print("=" * 60)

# Carrefour MAF uses catalog/category browsing
cat_endpoints = [
    f"{BASE}/api/v8/search?lang=ar&storeId=mafsau&currentPage=0&pageSize=20&sortBy=relevance",
    f"{BASE}/api/v8/search?lang=ar&storeId=mafsau&currentPage=0&pageSize=20&category=food",
    f"{BASE}/api/v8/search?lang=ar&storeId=mafsau&currentPage=0&pageSize=20&filter=",
    f"{BASE}/api/v8/search?keyword=*&lang=ar&storeId=mafsau&pageSize=20",
    f"{BASE}/api/v8/search?keyword=&lang=ar&storeId=mafsau&pageSize=20&currentPage=0",
    # POST search
]

for url in cat_endpoints:
    try:
        r = client.get(url, headers=h, timeout=10)
        has = r.status_code == 200 and len(r.content) > 100
        print(f"  [{r.status_code}] ...{url.split('search')[1][:60]} size={len(r.content)} {'DATA!' if has else ''}")
        if has:
            try:
                d = r.json()
                if isinstance(d, dict):
                    print(f"    Keys: {list(d.keys())[:10]}")
                    for k in d:
                        if isinstance(d[k], list) and d[k]:
                            print(f"    .{k} = List[{len(d[k])}]")
                        elif isinstance(d[k], (int, float)):
                            print(f"    .{k} = {d[k]}")
                    save(f"carrefour_search_{len(working)}.json", d)
                    working.append(url)
            except:
                pass
    except:
        pass

# Also try POST for search
print("\n  --- POST search ---")
post_bodies = [
    {"keyword": "rice", "lang": "ar", "storeId": "mafsau", "pageSize": 5},
    {"keyword": "", "lang": "ar", "storeId": "mafsau", "pageSize": 20},
    {"query": "rice", "lang": "ar"},
]
for body in post_bodies:
    try:
        r = client.post(f"{BASE}/api/v8/search", json=body, headers=h, timeout=10)
        has = r.status_code == 200 and len(r.content) > 100
        print(f"  [{r.status_code}] POST search body={list(body.keys())} size={len(r.content)} {'DATA!' if has else ''}")
        if has:
            d = r.json()
            print(f"    {json.dumps(d, ensure_ascii=False)[:500]}")
    except:
        pass

# ============================================================
# STEP 3: Try the actual website category pages for data
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Scrape category pages")
print("=" * 60)

# Carrefour category URLs pattern
cat_urls = [
    f"{BASE}/mafsau/ar/v4/search?keyword=rice&pageSize=20",
    f"{BASE}/mafsau/ar/supermarket/grocery/c/F1100000",
    f"{BASE}/mafsau/ar/c/F1100000",
    f"{BASE}/mafsau/ar/fresh-food/NFSA1100000",
    f"{BASE}/mafsau/ar/grocery/NFSA1100000",
]
for url in cat_urls:
    try:
        r = client.get(url, headers={
            "Accept": "text/html",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14)",
        }, timeout=10)
        has_data = r.status_code == 200 and len(r.content) > 1000
        print(f"  [{r.status_code}] ...{url.split('.com')[1][:50]} size={len(r.content)}")
        if has_data:
            # Check for product JSON
            prod_matches = re.findall(r'"price":\s*[\d.]+', r.text)
            if prod_matches:
                print(f"    Found {len(prod_matches)} price fields!")
            # Check for JSON-LD product data
            json_ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', r.text, re.DOTALL)
            for jl in json_ld:
                try:
                    d = json.loads(jl)
                    if isinstance(d, dict) and d.get("@type") in ("Product", "ItemList", "ProductGroup"):
                        print(f"    JSON-LD Product found!")
                        print(f"    {json.dumps(d, ensure_ascii=False)[:300]}")
                except:
                    pass
    except:
        pass

if not working:
    print("\n  No working Carrefour endpoints found.")
    print("  Carrefour uses a fully client-side SPA with no server-rendered product data.")
    print("  Would need a headless browser (Playwright/Selenium) to extract products.")

client.close()
print("\n=== DONE ===")
