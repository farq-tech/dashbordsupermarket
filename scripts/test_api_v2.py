#!/usr/bin/env python3
"""Explore API v2 endpoints - the real data source!"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import httpx

# ===== LZ-String decompressor =====
_LZ_KEY = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
_LZ_REV = {}
def _lz_val(ch):
    if _LZ_KEY not in _LZ_REV:
        _LZ_REV[_LZ_KEY] = {c: i for i, c in enumerate(_LZ_KEY)}
    return _LZ_REV[_LZ_KEY][ch]
def lz_decompress(s):
    if not s: return ""
    s = "".join(s.split())
    length = len(s)
    def gnv(i): return _lz_val(s[i])
    d = {0: chr(0), 1: chr(1), 2: chr(2)}
    ei = 4; ds = 4; nb = 3; w = ""; r = []
    dv = gnv(0); dp = 32; di = 1
    bits = 0; mp = 4; pw = 1
    while pw != mp:
        resb = dv & dp; dp >>= 1
        if dp == 0: dp = 32; dv = gnv(di); di += 1
        bits |= (1 if resb > 0 else 0) * pw; pw <<= 1
    nx = bits
    if nx == 2: return ""
    bw = 8 if nx == 0 else 16
    bits = 0; mp = 2**bw; pw = 1
    while pw != mp:
        resb = dv & dp; dp >>= 1
        if dp == 0: dp = 32; dv = gnv(di); di += 1
        bits |= (1 if resb > 0 else 0) * pw; pw <<= 1
    c = chr(bits); d[3] = c; w = c; r.append(c)
    while True:
        if di > length: return "".join(r)
        bits = 0; mp = 2**nb; pw = 1
        while pw != mp:
            resb = dv & dp; dp >>= 1
            if dp == 0:
                dp = 32
                if di < length: dv = gnv(di); di += 1
                else: dv = 0
            bits |= (1 if resb > 0 else 0) * pw; pw <<= 1
        cc = bits
        if cc == 0 or cc == 1:
            bw = 8 if cc == 0 else 16
            bits = 0; mp = 2**bw; pw = 1
            while pw != mp:
                resb = dv & dp; dp >>= 1
                if dp == 0: dp = 32; dv = gnv(di); di += 1
                bits |= (1 if resb > 0 else 0) * pw; pw <<= 1
            d[ds] = chr(bits); cc = ds; ds += 1; ei -= 1
        elif cc == 2:
            return "".join(r)
        if ei == 0: ei = 2**nb; nb += 1
        if cc in d: entry = d[cc]
        elif cc == ds: entry = w + w[0]
        else: return ""
        r.append(entry); d[ds] = w + entry[0]; ds += 1; ei -= 1; w = entry
        if ei == 0: ei = 2**nb; nb += 1

def try_decode(resp):
    try:
        return resp.json()
    except Exception:
        text = resp.text or ""
        if text:
            try:
                return json.loads(lz_decompress(text))
            except Exception:
                pass
        return None

BASE_V2 = "https://api.fustog.app/api/v2"

client = httpx.Client(timeout=30.0, headers={
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16)",
    "Accept": "application/json, */*;q=0.5",
    "Accept-Encoding": "identity",
})

# 1. Categories v2
print("=" * 60)
print("1. v2 Categories")
print("=" * 60)
r = client.get(f"{BASE_V2}/category/Categories")
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
cats = try_decode(r)
if cats:
    if isinstance(cats, list):
        print(f"Categories: {len(cats)}")
        if len(cats) > 0:
            print(f"First item keys: {list(cats[0].keys()) if isinstance(cats[0], dict) else type(cats[0])}")
            print(f"First: {json.dumps(cats[0], ensure_ascii=False)[:500]}")
            # Save full v2 categories
            with open("data/categories_v2.json", "w", encoding="utf-8") as f:
                json.dump(cats, f, ensure_ascii=False, indent=2)
            print("Saved to data/categories_v2.json")

            # Collect all IDs
            all_ids = []
            for cat in cats:
                cid = cat.get("CID") or cat.get("id") or cat.get("categoryId")
                if cid:
                    all_ids.append(cid)
                for sub in cat.get("SubItmes", cat.get("subItems", cat.get("children", []))):
                    sid = sub.get("CID") or sub.get("id")
                    if sid:
                        all_ids.append(sid)
            print(f"All IDs: {all_ids[:30]}... (total: {len(all_ids)})")
    elif isinstance(cats, dict):
        print(f"Dict keys: {list(cats.keys())[:20]}")
        print(f"Full: {json.dumps(cats, ensure_ascii=False)[:2000]}")

# 2. Products v2 - GET
print("\n" + "=" * 60)
print("2. v2 Products - GET")
print("=" * 60)
for cid in [1, 12, 23, 48]:
    r = client.get(f"{BASE_V2}/product/ProductsByCategory", params={"categoryId": cid})
    has_data = r.status_code == 200 and len(r.content) > 0
    status = f"{r.status_code} size={len(r.content)}"
    print(f"  GET categoryId={cid} -> {status} {'DATA!' if has_data else ''}")
    if has_data:
        data = try_decode(r)
        if data and isinstance(data, list) and len(data) > 0:
            print(f"    Products: {len(data)}")
            print(f"    Keys: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
            print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
        elif data and isinstance(data, dict):
            print(f"    Dict: {json.dumps(data, ensure_ascii=False)[:500]}")

# 3. Products v2 - POST
print("\n" + "=" * 60)
print("3. v2 Products - POST")
print("=" * 60)
for cid in [1, 12, 23, 48]:
    r = client.post(f"{BASE_V2}/product/ProductsByCategory", params={"categoryId": cid})
    has_data = r.status_code == 200 and len(r.content) > 0
    status = f"{r.status_code} size={len(r.content)}"
    print(f"  POST categoryId={cid} -> {status} {'DATA!' if has_data else ''}")
    if has_data:
        data = try_decode(r)
        if data and isinstance(data, list) and len(data) > 0:
            print(f"    Products: {len(data)}")
            print(f"    Keys: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
            print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")

# 4. ItemsPrices v2
print("\n" + "=" * 60)
print("4. v2 ItemsPrices")
print("=" * 60)
for method in ["GET", "POST"]:
    if method == "GET":
        r = client.get(f"{BASE_V2}/product/ItemsPrices")
    else:
        r = client.post(f"{BASE_V2}/product/ItemsPrices")
    has_data = r.status_code == 200 and len(r.content) > 0
    print(f"  {method} -> {r.status_code} size={len(r.content)} {'DATA!' if has_data else ''}")
    if has_data:
        data = try_decode(r)
        if data and isinstance(data, list) and len(data) > 0:
            print(f"    Prices: {len(data)}")
            print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
        elif data and isinstance(data, dict):
            print(f"    Dict: {json.dumps(data, ensure_ascii=False)[:500]}")

# 5. Retailer Settings v2
print("\n" + "=" * 60)
print("5. v2 Retailer Settings")
print("=" * 60)
r = client.get(f"{BASE_V2}/retailer/Settings")
print(f"  GET -> {r.status_code} size={len(r.content)}")
if r.status_code == 200 and len(r.content) > 0:
    data = try_decode(r)
    if data:
        print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")

# 6. Search v2
print("\n" + "=" * 60)
print("6. v2 Search")
print("=" * 60)
for method in ["GET", "POST"]:
    if method == "GET":
        r = client.get(f"{BASE_V2}/product/Search", params={"q": "rice"})
    else:
        r = client.post(f"{BASE_V2}/product/Search", params={"q": "rice"})
    has_data = r.status_code == 200 and len(r.content) > 0
    print(f"  {method} Search q=rice -> {r.status_code} size={len(r.content)} {'DATA!' if has_data else ''}")
    if has_data:
        data = try_decode(r)
        if data and isinstance(data, list) and len(data) > 0:
            print(f"    Results: {len(data)}")
            print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")

# 7. Systematic v2 endpoint discovery
print("\n" + "=" * 60)
print("7. v2 endpoint discovery")
print("=" * 60)
endpoints = [
    "/product/Products",
    "/product/AllProducts",
    "/product/GetAll",
    "/product/Items",
    "/product/List",
    "/product/Catalog",
    "/product/Details",
    "/product/ByStore",
    "/store/Stores",
    "/store/NearestStores",
    "/city/Cities",
    "/category/Products",
    "/price/All",
    "/price/Items",
    "/offer/Offers",
]

for path in endpoints:
    for method in ["GET", "POST"]:
        try:
            if method == "GET":
                r = client.get(f"{BASE_V2}{path}", timeout=10.0)
            else:
                r = client.post(f"{BASE_V2}{path}", timeout=10.0)
            if r.status_code != 404:
                has_data = r.status_code == 200 and len(r.content) > 0
                print(f"  [{r.status_code}] {method} {path} size={len(r.content)} {'DATA!' if has_data else ''}")
                if has_data:
                    data = try_decode(r)
                    if data:
                        preview = json.dumps(data, ensure_ascii=False)[:300] if not isinstance(data, str) else data[:300]
                        print(f"    -> {preview}")
        except Exception:
            pass

# 8. Try with lat/lng on v2
print("\n" + "=" * 60)
print("8. v2 Products with lat/lng")
print("=" * 60)
combos = [
    {"categoryId": "12", "lat": "24.7136", "lng": "46.6753"},
    {"categoryId": "12", "latitude": "24.7136", "longitude": "46.6753"},
    {"categoryId": "1", "lat": "24.7136", "lng": "46.6753"},
]
for params in combos:
    for method in ["GET", "POST"]:
        if method == "GET":
            r = client.get(f"{BASE_V2}/product/ProductsByCategory", params=params)
        else:
            r = client.post(f"{BASE_V2}/product/ProductsByCategory", params=params)
        has_data = r.status_code == 200 and len(r.content) > 0
        print(f"  {method} {params} -> {r.status_code} size={len(r.content)} {'DATA!' if has_data else ''}")
        if has_data:
            data = try_decode(r)
            if data and isinstance(data, list) and len(data) > 0:
                print(f"    Products: {len(data)}")
                print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")

client.close()
print("\n=== DONE ===")
