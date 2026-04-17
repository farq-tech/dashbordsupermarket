#!/usr/bin/env python3
"""Try to fetch products directly from individual retailer APIs"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import httpx

client = httpx.Client(timeout=15.0, follow_redirects=True)

# ============ TAMIMI ============
print("=" * 60)
print("1. TAMIMI (shop.tamimimarkets.com)")
print("=" * 60)
tamimi_headers = {
    "Accept": "application/json",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16)",
    "Accept-Language": "ar",
}
tamimi_urls = [
    "https://shop.tamimimarkets.com/api/categories",
    "https://shop.tamimimarkets.com/api/products",
    "https://shop.tamimimarkets.com/api/catalog",
    "https://shop.tamimimarkets.com/api/items",
]
for url in tamimi_urls:
    try:
        r = client.get(url, headers=tamimi_headers, timeout=10)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 2:
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else None
            if data:
                if isinstance(data, list):
                    print(f"    List of {len(data)} items")
                    if data:
                        print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:300]}")
                elif isinstance(data, dict):
                    print(f"    Keys: {list(data.keys())[:15]}")
                    preview = json.dumps(data, ensure_ascii=False)[:500]
                    print(f"    Data: {preview}")
    except Exception as e:
        print(f"  [ERR] {url} -> {type(e).__name__}: {e}")

# ============ PANDA ============
print("\n" + "=" * 60)
print("2. PANDA (api.panda.sa)")
print("=" * 60)
panda_headers = {
    "Accept": "application/json;charset=UTF-8",
    "User-Agent": "okhttp/5.0.0-alpha.6",
    "x-language": "ar",
    "x-pandaclick-agent": "4",
    "x-panda-source": "PandaClick",
}
panda_urls = [
    "https://api.panda.sa/v3/categories",
    "https://api.panda.sa/v3/products",
    "https://api.panda.sa/v3/catalog",
    "https://api.panda.sa/v3/stores",
    "https://api.panda.sa/v3/items",
    "https://api.panda.sa/v3/home",
]
for url in panda_urls:
    try:
        r = client.get(url, headers=panda_headers, timeout=10)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 2:
            try:
                data = r.json()
                if isinstance(data, list):
                    print(f"    List of {len(data)} items")
                    if data:
                        print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:300]}")
                elif isinstance(data, dict):
                    print(f"    Keys: {list(data.keys())[:15]}")
            except:
                pass
    except Exception as e:
        print(f"  [ERR] {url} -> {type(e).__name__}: {e}")

# ============ CARREFOUR ============
print("\n" + "=" * 60)
print("3. CARREFOUR")
print("=" * 60)
carrefour_headers = {
    "Accept": "*/*",
    "User-Agent": "Carrefour/3 CFNetwork/1410.0.3 Darwin/22.6.0",
    "accept-language": "ar",
    "storeid": "mafsau",
    "currency": "SAR",
    "langcode": "ar",
    "appid": "IOS",
    "env": "PROD",
}
carrefour_urls = [
    "https://www.carrefourksa.com/api/v1/categories",
    "https://www.carrefourksa.com/api/categories",
    "https://api.carrefourksa.com/api/v1/categories",
    "https://api.carrefourksa.com/api/products",
]
for url in carrefour_urls:
    try:
        r = client.get(url, headers=carrefour_headers, timeout=10)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 2:
            try:
                data = r.json()
                if isinstance(data, list):
                    print(f"    List of {len(data)} items")
                elif isinstance(data, dict):
                    print(f"    Keys: {list(data.keys())[:15]}")
            except:
                pass
    except Exception as e:
        print(f"  [ERR] {url} -> {type(e).__name__}: {e}")

# ============ LULU ============
print("\n" + "=" * 60)
print("4. LULU")
print("=" * 60)
lulu_headers = {
    "Accept": "*/*",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "accept-language": "ar;q=1.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
}
lulu_base = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"
lulu_urls = [
    f"{lulu_base}/categories/",
    f"{lulu_base}/products/",
    f"{lulu_base}/catalogue/",
]
for url in lulu_urls:
    try:
        r = client.get(url, headers=lulu_headers, timeout=10)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 2:
            try:
                data = r.json()
                if isinstance(data, list):
                    print(f"    List of {len(data)} items")
                elif isinstance(data, dict):
                    print(f"    Keys: {list(data.keys())[:15]}")
                    print(f"    Data: {json.dumps(data, ensure_ascii=False)[:500]}")
            except:
                pass
    except Exception as e:
        print(f"  [ERR] {url} -> {type(e).__name__}: {e}")

# ============ FARM ============
print("\n" + "=" * 60)
print("5. FARM (go.farm.com.sa)")
print("=" * 60)
farm_headers = {
    "Accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
}
farm_urls = [
    "https://go.farm.com.sa/public/api/v1.0/categories",
    "https://go.farm.com.sa/public/api/v1.0/products",
    "https://go.farm.com.sa/public/api/v1.0/home",
]
for url in farm_urls:
    try:
        r = client.get(url, headers=farm_headers, timeout=10)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 2:
            try:
                data = r.json()
                if isinstance(data, list):
                    print(f"    List of {len(data)} items")
                elif isinstance(data, dict):
                    print(f"    Keys: {list(data.keys())[:15]}")
            except:
                pass
    except Exception as e:
        print(f"  [ERR] {url} -> {type(e).__name__}: {e}")

# ============ RAMEZ ============
print("\n" + "=" * 60)
print("6. RAMEZ (risteh.com)")
print("=" * 60)
ramez_headers = {
    "Accept": "application/json",
    "accept-language": "ar",
    "app_version": "5.9.4",
    "device_type": "iOS",
    "apikey": "^~>h2q=m[h=>3?bU/!M'X!m~?4GjKJP{Q@y;~fa3Vjs/M#`8FuB;x[LKwJ&>gNrxBt8!5PZ:9QLuHBUtu{TPc2s]k74]Br?PGe6+NcFUT-8",
    "User-Agent": "Ramez/8 CFNetwork/1404.0.5 Darwin/22.3.0",
}
ramez_urls = [
    "https://risteh.com/SA/GroceryStoreApi/api/v9/Categories/list",
    "https://risteh.com/SA/GroceryStoreApi/api/v9/Products/list",
    "https://risteh.com/SA/GroceryStoreApi/api/v9/Home",
]
for url in ramez_urls:
    try:
        r = client.get(url, headers=ramez_headers, timeout=10)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 2:
            try:
                data = r.json()
                if isinstance(data, list):
                    print(f"    List of {len(data)} items")
                    if data:
                        print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:300]}")
                elif isinstance(data, dict):
                    print(f"    Keys: {list(data.keys())[:15]}")
                    print(f"    Data: {json.dumps(data, ensure_ascii=False)[:500]}")
            except:
                pass
    except Exception as e:
        print(f"  [ERR] {url} -> {type(e).__name__}: {e}")

client.close()
print("\n=== DONE ===")
