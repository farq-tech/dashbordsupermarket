#!/usr/bin/env python3
"""Discover product endpoints for ALL retailer stores"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import httpx

client = httpx.Client(timeout=15.0, follow_redirects=True)

# First get full retailer settings
print("=" * 70)
print("FULL RETAILER SETTINGS")
print("=" * 70)
r = client.get("https://api.fustog.app/api/v1/retailer/Settings", headers={
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16)",
    "Accept": "application/json",
})
try:
    settings = r.json()
except:
    # Fallback: load from previously saved file
    import os
    cached = "data/retailer_settings_full.json"
    if os.path.exists(cached):
        with open(cached, "r", encoding="utf-8") as f:
            settings = json.load(f)
        print("  (Loaded from cache)")
    else:
        settings = {}

# Save full settings
with open("data/retailer_settings_full.json", "w", encoding="utf-8") as f:
    json.dump(settings, f, ensure_ascii=False, indent=2)
print("Saved full settings to data/retailer_settings_full.json")

for store, config in settings.items():
    print(f"\n--- {store.upper()} ---")
    for k, v in config.items():
        print(f"  {k}: {v}")

def test_url(url, headers=None, method="GET", label=""):
    try:
        h = headers or {"Accept": "application/json", "User-Agent": "okhttp/5.0.0-alpha.6"}
        if method == "GET":
            r = client.get(url, headers=h, timeout=10)
        else:
            r = client.post(url, headers=h, timeout=10)
        has_data = r.status_code == 200 and len(r.content) > 10
        icon = "OK" if has_data else str(r.status_code)
        print(f"  [{icon}] {method} {url} size={len(r.content)}")
        if has_data:
            try:
                data = r.json()
                if isinstance(data, list):
                    print(f"       List[{len(data)}] keys={list(data[0].keys())[:8] if data else 'empty'}")
                elif isinstance(data, dict):
                    print(f"       Dict keys={list(data.keys())[:10]}")
                    # Look for product/item arrays
                    for k in ["data", "products", "items", "results", "categories", "content"]:
                        if k in data:
                            val = data[k]
                            if isinstance(val, list):
                                print(f"       .{k} = List[{len(val)}]")
                            elif isinstance(val, dict):
                                print(f"       .{k} = Dict keys={list(val.keys())[:10]}")
            except:
                pass
        return has_data
    except Exception as e:
        print(f"  [ERR] {method} {url} -> {type(e).__name__}")
        return False

# ============ TAMIMI ============
print("\n" + "=" * 70)
print("1. TAMIMI EXPLORATION")
print("=" * 70)
tamimi_h = {"Accept": "*/*", "accept-language": "ar", "medium": "APP", "User-Agent": "okhttp/5.0.0-alpha.6"}
tamimi_bases = [
    "https://shop.tamimimarkets.com",
    "https://api.tamimimarkets.com",
    "https://tamimimarkets.com",
]
tamimi_paths = [
    "/api/categories", "/api/products", "/api/catalog", "/api/home",
    "/api/v1/categories", "/api/v1/products", "/api/v1/catalog",
    "/api/v2/categories", "/api/v2/products",
    "/categories", "/products", "/home",
    "/api/store/categories", "/api/store/products",
    "/api/grocery/categories", "/api/grocery/products",
]
for base in tamimi_bases:
    for path in tamimi_paths:
        test_url(f"{base}{path}", tamimi_h)

# ============ CARREFOUR ============
print("\n" + "=" * 70)
print("2. CARREFOUR EXPLORATION")
print("=" * 70)
carrefour_h = {
    "Accept": "*/*",
    "User-Agent": "Carrefour/3 CFNetwork/1410.0.3 Darwin/22.6.0",
    "accept-language": "ar",
    "storeid": "mafsau",
    "currency": "SAR",
    "langcode": "ar",
    "appid": "IOS",
    "env": "PROD",
}
carrefour_bases = [
    "https://www.carrefourksa.com",
    "https://api.carrefourksa.com",
    "https://api-prod.retailsso.com",
]
carrefour_paths = [
    "/api/v1/categories", "/api/v1/products", "/api/v1/catalog",
    "/api/v2/categories", "/api/v2/products",
    "/api/categories", "/api/products",
    "/v1/categories", "/v1/products",
    "/v2/categories", "/v2/products",
    "/v2/customers/categories",
]
for base in carrefour_bases:
    for path in carrefour_paths:
        test_url(f"{base}{path}", carrefour_h)

# ============ LULU ============
print("\n" + "=" * 70)
print("3. LULU EXPLORATION")
print("=" * 70)
lulu_h = {
    "Accept": "*/*",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "accept-language": "ar;q=1.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
}
lulu_base = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"
lulu_paths = [
    "/api/categories/", "/api/products/",
    "/api/v1/categories/", "/api/v1/products/",
    "/api/v2/categories/", "/api/v2/products/",
    "/catalogue/categories/", "/catalogue/products/",
    "/search/products/", "/store/categories/",
    "/users/otp-login/",
]
for path in lulu_paths:
    test_url(f"{lulu_base}{path}", lulu_h)

# Also try luluhypermarket.com
lulu_alt_bases = [
    "https://www.luluhypermarket.com",
    "https://api.luluhypermarket.com",
    "https://lulu.sa",
    "https://www.lulu-saudi.com",
]
for base in lulu_alt_bases:
    for path in ["/api/categories", "/api/products", "/api/v1/categories", "/api/v1/products"]:
        test_url(f"{base}{path}", lulu_h)

# ============ FARM ============
print("\n" + "=" * 70)
print("4. FARM EXPLORATION")
print("=" * 70)
farm_h = {"Accept": "application/json", "accept-language": "ar"}
farm_base = "https://go.farm.com.sa"
farm_paths = [
    "/public/api/v1.0/categories",
    "/public/api/v1.0/products",
    "/public/api/v1.0/home",
    "/public/api/v1.0/stores",
    "/public/api/v1.0/user/categories",
    "/public/api/v2/categories",
    "/public/api/v2/products",
    "/api/v1/categories",
    "/api/v1/products",
    "/api/categories",
    "/api/products",
]
for path in farm_paths:
    test_url(f"{farm_base}{path}", farm_h)

# ============ RAMEZ ============
print("\n" + "=" * 70)
print("5. RAMEZ EXPLORATION")
print("=" * 70)
ramez_h = {
    "Accept": "application/json",
    "accept-language": "ar",
    "app_version": "5.9.4",
    "device_type": "iOS",
    "apikey": "^~>h2q=m[h=>3?bU/!M'X!m~?4GjKJP{Q@y;~fa3Vjs/M#`8FuB;x[LKwJ&>gNrxBt8!5PZ:9QLuHBUtu{TPc2s]k74]Br?PGe6+NcFUT-8",
    "User-Agent": "Ramez/8 CFNetwork/1404.0.5 Darwin/22.3.0",
}
ramez_bases = [
    "https://risteh.com/SA/GroceryStoreApi",
    "https://risteh.com/SA",
    "https://risteh.com",
]
ramez_paths = [
    "/api/v9/Categories/list", "/api/v9/Products/list",
    "/api/v9/Categories", "/api/v9/Products",
    "/api/v9/Home", "/api/v9/Home/index",
    "/api/v8/Categories/list", "/api/v8/Products/list",
    "/api/v7/Categories/list", "/api/v7/Products/list",
    "/api/Categories", "/api/Products",
    "/categories", "/products",
]
for base in ramez_bases:
    for path in ramez_paths:
        test_url(f"{base}{path}", ramez_h)

# ============ SADHAN ============
print("\n" + "=" * 70)
print("6. SADHAN EXPLORATION")
print("=" * 70)
sadhan_h = {
    "Accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "User-Agent": "Alsadhan%20Stores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
}
sadhan_base = "https://sadhanmarketapi.witheldokan.com"
sadhan_paths = [
    "/api/customer/auth",
    "/api/categories", "/api/products",
    "/api/v1/categories", "/api/v1/products",
    "/api/customer/categories", "/api/customer/products",
    "/api/store/categories", "/api/store/products",
    "/api/home", "/api/catalog",
]
for path in sadhan_paths:
    test_url(f"{sadhan_base}{path}", sadhan_h)

# ============ SPAR ============
print("\n" + "=" * 70)
print("7. SPAR EXPLORATION")
print("=" * 70)
spar_h = {"Accept": "application/json", "User-Agent": "okhttp/5.0.0-alpha.6"}
spar_bases = [
    "https://api.spar.sa",
    "https://www.spar.sa",
    "https://spar.sa",
    "https://api.sparsa.com",
    "https://www.sparsaudi.com",
]
for base in spar_bases:
    for path in ["/api/categories", "/api/products", "/api/v1/categories", "/api/v1/products", "/categories", "/products"]:
        test_url(f"{base}{path}", spar_h)

# Check if spar info is in the settings
if "spar" in settings:
    print(f"\nSpar settings: {json.dumps(settings['spar'], ensure_ascii=False, indent=2)[:1000]}")

client.close()
print("\n=== DISCOVERY DONE ===")
