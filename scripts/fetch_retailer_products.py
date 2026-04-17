#!/usr/bin/env python3
"""Fetch products from working retailer APIs (Panda, Farm)"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import os
import csv
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
client = httpx.Client(timeout=30.0, follow_redirects=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# ============ PANDA ============
print("=" * 60)
print("PANDA - Fetching categories and products")
print("=" * 60)

panda_headers = {
    "Accept": "application/json;charset=UTF-8",
    "User-Agent": "okhttp/5.0.0-alpha.6",
    "x-language": "ar",
    "x-pandaclick-agent": "4",
    "x-panda-source": "PandaClick",
}

# Get categories
print("[1/4] Fetching Panda categories...")
r = client.get("https://api.panda.sa/v3/categories", headers=panda_headers)
panda_cats = r.json()
print(f"  Status: {r.status_code}, Keys: {list(panda_cats.keys())}")

cat_data = panda_cats.get("data", panda_cats)
if isinstance(cat_data, list):
    print(f"  Categories: {len(cat_data)}")
elif isinstance(cat_data, dict):
    print(f"  Data keys: {list(cat_data.keys())[:10]}")

with open(f"data/panda_categories_{timestamp}.json", "w", encoding="utf-8") as f:
    json.dump(panda_cats, f, ensure_ascii=False, indent=2)
print(f"  Saved to data/panda_categories_{timestamp}.json")

# Get products
print("[2/4] Fetching Panda products...")
r = client.get("https://api.panda.sa/v3/products", headers=panda_headers)
panda_prods = r.json()
print(f"  Status: {r.status_code}, Size: {len(r.content)}")

prod_data = panda_prods.get("data", panda_prods)
if isinstance(prod_data, list):
    print(f"  Products: {len(prod_data)}")
    if prod_data:
        print(f"  First item keys: {list(prod_data[0].keys())}")
        print(f"  Sample: {json.dumps(prod_data[0], ensure_ascii=False)[:600]}")
elif isinstance(prod_data, dict):
    print(f"  Data keys: {list(prod_data.keys())[:20]}")
    # Check if paginated
    for k in ["items", "products", "results", "content", "data", "records"]:
        if k in prod_data:
            items = prod_data[k]
            if isinstance(items, list):
                print(f"  Found '{k}': {len(items)} items")
                if items:
                    print(f"  Sample: {json.dumps(items[0], ensure_ascii=False)[:600]}")
    # Check pagination
    for k in ["total", "totalCount", "totalItems", "count", "pages", "totalPages", "page", "per_page"]:
        if k in prod_data:
            print(f"  Pagination {k}: {prod_data[k]}")

with open(f"data/panda_products_{timestamp}.json", "w", encoding="utf-8") as f:
    json.dump(panda_prods, f, ensure_ascii=False, indent=2)
print(f"  Saved to data/panda_products_{timestamp}.json")

# Try paginated products
print("[3/4] Trying Panda paginated products...")
pages_data = []
for page in range(1, 6):  # Try first 5 pages
    try:
        r = client.get("https://api.panda.sa/v3/products",
            headers=panda_headers,
            params={"page": page, "limit": 50, "per_page": 50},
            timeout=15)
        if r.status_code == 200:
            data = r.json()
            items = data.get("data", data)
            if isinstance(items, dict):
                for k in ["items", "products", "results", "content", "data"]:
                    if k in items and isinstance(items[k], list):
                        items = items[k]
                        break
            if isinstance(items, list):
                print(f"  Page {page}: {len(items)} items")
                pages_data.extend(items)
                if len(items) == 0:
                    break
            else:
                print(f"  Page {page}: non-list response, keys={list(items.keys()) if isinstance(items, dict) else type(items)}")
                break
        else:
            print(f"  Page {page}: status {r.status_code}")
            break
    except Exception as e:
        print(f"  Page {page}: error {e}")
        break

if pages_data:
    print(f"  Total from pagination: {len(pages_data)}")
    with open(f"data/panda_products_paginated_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(pages_data, f, ensure_ascii=False, indent=2)

# Try category-specific products
print("[4/4] Trying Panda category products...")
# Extract category IDs from response
cat_ids = []
if isinstance(cat_data, list):
    for cat in cat_data[:3]:  # First 3 categories
        cid = cat.get("id") or cat.get("category_id") or cat.get("slug")
        if cid:
            cat_ids.append(cid)
elif isinstance(cat_data, dict):
    for k in ["categories", "items", "data"]:
        if k in cat_data and isinstance(cat_data[k], list):
            for cat in cat_data[k][:3]:
                cid = cat.get("id") or cat.get("category_id") or cat.get("slug")
                if cid:
                    cat_ids.append(cid)

print(f"  Category IDs to try: {cat_ids}")
for cid in cat_ids:
    try:
        urls = [
            f"https://api.panda.sa/v3/categories/{cid}/products",
            f"https://api.panda.sa/v3/products?category={cid}",
            f"https://api.panda.sa/v3/products?category_id={cid}",
        ]
        for url in urls:
            r = client.get(url, headers=panda_headers, timeout=10)
            if r.status_code == 200 and len(r.content) > 10:
                data = r.json()
                items = data.get("data", data)
                if isinstance(items, list) and len(items) > 0:
                    print(f"  {url} -> {len(items)} products!")
                    print(f"  Sample: {json.dumps(items[0], ensure_ascii=False)[:400]}")
                elif isinstance(items, dict):
                    for dk in ["items", "products", "results"]:
                        if dk in items and isinstance(items[dk], list) and len(items[dk]) > 0:
                            print(f"  {url} -> {len(items[dk])} products in '{dk}'!")
                            break
    except Exception as e:
        pass

# ============ FARM ============
print("\n" + "=" * 60)
print("FARM - Fetching categories and products")
print("=" * 60)

farm_headers = {
    "Accept": "application/json",
    "accept-language": "ar",
}

# Get categories
print("[1/2] Fetching Farm categories...")
r = client.get("https://go.farm.com.sa/public/api/v1.0/categories", headers=farm_headers)
farm_cats = r.json()
print(f"  Status: {r.status_code}, Keys: {list(farm_cats.keys())}")

farm_cat_data = farm_cats.get("details", farm_cats.get("data", farm_cats))
if isinstance(farm_cat_data, list):
    print(f"  Categories: {len(farm_cat_data)}")
    if farm_cat_data:
        print(f"  First keys: {list(farm_cat_data[0].keys())}")
        print(f"  Sample: {json.dumps(farm_cat_data[0], ensure_ascii=False)[:500]}")
elif isinstance(farm_cat_data, dict):
    print(f"  Keys: {list(farm_cat_data.keys())[:15]}")

with open(f"data/farm_categories_{timestamp}.json", "w", encoding="utf-8") as f:
    json.dump(farm_cats, f, ensure_ascii=False, indent=2)

# Get products
print("[2/2] Fetching Farm products...")
r = client.get("https://go.farm.com.sa/public/api/v1.0/products", headers=farm_headers)
farm_prods = r.json()
print(f"  Status: {r.status_code}, Size: {len(r.content)}")

farm_prod_data = farm_prods.get("details", farm_prods.get("data", farm_prods))
if isinstance(farm_prod_data, list):
    print(f"  Products: {len(farm_prod_data)}")
    if farm_prod_data:
        print(f"  First keys: {list(farm_prod_data[0].keys())}")
        print(f"  Sample: {json.dumps(farm_prod_data[0], ensure_ascii=False)[:500]}")
elif isinstance(farm_prod_data, dict):
    print(f"  Keys: {list(farm_prod_data.keys())[:20]}")
    for k in ["items", "products", "results", "content", "data", "records"]:
        if k in farm_prod_data and isinstance(farm_prod_data[k], list):
            print(f"  Found '{k}': {len(farm_prod_data[k])} items")

with open(f"data/farm_products_{timestamp}.json", "w", encoding="utf-8") as f:
    json.dump(farm_prods, f, ensure_ascii=False, indent=2)

client.close()
print("\n=== DONE ===")
