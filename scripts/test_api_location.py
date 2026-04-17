#!/usr/bin/env python3
"""Test with user location params and various content types"""
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

BASE = "https://api.fustog.app/api/v1"

# Riyadh coordinates
LAT = "24.7136"
LNG = "46.6753"

client = httpx.Client(timeout=20.0, headers={
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16)",
    "Accept": "application/json, */*;q=0.5",
    "Accept-Encoding": "identity",
})

print("=" * 60)
print("Testing with lat/lng in query params")
print("=" * 60)

# Various combinations with lat/lng
combos = [
    # Products with lat/lng
    {"categoryId": "12", "lat": LAT, "lng": LNG},
    {"categoryId": "12", "latitude": LAT, "longitude": LNG},
    {"categoryId": "12", "Lat": LAT, "Lng": LNG},
    {"categoryId": "12", "Latitude": LAT, "Longitude": LNG},
    {"categoryId": "12", "lat": LAT, "lng": LNG, "cityId": "1"},
    {"categoryId": "12", "lat": LAT, "lng": LNG, "city": "Riyadh"},
    {"categoryId": "12", "lat": LAT, "lng": LNG, "storeId": "1"},
    # With different category IDs
    {"categoryId": "1", "lat": LAT, "lng": LNG},
    {"categoryId": "23", "lat": LAT, "lng": LNG},
    {"categoryId": "48", "lat": LAT, "lng": LNG},
]

for params in combos:
    r = client.post(f"{BASE}/product/ProductsByCategory", params=params)
    has_data = r.status_code == 200 and len(r.content) > 0
    print(f"  {params} -> {r.status_code} size={len(r.content)} {'DATA!' if has_data else ''}")
    if has_data:
        data = try_decode(r)
        if data and isinstance(data, list) and len(data) > 0:
            print(f"    Products: {len(data)}")
            print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")

# Prices with lat/lng
print("\n" + "=" * 60)
print("Testing ItemsPrices with lat/lng")
print("=" * 60)

price_combos = [
    {"lat": LAT, "lng": LNG},
    {"latitude": LAT, "longitude": LNG},
    {"lat": LAT, "lng": LNG, "cityId": "1"},
    {"lat": LAT, "lng": LNG, "storeId": "1"},
]

for params in price_combos:
    r = client.post(f"{BASE}/product/ItemsPrices", params=params)
    has_data = r.status_code == 200 and len(r.content) > 0
    print(f"  {params} -> {r.status_code} size={len(r.content)} {'DATA!' if has_data else ''}")
    if has_data:
        data = try_decode(r)
        if data and isinstance(data, list) and len(data) > 0:
            print(f"    Prices: {len(data)}")
            print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")

# Try with form-encoded content type
print("\n" + "=" * 60)
print("Testing with form-encoded body")
print("=" * 60)

form_combos = [
    {"categoryId": "12"},
    {"categoryId": "12", "lat": LAT, "lng": LNG},
    {"categoryId": "12", "latitude": LAT, "longitude": LNG},
    {"categoryId": "12", "lat": LAT, "lng": LNG, "cityId": "1"},
]

for form_data in form_combos:
    r = client.post(f"{BASE}/product/ProductsByCategory", data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    has_data = r.status_code == 200 and len(r.content) > 0
    print(f"  form={form_data} -> {r.status_code} size={len(r.content)} {'DATA!' if has_data else ''}")
    if has_data:
        data = try_decode(r)
        if data and isinstance(data, list) and len(data) > 0:
            print(f"    Products: {len(data)}")

# Try trends.fustog.app
print("\n" + "=" * 60)
print("Testing trends.fustog.app")
print("=" * 60)

TRENDS = "https://trends.fustog.app"
trends_paths = [
    ("GET", "/api/v1/category/Categories"),
    ("GET", "/api/v1/product/ProductsByCategory?categoryId=12"),
    ("POST", "/api/v1/product/ProductsByCategory?categoryId=12"),
    ("GET", "/api/products"),
    ("GET", "/api/categories"),
    ("GET", "/"),
]

for method, path in trends_paths:
    try:
        url = f"{TRENDS}{path}"
        if method == "GET":
            r = client.get(url, timeout=10.0)
        else:
            r = client.post(url, timeout=10.0)
        print(f"  [{r.status_code}] {method} {url[:80]} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 2 and len(r.content) < 5000:
            data = try_decode(r)
            if data:
                preview = json.dumps(data, ensure_ascii=False)[:300] if not isinstance(data, str) else data[:300]
                print(f"    -> {preview}")
    except Exception as e:
        print(f"  [ERR] {method} {path} -> {e}")

# Try without /api/v1 prefix
print("\n" + "=" * 60)
print("Testing api.fustog.app without /api/v1 prefix")
print("=" * 60)

no_prefix_paths = [
    ("GET", "/category/Categories"),
    ("GET", "/product/ProductsByCategory?categoryId=12"),
    ("POST", "/product/ProductsByCategory?categoryId=12"),
    ("GET", "/api/category/Categories"),
    ("GET", "/api/v2/category/Categories"),
    ("GET", "/v1/category/Categories"),
    ("GET", "/v2/category/Categories"),
]

for method, path in no_prefix_paths:
    try:
        url = f"https://api.fustog.app{path}"
        if method == "GET":
            r = client.get(url, timeout=10.0)
        else:
            r = client.post(url, timeout=10.0)
        print(f"  [{r.status_code}] {method} {path} size={len(r.content)}")
    except Exception as e:
        print(f"  [ERR] {method} {path} -> {e}")

client.close()
print("\n=== DONE ===")
