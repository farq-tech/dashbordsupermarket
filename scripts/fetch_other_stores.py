#!/usr/bin/env python3
"""Try to fetch products from remaining stores: Carrefour, Lulu, Farm, Ramez, Sadhan, Spar"""
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

# Load retailer settings
settings = {}
if os.path.exists("data/retailer_settings_full.json"):
    with open("data/retailer_settings_full.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
    print(f"Loaded {len(settings)} store configs from retailer_settings_full.json")

all_results = {}

# ============================================================
# 1. CARREFOUR (MAF/Retail SSO)
# ============================================================
print("\n" + "=" * 60)
print("1. CARREFOUR")
print("=" * 60)
carrefour_h = {
    "Accept": "application/json",
    "User-Agent": "Carrefour/3 CFNetwork/1410.0.3 Darwin/22.6.0",
    "accept-language": "ar",
    "storeid": "mafsau",
    "currency": "SAR",
    "langcode": "ar",
    "appid": "IOS",
    "env": "PROD",
}

# Carrefour KSA likely uses MAF API
carrefour_bases = [
    "https://www.carrefourksa.com",
    "https://api.carrefourksa.com",
    "https://api-prod.retailsso.com",
    "https://api.retailsso.com",
    # MAF e-commerce API patterns
    "https://www.carrefour.sa",
    "https://api.carrefour.sa",
]

carrefour_paths = [
    "/api/v7/categories?storeId=mafsau&lang=ar",
    "/api/v7/products?storeId=mafsau&lang=ar&limit=5",
    "/api/v5/categories?lang=ar",
    "/api/v5/products?lang=ar&limit=5",
    "/api/v2/products?lang=ar&limit=5",
    "/api/categories?lang=ar",
    "/api/products?lang=ar&limit=5",
    "/v1/categories?storeId=mafsau",
    "/v1/products?storeId=mafsau&limit=5",
    "/v2/customers/categories?storeId=mafsau",
    "/v2/customers/products?storeId=mafsau&limit=5",
]

for base in carrefour_bases:
    found_any = False
    for path in carrefour_paths:
        try:
            r = client.get(f"{base}{path}", headers=carrefour_h, timeout=8)
            has = r.status_code == 200 and len(r.content) > 50
            if r.status_code not in (404, 502, 503) and has:
                print(f"  [{r.status_code}] {base}{path} size={len(r.content)} DATA!")
                found_any = True
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"       Keys: {list(d.keys())[:10]}")
                except:
                    pass
        except Exception as e:
            if "ConnectError" not in str(type(e).__name__):
                print(f"  [ERR] {base}{path} -> {type(e).__name__}")
            break  # Skip this base if connection fails
    if found_any:
        break

# Try the MAF retail API directly
print("\n  --- MAF Retail API ---")
maf_h = {
    "Accept": "application/json",
    "User-Agent": "okhttp/4.12.0",
    "x-maf-application": "carrefour",
    "x-maf-country": "sa",
    "x-maf-language": "ar",
}
maf_bases = [
    "https://api.mafrservices.com",
    "https://api.mafretail.com",
]
for base in maf_bases:
    for path in [
        "/api/v1/categories",
        "/api/v1/products?limit=5",
        "/category/list",
        "/product/list",
    ]:
        try:
            r = client.get(f"{base}{path}", headers=maf_h, timeout=8)
            has = r.status_code == 200 and len(r.content) > 50
            if r.status_code not in (404, 502, 503):
                print(f"  [{r.status_code}] {base}{path} size={len(r.content)} {'DATA!' if has else ''}")
                if has:
                    try:
                        d = r.json()
                        print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
                    except:
                        pass
        except Exception as e:
            if "ConnectError" not in str(type(e).__name__):
                print(f"  [ERR] {base}{path} -> {type(e).__name__}")
            break

# ============================================================
# 2. LULU (Akinon platform)
# ============================================================
print("\n" + "=" * 60)
print("2. LULU HYPERMARKET")
print("=" * 60)
lulu_h = {
    "Accept": "*/*",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "accept-language": "ar;q=1.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
    "Content-Type": "application/json",
}
lulu_base = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"

# Akinon typically uses these API patterns
akinon_paths = [
    ("/ccm/api/v1/products/", "GET"),
    ("/ccm/api/v1/categories/", "GET"),
    ("/ccm/api/v1/products/?limit=5", "GET"),
    ("/api/v2/products/", "GET"),
    ("/api/v2/categories/", "GET"),
    ("/api/v2/products/?limit=5", "GET"),
    ("/api/v1/search/?q=rice", "GET"),
    ("/api/v1/search/?q=rice", "POST"),
    # Akinon Commerce patterns
    ("/api/v1/products/", "POST"),
    ("/api/v1/categories/", "POST"),
    ("/ccm/api/products/", "GET"),
    ("/ccm/api/categories/", "GET"),
]

for path, method in akinon_paths:
    try:
        if method == "GET":
            r = client.get(f"{lulu_base}{path}", headers=lulu_h, timeout=10)
        else:
            r = client.post(f"{lulu_base}{path}", json={}, headers=lulu_h, timeout=10)
        has = r.status_code == 200 and len(r.content) > 50
        if r.status_code not in (404,):
            print(f"  [{r.status_code}] {method} {path} size={len(r.content)} {'DATA!' if has else ''}")
            if has:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"       Keys: {list(d.keys())[:10]}")
                    print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
                except:
                    pass
    except Exception as e:
        print(f"  [ERR] {method} {path} -> {type(e).__name__}")

# Try luluhypermarket.com website
print("\n  --- luluhypermarket.com web ---")
lulu_web_h = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
    "Accept-Language": "ar",
}
for base in ["https://www.luluhypermarket.com/en-sa", "https://www.luluhypermarket.com/ar-sa"]:
    for path in ["/api/categories", "/api/products", "/api/search?q=rice"]:
        try:
            r = client.get(f"{base}{path}", headers=lulu_web_h, timeout=10)
            has = r.status_code == 200 and len(r.content) > 50
            if r.status_code not in (404,):
                print(f"  [{r.status_code}] {base.split('/')[-1]}{path} size={len(r.content)} {'DATA!' if has else ''}")
                if has:
                    try:
                        d = r.json()
                        print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
                    except:
                        pass
        except Exception as e:
            if "ConnectError" not in str(type(e).__name__):
                print(f"  [ERR] {base}{path} -> {type(e).__name__}")
            break

# ============================================================
# 3. FARM SUPERSTORES
# ============================================================
print("\n" + "=" * 60)
print("3. FARM SUPERSTORES")
print("=" * 60)
farm_h = {
    "Accept": "application/json",
    "accept-language": "ar",
    "User-Agent": "okhttp/5.0.0-alpha.6",
}
farm_base = "https://go.farm.com.sa"

farm_paths = [
    "/public/api/v1.0/categories",
    "/public/api/v1.0/products",
    "/public/api/v1.0/home",
    "/public/api/v1.0/stores",
    "/public/api/v1.0/catalog",
    "/public/api/v2/categories",
    "/public/api/v2/products",
    "/api/v1/categories",
    "/api/v1/products",
    "/api/v2/categories",
    "/api/v2/products",
    "/api/categories",
    "/api/products",
]

for path in farm_paths:
    try:
        r = client.get(f"{farm_base}{path}", headers=farm_h, timeout=10)
        has = r.status_code == 200 and len(r.content) > 50
        if r.status_code not in (404,):
            print(f"  [{r.status_code}] {path} size={len(r.content)} {'DATA!' if has else ''}")
            if has:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"       Keys: {list(d.keys())[:10]}")
                    print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
                except:
                    print(f"       Raw: {r.content[:200]}")
    except Exception as e:
        print(f"  [ERR] {path} -> {type(e).__name__}")

# Try farm.com.sa web
print("\n  --- farm.com.sa web ---")
for base in ["https://farm.com.sa", "https://www.farm.com.sa"]:
    try:
        r = client.get(base, headers={
            "Accept": "text/html",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
        }, timeout=10)
        print(f"  [{r.status_code}] {base} size={len(r.content)}")
        if r.status_code == 200:
            import re
            apis = set(re.findall(r'https?://[^\s"\'<>]+api[^\s"\'<>]*', r.text))
            for a in sorted(apis)[:5]:
                print(f"    API: {a}")
    except Exception as e:
        print(f"  [ERR] {base} -> {type(e).__name__}")

# ============================================================
# 4. RAMEZ (Risteh platform)
# ============================================================
print("\n" + "=" * 60)
print("4. RAMEZ")
print("=" * 60)
ramez_h = {
    "Accept": "application/json",
    "accept-language": "ar",
    "app_version": "5.9.4",
    "device_type": "iOS",
    "apikey": "^~>h2q=m[h=>3?bU/!M'X!m~?4GjKJP{Q@y;~fa3Vjs/M#`8FuB;x[LKwJ&>gNrxBt8!5PZ:9QLuHBUtu{TPc2s]k74]Br?PGe6+NcFUT-8",
    "User-Agent": "Ramez/8 CFNetwork/1404.0.5 Darwin/22.3.0",
}

ramez_base = "https://risteh.com/SA/GroceryStoreApi"
ramez_paths = [
    "/api/v9/Categories/list",
    "/api/v9/Products/list",
    "/api/v9/Home",
    "/api/v9/Home/index",
    "/api/v9/Categories",
    "/api/v9/Products",
    "/api/v9/Products?page=1&limit=5",
    "/api/v8/Categories/list",
    "/api/v8/Products/list",
]

for path in ramez_paths:
    for method in ["GET", "POST"]:
        try:
            if method == "GET":
                r = client.get(f"{ramez_base}{path}", headers=ramez_h, timeout=10)
            else:
                r = client.post(f"{ramez_base}{path}", json={}, headers=ramez_h, timeout=10)
            has = r.status_code == 200 and len(r.content) > 50
            if r.status_code not in (404, 405):
                print(f"  [{r.status_code}] {method} {path} size={len(r.content)} {'DATA!' if has else ''}")
                if has:
                    try:
                        d = r.json()
                        if isinstance(d, dict):
                            print(f"       Keys: {list(d.keys())[:10]}")
                        print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
                    except:
                        pass
        except Exception as e:
            if "ConnectError" not in str(type(e).__name__):
                print(f"  [ERR] {method} {path} -> {type(e).__name__}")

# Also try alternative Ramez patterns
print("\n  --- Alternative Ramez paths ---")
for base in ["https://risteh.com/SA", "https://risteh.com"]:
    for path in ["/api/v9/Categories/list", "/api/v9/Products/list", "/categories", "/products"]:
        try:
            r = client.get(f"{base}{path}", headers=ramez_h, timeout=8)
            has = r.status_code == 200 and len(r.content) > 50
            if r.status_code not in (404,) and has:
                print(f"  [{r.status_code}] {base}{path} size={len(r.content)} DATA!")
                d = r.json()
                print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
        except:
            pass

# ============================================================
# 5. SADHAN (Eldokan platform)
# ============================================================
print("\n" + "=" * 60)
print("5. SADHAN (AL SADHAN)")
print("=" * 60)
sadhan_h = {
    "Accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "User-Agent": "Alsadhan%20Stores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
}
sadhan_base = "https://sadhanmarketapi.witheldokan.com"
sadhan_paths = [
    "/api/categories",
    "/api/products",
    "/api/products?limit=5",
    "/api/v1/categories",
    "/api/v1/products",
    "/api/customer/categories",
    "/api/customer/products",
    "/api/store/categories",
    "/api/store/products",
    "/api/home",
    "/api/catalog",
    # Eldokan specific
    "/api/guest/categories",
    "/api/guest/products",
    "/api/guest/home",
    "/categories",
    "/products",
]

for path in sadhan_paths:
    try:
        r = client.get(f"{sadhan_base}{path}", headers=sadhan_h, timeout=10)
        has = r.status_code == 200 and len(r.content) > 50
        if r.status_code not in (404,):
            print(f"  [{r.status_code}] {path} size={len(r.content)} {'DATA!' if has else ''}")
            if has:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"       Keys: {list(d.keys())[:10]}")
                    print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
                except:
                    pass
    except Exception as e:
        print(f"  [ERR] {path} -> {type(e).__name__}")

# ============================================================
# 6. SPAR
# ============================================================
print("\n" + "=" * 60)
print("6. SPAR")
print("=" * 60)
spar_h = {
    "Accept": "application/json",
    "User-Agent": "okhttp/5.0.0-alpha.6",
}
spar_bases = [
    "https://www.spar.sa",
    "https://spar.sa",
    "https://api.spar.sa",
    "https://www.sparsaudi.com",
    "https://sparsaudi.com",
]
for base in spar_bases:
    for path in ["/api/categories", "/api/products", "/categories", "/products"]:
        try:
            r = client.get(f"{base}{path}", headers=spar_h, timeout=8)
            has = r.status_code == 200 and len(r.content) > 50
            if r.status_code not in (404, 502, 503):
                print(f"  [{r.status_code}] {base}{path} size={len(r.content)} {'DATA!' if has else ''}")
                if has:
                    try:
                        d = r.json()
                        print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
                    except:
                        pass
        except Exception as e:
            if "ConnectError" not in str(type(e).__name__):
                print(f"  [ERR] {base}{path} -> {type(e).__name__}")
            break

# ============================================================
# 7. DANUBE (bonus - popular Saudi chain)
# ============================================================
print("\n" + "=" * 60)
print("7. DANUBE / BINDAWOOD (bonus)")
print("=" * 60)
danube_h = {
    "Accept": "application/json",
    "User-Agent": "okhttp/5.0.0-alpha.6",
    "Accept-Language": "ar",
}
danube_bases = [
    "https://www.danubehome.com",
    "https://api.danubehome.com",
    "https://www.bindawood.com",
    "https://api.bindawood.com",
]
for base in danube_bases:
    for path in ["/api/categories", "/api/products", "/api/v1/categories", "/api/v1/products"]:
        try:
            r = client.get(f"{base}{path}", headers=danube_h, timeout=8)
            has = r.status_code == 200 and len(r.content) > 50
            if r.status_code not in (404, 502, 503):
                print(f"  [{r.status_code}] {base}{path} size={len(r.content)} {'DATA!' if has else ''}")
                if has:
                    try:
                        d = r.json()
                        print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
                    except:
                        pass
        except Exception as e:
            if "ConnectError" not in str(type(e).__name__):
                print(f"  [ERR] {base}{path} -> {type(e).__name__}")
            break

client.close()
print("\n=== ALL STORES DONE ===")
