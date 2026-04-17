#!/usr/bin/env python3
"""Test POST requests with various body formats"""
import json
import httpx

# ===== Inline LZ-String decompressor =====
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
HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16)",
    "Accept": "application/json, */*;q=0.5",
    "Accept-Encoding": "identity",
}

client = httpx.Client(timeout=20.0, headers=HEADERS)

# ============ Products by Category ============
print("=" * 60)
print("TESTING ProductsByCategory endpoint (POST)")
print("=" * 60)

# Test A: POST with JSON body {categoryId: 12}
print("\n--- A: POST JSON body {categoryId: 12} ---")
r = client.post(f"{BASE}/product/ProductsByCategory",
    json={"categoryId": 12})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Products: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# Test B: POST with JSON body {CategoryId: 12} (capital C)
print("\n--- B: POST JSON body {CategoryId: 12} ---")
r = client.post(f"{BASE}/product/ProductsByCategory",
    json={"CategoryId": 12})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Products: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# Test C: POST with JSON body {CID: 12}
print("\n--- C: POST JSON body {CID: 12} ---")
r = client.post(f"{BASE}/product/ProductsByCategory",
    json={"CID": 12})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Products: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# Test D: POST with query params only
print("\n--- D: POST query params ?categoryId=12 ---")
r = client.post(f"{BASE}/product/ProductsByCategory?categoryId=12")
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Products: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# Test E: POST with form data
print("\n--- E: POST form data categoryId=12 ---")
r = client.post(f"{BASE}/product/ProductsByCategory",
    data={"categoryId": "12"})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Products: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# Test F: POST with JSON + location
print("\n--- F: POST JSON {categoryId:12, latitude:24.7, longitude:46.6} ---")
r = client.post(f"{BASE}/product/ProductsByCategory",
    json={"categoryId": 12, "latitude": 24.7136, "longitude": 46.6753, "cityId": 1})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Products: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# Test G: POST with parent category ID=1 + JSON
print("\n--- G: POST JSON {categoryId:1} (parent) ---")
r = client.post(f"{BASE}/product/ProductsByCategory",
    json={"categoryId": 1})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Products: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# Test H: POST with content-type explicitly set
print("\n--- H: POST explicit Content-Type: application/json ---")
r = client.post(f"{BASE}/product/ProductsByCategory",
    content=json.dumps({"categoryId": 12}).encode(),
    headers={"Content-Type": "application/json"})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Products: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# ============ ItemsPrices ============
print("\n" + "=" * 60)
print("TESTING ItemsPrices endpoint (POST)")
print("=" * 60)

# Test I: POST empty JSON
print("\n--- I: POST JSON {} ---")
r = client.post(f"{BASE}/product/ItemsPrices", json={})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Prices: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# Test J: POST with location
print("\n--- J: POST JSON with location ---")
r = client.post(f"{BASE}/product/ItemsPrices",
    json={"latitude": 24.7136, "longitude": 46.6753, "cityId": 1})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Prices: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# Test K: POST with Content-Type explicit
print("\n--- K: POST explicit Content-Type ---")
r = client.post(f"{BASE}/product/ItemsPrices",
    content=b"{}",
    headers={"Content-Type": "application/json"})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"SUCCESS! Prices: {len(data)}")
    print(f"Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty. Raw: {r.content[:300]}")

# ============ Try other endpoint patterns ============
print("\n" + "=" * 60)
print("TESTING alternative endpoint paths")
print("=" * 60)

alt_endpoints = [
    ("GET", "/product/Products"),
    ("POST", "/product/Products"),
    ("GET", "/product/AllProducts"),
    ("POST", "/product/AllProducts"),
    ("GET", "/product/Search"),
    ("POST", "/product/Search", {"query": ""}),
    ("GET", "/product/GetAll"),
    ("POST", "/product/GetAll"),
    ("GET", "/store/Stores"),
    ("POST", "/store/Stores"),
    ("GET", "/city/Cities"),
    ("POST", "/city/Cities"),
    ("GET", "/retailer/Settings"),
    ("POST", "/retailer/Settings"),
]

for item in alt_endpoints:
    method = item[0]
    path = item[1]
    body = item[2] if len(item) > 2 else None
    try:
        if method == "GET":
            r = client.get(f"{BASE}{path}", timeout=10.0)
        else:
            r = client.post(f"{BASE}{path}", json=body, timeout=10.0)
        status_icon = "OK" if r.status_code == 200 and len(r.content) > 0 else "EMPTY" if r.status_code == 200 else str(r.status_code)
        print(f"[{status_icon}] {method} {path} -> Status:{r.status_code} Size:{len(r.content)}")
        if r.status_code == 200 and len(r.content) > 2:
            data = try_decode(r)
            if data:
                if isinstance(data, list):
                    print(f"       List of {len(data)} items. First: {json.dumps(data[0], ensure_ascii=False)[:200] if data else 'empty'}")
                elif isinstance(data, dict):
                    print(f"       Dict keys: {list(data.keys())[:10]}")
    except Exception as e:
        print(f"[ERR] {method} {path} -> {e}")

client.close()
print("\n=== ALL TESTS DONE ===")
