#!/usr/bin/env python3
"""Carrefour: Get OAuth token with JSON body, then fetch products"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, re, time, csv
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
BASE = "https://www.carrefourksa.com"
client = httpx.Client(timeout=25.0, follow_redirects=True)

app_h = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Carrefour/3 CFNetwork/1410.0.3 Darwin/22.6.0",
    "accept-language": "ar",
    "storeid": "mafsau",
    "langcode": "ar",
    "appid": "IOS",
    "env": "PROD",
    "mafcountry": "SA",
}

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Step 1: Get OAuth token with JSON body
print("=" * 60)
print("STEP 1: Get OAuth token")
print("=" * 60)

token = None
for grant in ["client_credentials", "anonymous", "guest", "password"]:
    try:
        r = client.post(f"{BASE}/v2/oauth/token",
            json={"grantType": grant},
            headers=app_h, timeout=10)
        print(f"  [{r.status_code}] grantType={grant}: {r.text[:300]}")
        if r.status_code == 200:
            d = r.json()
            token = d.get("accessToken", d.get("access_token", d.get("token", "")))
            if not token and isinstance(d.get("data"), dict):
                token = d["data"].get("accessToken", d["data"].get("token", ""))
            if token:
                print(f"  TOKEN: {token[:60]}...")
                save("carrefour_token.json", d)
                break
    except Exception as e:
        print(f"  [ERR] -> {type(e).__name__}: {e}")

if not token:
    # Try with different body formats
    print("\n  Trying alternative body formats...")
    bodies = [
        {"grantType": "client_credentials", "clientId": "IOS", "storeId": "mafsau"},
        {"grantType": "anonymous", "storeId": "mafsau", "langCode": "ar"},
        {"grantType": "client_credentials", "appId": "IOS"},
    ]
    for body in bodies:
        try:
            r = client.post(f"{BASE}/v2/oauth/token", json=body, headers=app_h, timeout=10)
            print(f"  [{r.status_code}] body={list(body.keys())}: {r.text[:300]}")
            if r.status_code == 200:
                d = r.json()
                token = d.get("accessToken", d.get("token", ""))
                if not token and isinstance(d.get("data"), dict):
                    token = d["data"].get("accessToken", "")
                if token:
                    print(f"  TOKEN: {token[:60]}...")
                    save("carrefour_token.json", d)
                    break
        except:
            pass

# Step 2: Use token to fetch data
if token:
    print("\n" + "=" * 60)
    print("STEP 2: Fetch products with token")
    print("=" * 60)

    auth_h = {**app_h, "Authorization": f"Bearer {token}"}

    endpoints = [
        "/api/v1/menu",
        "/api/v8/search?keyword=rice&storeId=mafsau&lang=ar&pageSize=20",
        "/api/v8/search?keyword=&storeId=mafsau&lang=ar&pageSize=50",
        "/v1/auto-suggest?keyword=rice&storeId=mafsau&lang=ar",
    ]

    all_products = []
    categories = []

    for ep in endpoints:
        try:
            r = client.get(f"{BASE}{ep}", headers=auth_h, timeout=15)
            print(f"\n  [{r.status_code}] {ep[:60]} size={len(r.content)}")
            if r.status_code == 200 and len(r.content) > 100:
                d = r.json()
                if isinstance(d, dict):
                    print(f"    Keys: {list(d.keys())[:15]}")
                    for k in ["products", "items", "results", "data", "hits", "menu", "categories", "suggestions", "totalCount", "numHits"]:
                        if k in d:
                            val = d[k]
                            if isinstance(val, list):
                                print(f"    .{k} = List[{len(val)}]")
                                if val and isinstance(val[0], dict):
                                    print(f"    First keys: {list(val[0].keys())[:15]}")
                                    print(f"    Sample: {json.dumps(val[0], ensure_ascii=False)[:500]}")
                            elif isinstance(val, (int, float)):
                                print(f"    .{k} = {val}")
                            elif isinstance(val, dict):
                                print(f"    .{k} keys = {list(val.keys())[:10]}")
                save(f"carrefour_result_{ep.split('?')[0].split('/')[-1]}.json", d)
        except Exception as e:
            print(f"  [ERR] -> {type(e).__name__}")

    # Step 3: If search works, paginate through all products
    print("\n" + "=" * 60)
    print("STEP 3: Paginate search results")
    print("=" * 60)

    # Try searching with empty keyword to get all products
    page = 0
    total = 0
    while page < 500:  # Safety limit
        try:
            url = f"{BASE}/api/v8/search?keyword=&storeId=mafsau&lang=ar&pageSize=60&currentPage={page}"
            r = client.get(url, headers=auth_h, timeout=15)
            if r.status_code != 200:
                print(f"  Page {page}: HTTP {r.status_code}")
                break

            d = r.json()
            products = d.get("products", d.get("items", d.get("hits", d.get("data", []))))
            if isinstance(products, dict):
                products = products.get("products", products.get("items", []))

            if not products:
                print(f"  Page {page}: No products, done!")
                break

            total_count = d.get("totalCount", d.get("numHits", d.get("total", 0)))
            all_products.extend(products)

            if page == 0 or page % 10 == 0:
                print(f"  Page {page}: +{len(products)} (total: {len(all_products)}/{total_count})")

            if len(all_products) >= total_count or len(products) < 60:
                print(f"  Done! {len(all_products)} products")
                break

            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"  Page {page}: ERR {e}")
            break

    if all_products:
        print(f"\n  TOTAL: {len(all_products)} products")

        # Normalize and save
        normalized = []
        for p in all_products:
            row = {
                "product_id": p.get("id", p.get("productId", "")),
                "sku": p.get("sku", p.get("code", "")),
                "name_ar": p.get("name", p.get("title", "")),
                "name_en": p.get("nameEn", p.get("englishName", "")),
                "category_id": p.get("categoryId", ""),
                "category_name": p.get("category", p.get("categoryName", "")),
                "parent_category": "",
                "brand_id": "",
                "brand_name": p.get("brand", p.get("brandName", "")),
                "description": p.get("description", ""),
                "image_url": p.get("image", p.get("imageUrl", p.get("thumbnail", ""))),
                "price": p.get("price", p.get("currentPrice", "")),
                "sale_price": p.get("salePrice", p.get("discountPrice", "")),
                "currency": "SAR",
                "size": p.get("size", p.get("weight", "")),
                "unit": p.get("unit", ""),
                "in_stock": 1 if p.get("inStock", p.get("available", True)) else 0,
                "variety_id": "",
                "barcode": p.get("barcode", p.get("ean", "")),
                "store": "carrefour",
                "store_name": "Carrefour",
                "city": "Riyadh",
                "source_endpoint": "carrefourksa.com/api/v8/search",
                "fetched_at": datetime.now().isoformat(),
                "varieties_count": 1,
            }
            normalized.append(row)

        fn = list(normalized[0].keys())
        with open("data/carrefour_products.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fn)
            w.writeheader()
            w.writerows(normalized)
        print(f"  CSV: data/carrefour_products.csv ({len(normalized)} rows)")

        save("carrefour_products.json", {"metadata": {"total": len(normalized), "store": "Carrefour"}, "products": normalized})
        save(f"carrefour_raw_{ts}.json", all_products)
        print(f"  JSON: data/carrefour_products.json")
else:
    print("\n  Could not get OAuth token. Carrefour requires mobile app auth flow.")

client.close()
print("\n=== DONE ===")
