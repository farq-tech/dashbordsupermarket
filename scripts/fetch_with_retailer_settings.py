#!/usr/bin/env python3
"""Use EXACT retailer settings from Fustog API to access each store"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
client = httpx.Client(timeout=20.0, follow_redirects=True)

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 1. RAMEZ - Has API key
# ============================================================
print("=" * 60)
print("1. RAMEZ (with API key from settings)")
print("=" * 60)

ramez_h = {
    "Accept": "application/json",
    "apikey": "^~>h2q=m[h=>3?bU/!M'X!m~?4GjKJP{Q@y;~fa3Vjs/M#`8FuB;x[LKwJ&>gNrxBt8!5PZ:9QLuHBUtu{TPc2s]k74]Br?PGe6+NcFUT-8",
    "User-Agent": "Ramez/8 CFNetwork/1404.0.5 Darwin/22.3.0",
    "accept-language": "ar",
    "device_type": "iOS",
    "app_version": "5.9.4",
    "accept-encoding": "deflate",
}

# Try multiple API versions and endpoints
ramez_base = "https://risteh.com/SA/GroceryStoreApi/api"
ramez_endpoints = [
    # v9 endpoints
    f"{ramez_base}/v9/Home",
    f"{ramez_base}/v9/Category",
    f"{ramez_base}/v9/Categories",
    f"{ramez_base}/v9/Products",
    f"{ramez_base}/v9/Products/list",
    f"{ramez_base}/v9/Products/all",
    f"{ramez_base}/v9/Product/list",
    f"{ramez_base}/v9/Search?q=rice",
    f"{ramez_base}/v9/Menu",
    # v8 endpoints
    f"{ramez_base}/v8/Home",
    f"{ramez_base}/v8/Categories",
    f"{ramez_base}/v8/Products",
    # Different base
    "https://risteh.com/SA/GroceryStoreApi/v9/Home",
    "https://risteh.com/SA/GroceryStoreApi/v9/Categories",
    # Try without SA
    "https://risteh.com/GroceryStoreApi/api/v9/Home",
]

for url in ramez_endpoints:
    try:
        r = client.get(url, headers=ramez_h, timeout=10)
        if r.status_code != 404 and len(r.content) > 50:
            print(f"  [{r.status_code}] {url.split('risteh.com')[1][:60]} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        for k in d:
                            val = d[k]
                            if isinstance(val, list) and len(val) > 0:
                                print(f"    .{k} = List[{len(val)}]")
                                if isinstance(val[0], dict):
                                    print(f"    First keys: {list(val[0].keys())[:12]}")
                                    print(f"    Sample: {json.dumps(val[0], ensure_ascii=False)[:300]}")
                        save(f"ramez_{url.split('/')[-1].split('?')[0].lower()}.json", d)
                    elif isinstance(d, list) and d:
                        print(f"    Array[{len(d)}]")
                        if isinstance(d[0], dict):
                            print(f"    First keys: {list(d[0].keys())[:12]}")
                except:
                    pass
    except Exception as e:
        err = str(type(e).__name__)
        if "timeout" in err.lower() or "connect" in err.lower():
            print(f"  [TIMEOUT/CONN] {url.split('risteh.com')[1][:40]}")
        else:
            print(f"  [{err}] {url.split('risteh.com')[1][:40]}")

# ============================================================
# 2. LULU - Akinon cloud
# ============================================================
print("\n" + "=" * 60)
print("2. LULU (Akinon cloud)")
print("=" * 60)

lulu_h = {
    "Accept": "*/*",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "accept-language": "ar;q=1.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
    "Content-Type": "application/x-www-form-urlencoded",
}

lulu_base = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"
lulu_endpoints = [
    "/users/otp-login/",
    "/products/",
    "/categories/",
    "/search/",
    "/menu/",
    "/widgets/",
    "/home/",
    "/catalog/",
    "/api/v1/products/",
    "/api/v1/categories/",
    "/api/v2/products/",
    "/api/v2/categories/",
    "/users/",
    "/basket/",
    "/orders/",
]

for ep in lulu_endpoints:
    try:
        r = client.get(f"{lulu_base}{ep}", headers=lulu_h, timeout=10)
        if r.status_code not in (404, 405) and len(r.content) > 50:
            print(f"  [{r.status_code}] {ep} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        for k in ["products", "items", "results", "data", "categories"]:
                            if k in d:
                                val = d[k]
                                if isinstance(val, list):
                                    print(f"    .{k} = List[{len(val)}]")
                                    if val and isinstance(val[0], dict):
                                        print(f"    First keys: {list(val[0].keys())[:12]}")
                    save(f"lulu_akinon_{ep.strip('/').replace('/', '_')}.json", d)
                except:
                    pass
        elif r.status_code == 405:
            # Try POST
            r2 = client.post(f"{lulu_base}{ep}", headers=lulu_h, timeout=10)
            if r2.status_code != 404 and len(r2.content) > 50:
                print(f"  [{r2.status_code}] POST {ep} size={len(r2.content)}")
    except Exception as e:
        err = str(type(e).__name__)
        if "timeout" not in err.lower() and "connect" not in err.lower():
            print(f"  [{err}] {ep}")

# ============================================================
# 3. FARM - Correct API URL
# ============================================================
print("\n" + "=" * 60)
print("3. FARM (from retailer settings)")
print("=" * 60)

farm_h = {
    "Accept": "application/json",
    "accept-encoding": "deflate",
    "accept-language": "en-US,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
}

farm_base = "https://go.farm.com.sa/public/api"
farm_endpoints = [
    "/v1.0/home",
    "/v1.0/categories",
    "/v1.0/products",
    "/v1.0/stores",
    "/v1.0/catalog",
    "/v2.0/home",
    "/v2.0/categories",
    "/v2.0/products",
    "/v2/home",
    "/v2/categories",
    "/v2/products",
]

for ep in farm_endpoints:
    try:
        r = client.get(f"{farm_base}{ep}", headers=farm_h, timeout=10)
        if len(r.content) > 50:
            print(f"  [{r.status_code}] {ep} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        if "status" in d and not d.get("status"):
                            print(f"    Error: {d.get('message', '')[:100]}")
                except:
                    pass
    except Exception as e:
        err = str(type(e).__name__)
        if "timeout" not in err.lower():
            print(f"  [{err}] {ep}")

# ============================================================
# 4. SADHAN - Correct API
# ============================================================
print("\n" + "=" * 60)
print("4. SADHAN (from retailer settings)")
print("=" * 60)

sadhan_h = {
    "Accept": "application/json",
    "accept-encoding": "deflate",
    "accept-language": "en-US,en;q=0.9",
    "User-Agent": "Alsadhan%20Stores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
}

sadhan_base = "https://sadhanmarketapi.witheldokan.com/api"
sadhan_endpoints = [
    "/home",
    "/categories",
    "/products",
    "/catalog",
    "/menu",
    "/customer/home",
    "/v1/home",
    "/v1/categories",
    "/v1/products",
]

for ep in sadhan_endpoints:
    try:
        r = client.get(f"{sadhan_base}{ep}", headers=sadhan_h, timeout=10)
        if len(r.content) > 50:
            print(f"  [{r.status_code}] {ep} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        if "message" in d:
                            print(f"    Message: {d.get('message', '')[:100]}")
                except:
                    pass
    except Exception as e:
        err = str(type(e).__name__)
        if "connect" in err.lower() or "timeout" in err.lower():
            print(f"  [TIMEOUT] {ep}")
            break  # Stop trying if server is down
        else:
            print(f"  [{err}] {ep}")

client.close()
print("\n=== DONE ===")
