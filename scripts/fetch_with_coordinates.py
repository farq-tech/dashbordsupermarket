#!/usr/bin/env python3
"""Try store APIs with Riyadh coordinates - some require location"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

# Riyadh coordinates
LAT = 24.7136
LNG = 46.6753

client = httpx.Client(timeout=20.0, follow_redirects=True)

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 1. LULU - Akinon with location
# ============================================================
print("=" * 60)
print("1. LULU (with Riyadh coordinates)")
print("=" * 60)

lulu_h = {
    "Accept": "*/*",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "accept-language": "ar;q=1.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
}

lulu_base = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"

# Try with location params
lulu_endpoints = [
    f"/products/?lat={LAT}&lng={LNG}&limit=50",
    f"/categories/?lat={LAT}&lng={LNG}",
    f"/products/?latitude={LAT}&longitude={LNG}&limit=50",
    f"/products/?location={LAT},{LNG}&limit=50",
    f"/stores/?lat={LAT}&lng={LNG}",
    f"/products/?page_size=50",
    f"/categories/tree/",
    f"/search/?q=rice&lat={LAT}&lng={LNG}",
]

for ep in lulu_endpoints:
    try:
        r = client.get(f"{lulu_base}{ep}", headers=lulu_h, timeout=10)
        if r.status_code not in (404,) and len(r.content) > 50:
            print(f"  [{r.status_code}] {ep[:60]} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        for k in ["products", "items", "results", "data", "categories", "count"]:
                            if k in d:
                                val = d[k]
                                if isinstance(val, list):
                                    print(f"    .{k} = List[{len(val)}]")
                                    if val and isinstance(val[0], dict):
                                        print(f"    First keys: {list(val[0].keys())[:12]}")
                                        print(f"    Sample: {json.dumps(val[0], ensure_ascii=False)[:300]}")
                                elif isinstance(val, (int, float)):
                                    print(f"    .{k} = {val}")
                        save(f"lulu_coord_{ep.split('/')[1].split('?')[0]}.json", d)
                    elif isinstance(d, list) and d:
                        print(f"    Array[{len(d)}]")
                        if isinstance(d[0], dict):
                            print(f"    First keys: {list(d[0].keys())[:12]}")
                            print(f"    Sample: {json.dumps(d[0], ensure_ascii=False)[:300]}")
                        save(f"lulu_coord_{ep.split('/')[1].split('?')[0]}.json", d)
                except:
                    pass
    except Exception as e:
        pass

# Try gcc.luluhypermarket.com with location
print("\n  Trying gcc API with coordinates...")
gcc_h = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36",
    "Referer": "https://www.luluhypermarket.com/",
    "Origin": "https://www.luluhypermarket.com",
}

gcc_endpoints = [
    f"/api/client/products/?lat={LAT}&lng={LNG}&limit=50",
    f"/api/client/categories/?lat={LAT}&lng={LNG}",
    f"/api/client/stores/?lat={LAT}&lng={LNG}",
    f"/api/client/widgets/home-slider-sa/?lat={LAT}&lng={LNG}",
    f"/api/hot-food-config?lat={LAT}&lng={LNG}",
]

for ep in gcc_endpoints:
    try:
        r = client.get(f"https://gcc.luluhypermarket.com{ep}", headers=gcc_h, timeout=10)
        if r.status_code not in (404,) and len(r.content) > 50:
            print(f"  [{r.status_code}] {ep[:60]} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                    save(f"lulu_gcc_{ep.split('/')[-1].split('?')[0]}.json", d)
                except:
                    pass
    except:
        pass

# ============================================================
# 2. RAMEZ - with location
# ============================================================
print("\n" + "=" * 60)
print("2. RAMEZ (with Riyadh coordinates)")
print("=" * 60)

ramez_h = {
    "Accept": "application/json",
    "apikey": "^~>h2q=m[h=>3?bU/!M'X!m~?4GjKJP{Q@y;~fa3Vjs/M#`8FuB;x[LKwJ&>gNrxBt8!5PZ:9QLuHBUtu{TPc2s]k74]Br?PGe6+NcFUT-8",
    "User-Agent": "Ramez/8 CFNetwork/1404.0.5 Darwin/22.3.0",
    "accept-language": "ar",
    "device_type": "iOS",
    "app_version": "5.9.4",
    "latitude": str(LAT),
    "longitude": str(LNG),
}

ramez_endpoints = [
    f"https://risteh.com/SA/GroceryStoreApi/api/v9/Home?lat={LAT}&lng={LNG}",
    f"https://risteh.com/SA/GroceryStoreApi/api/v9/Category?lat={LAT}&lng={LNG}",
    f"https://risteh.com/SA/GroceryStoreApi/api/v9/Products?lat={LAT}&lng={LNG}",
    f"https://risteh.com/SA/GroceryStoreApi/api/v9/Store?lat={LAT}&lng={LNG}",
    f"https://risteh.com/SA/GroceryStoreApi/api/v9/Home",
]

for url in ramez_endpoints:
    try:
        r = client.get(url, headers=ramez_h, timeout=10)
        if r.status_code != 404 and len(r.content) > 50:
            print(f"  [{r.status_code}] {url.split('v9/')[1] if 'v9/' in url else url[-30:]} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        for k in d:
                            val = d[k]
                            if isinstance(val, list) and val:
                                print(f"    .{k} = List[{len(val)}]")
                                if isinstance(val[0], dict):
                                    print(f"    First keys: {list(val[0].keys())[:12]}")
                                    print(f"    Sample: {json.dumps(val[0], ensure_ascii=False)[:300]}")
                        save(f"ramez_coord.json", d)
                except:
                    pass
    except Exception as e:
        err = type(e).__name__
        if "connect" in err.lower() or "timeout" in err.lower():
            print(f"  [CONN/TIMEOUT] {url.split('v9/')[1] if 'v9/' in url else url[-30:]}")
        else:
            print(f"  [{err}] {url.split('v9/')[1] if 'v9/' in url else url[-30:]}")

# ============================================================
# 3. FARM - with location
# ============================================================
print("\n" + "=" * 60)
print("3. FARM (with Riyadh coordinates)")
print("=" * 60)

farm_h = {
    "Accept": "application/json",
    "accept-language": "ar",
    "User-Agent": "FarmApp/1 CFNetwork/1404.0.5 Darwin/22.3.0",
}

farm_endpoints = [
    f"https://go.farm.com.sa/public/api/v1.0/home?lat={LAT}&lng={LNG}",
    f"https://go.farm.com.sa/public/api/v1.0/user/store?lat={LAT}&lng={LNG}",
    f"https://go.farm.com.sa/public/api/v1.0/store?lat={LAT}&lng={LNG}",
    f"https://go.farm.com.sa/public/api/v1.0/stores?lat={LAT}&lng={LNG}",
    f"https://go.farm.com.sa/public/api/v1.0/categories?lat={LAT}&lng={LNG}",
    f"https://go.farm.com.sa/public/api/v1.0/products?lat={LAT}&lng={LNG}",
]

for url in farm_endpoints:
    try:
        r = client.get(url, headers=farm_h, timeout=10)
        if len(r.content) > 50:
            print(f"  [{r.status_code}] {url.split('v1.0/')[1][:40]} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        if d.get("status") is False:
                            print(f"    Error: {d.get('message', '')[:80]}")
                        else:
                            for k in d:
                                val = d[k]
                                if isinstance(val, list) and val:
                                    print(f"    .{k} = List[{len(val)}]")
                                    if isinstance(val[0], dict):
                                        print(f"    First keys: {list(val[0].keys())[:12]}")
                                        print(f"    Sample: {json.dumps(val[0], ensure_ascii=False)[:300]}")
                            save(f"farm_coord_{url.split('v1.0/')[1].split('?')[0]}.json", d)
                except:
                    pass
    except Exception as e:
        err = type(e).__name__
        print(f"  [{err}] {url.split('v1.0/')[1][:40] if 'v1.0/' in url else url[-30:]}")

# ============================================================
# 4. SADHAN - with location
# ============================================================
print("\n" + "=" * 60)
print("4. SADHAN (with Riyadh coordinates)")
print("=" * 60)

sadhan_h = {
    "Accept": "application/json",
    "User-Agent": "Alsadhan%20Stores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
    "accept-language": "ar",
    "Referer": "https://alsadhan.witheldokan.com/",
    "latitude": str(LAT),
    "longitude": str(LNG),
}

sadhan_endpoints = [
    f"https://masterapi.witheldokan.com/api/home?lat={LAT}&lng={LNG}",
    f"https://masterapi.witheldokan.com/api/categories?lat={LAT}&lng={LNG}",
    f"https://masterapi.witheldokan.com/api/products?lat={LAT}&lng={LNG}",
    f"https://masterapi.witheldokan.com/api/stores?lat={LAT}&lng={LNG}",
    f"https://masterapi.witheldokan.com/api/store?lat={LAT}&lng={LNG}",
]

for url in sadhan_endpoints:
    try:
        r = client.get(url, headers=sadhan_h, timeout=10)
        if len(r.content) > 50:
            print(f"  [{r.status_code}] {url.split('.com')[1][:40]} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        if "errors" in d:
                            print(f"    Error: {d.get('message', '')[:80]}")
                        else:
                            for k in d:
                                val = d[k]
                                if isinstance(val, list) and val:
                                    print(f"    .{k} = List[{len(val)}]")
                            save(f"sadhan_coord_{url.split('/')[-1].split('?')[0]}.json", d)
                except:
                    pass
    except Exception as e:
        err = type(e).__name__
        if "timeout" in err.lower() or "connect" in err.lower():
            print(f"  [TIMEOUT] stopping sadhan")
            break
        print(f"  [{err}] {url.split('.com')[1][:40]}")

# ============================================================
# 5. CARREFOUR - with location (skipped per user but try quickly)
# ============================================================
# User said skip carrefour - skipping

client.close()
print("\n=== DONE ===")
