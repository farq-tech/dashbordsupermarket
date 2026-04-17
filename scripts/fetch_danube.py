#!/usr/bin/env python3
"""Fetch ALL 30,000+ products from Danube via /api/products"""

import requests
import json
import csv
import time
import sys
import os
from datetime import datetime

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

BASE = "https://www.danube.sa"
HEADERS = {
    "Host": "www.danube.sa",
    "x-view-version": "2",
    "Accept": "application/json",
    "x-spree-platform": "ios",
    "x-spree-deliverymethod": "home_delivery",
    "Accept-Language": "ar",
    "x-spree-districtid": "98",
    "User-Agent": "danube/39212 CFNetwork/3860.300.31 Darwin/25.2.0",
    "x-device-id": "30B18F93-A1CA-4227-92F2-3E3B5C88C825",
    "x-spree-checkouttype": "regular",
    "x-spree-supermarketid": "376",
    "Content-Type": "application/json",
}

session = requests.Session()
session.headers.update(HEADERS)

PER_PAGE = 100  # Max per page

print("=" * 60)
print("DANUBE Product Scraper - 30,000+ products")
print("=" * 60)

# Step 1: Get categories
print("\n[1] Fetching departments...")
r = session.get(f"{BASE}/en/api/v3/departments", timeout=15)
depts = r.json().get("data", [])
print(f"  {len(depts)} departments found")

# Save departments
cat_path = "f:/fustog/data/danube_categories.json"
with open(cat_path, "w", encoding="utf-8") as f:
    json.dump(depts, f, ensure_ascii=False, indent=2)

# Step 2: Fetch ALL products with pagination
print(f"\n[2] Fetching ALL products (per_page={PER_PAGE})...")

all_products = []
seen_ids = set()
page = 1
total_pages = None
total_count = None
retries = 0
max_retries = 3

while True:
    try:
        r = session.get(
            f"{BASE}/api/products",
            params={"page": page, "per_page": PER_PAGE},
            timeout=30
        )

        if r.status_code != 200:
            print(f"  Page {page}: HTTP {r.status_code}")
            retries += 1
            if retries >= max_retries:
                print(f"  Giving up after {max_retries} retries")
                break
            time.sleep(2)
            continue

        data = r.json()
        retries = 0

        if total_pages is None:
            total_pages = data.get("pages", 1)
            total_count = data.get("total_count", 0)
            print(f"  Total: {total_count} products, {total_pages} pages")

        products = data.get("products", [])
        new_count = 0
        for p in products:
            pid = p.get("id")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                all_products.append(p)
                new_count += 1

        print(f"  Page {page}/{total_pages}: {len(products)} items, {new_count} new (total: {len(all_products)})")

        if page >= total_pages or not products:
            break

        page += 1

        # Polite delay
        if page % 10 == 0:
            time.sleep(1)
        else:
            time.sleep(0.3)

    except Exception as e:
        print(f"  Page {page} ERROR: {e}")
        retries += 1
        if retries >= max_retries:
            break
        time.sleep(3)

print(f"\n  TOTAL unique products: {len(all_products)}")

# Step 3: Save JSON
print("\n[3] Saving data...")
json_path = "f:/fustog/data/danube_products.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({
        "metadata": {
            "fetched_at": datetime.now().isoformat(),
            "total": len(all_products),
            "departments": len(depts),
            "store": "Danube",
            "source": "www.danube.sa"
        },
        "products": all_products
    }, f, ensure_ascii=False)
print(f"  JSON: {json_path} ({os.path.getsize(json_path) / 1024 / 1024:.1f} MB)")

# Step 4: Save CSV
csv_path = "f:/fustog/data/danube_products.csv"
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "product_id", "name_ar", "full_name_ar", "name_en", "full_name_en",
        "brand_ar", "brand_en", "price", "original_price", "on_sale",
        "display_price", "currency", "slug", "in_stock", "weight",
        "pack_size", "pack_unit", "category_facets", "category_facets_en",
        "image_url", "description", "store"
    ])

    for p in all_products:
        # Get image from master variant
        master = p.get("master", {})
        images = master.get("images", []) if master else []
        img = ""
        if images:
            img = images[0].get("product_url", "") or images[0].get("large_url", "")

        # Get category from algolia facets
        facets = p.get("algolia_taxon_facets", [])
        facets_en = p.get("algolia_taxon_facets_en", [])

        w.writerow([
            p.get("id", ""),
            p.get("name", ""),
            p.get("full_name", ""),
            p.get("name_en", ""),
            p.get("full_name_en", ""),
            p.get("brand", ""),
            p.get("brand_en", ""),
            p.get("price", ""),
            p.get("original_price", ""),
            p.get("on_sale", False),
            p.get("display_price", ""),
            "SAR",
            p.get("slug", ""),
            p.get("in_stock", True),
            p.get("weight", ""),
            p.get("pack_size", ""),
            p.get("pack_unit", ""),
            " | ".join(facets) if isinstance(facets, list) else str(facets),
            " | ".join(facets_en) if isinstance(facets_en, list) else str(facets_en),
            img,
            (p.get("description", "") or "")[:200],
            "Danube"
        ])

print(f"  CSV: {csv_path} ({os.path.getsize(csv_path) / 1024 / 1024:.1f} MB)")

print(f"\n{'='*60}")
print(f"DONE! {len(all_products)} Danube products saved")
print(f"{'='*60}")
