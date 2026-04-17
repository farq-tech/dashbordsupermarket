#!/usr/bin/env python3
"""Deep API investigation - retailer settings, search, and product variants"""
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

# 1. Get retailer settings (full details)
print("=" * 60)
print("1. RETAILER SETTINGS (full)")
print("=" * 60)
r = client.get(f"{BASE}/retailer/Settings")
settings = try_decode(r)
if settings:
    print(json.dumps(settings, ensure_ascii=False, indent=2)[:3000])

# 2. Try POST ProductsByCategory with various query param combos
print("\n" + "=" * 60)
print("2. POST ProductsByCategory with various params")
print("=" * 60)

combos = [
    {"categoryId": "12"},
    {"categoryId": "12", "page": "1", "limit": "20"},
    {"categoryId": "12", "page": "1", "pageSize": "20"},
    {"categoryId": "12", "storeId": "1"},
    {"categoryId": "12", "cityId": "1"},
    {"categoryId": "12", "branchId": "1"},
    {"categoryId": "1", "page": "1"},
    {"CID": "12"},
    {"id": "12"},
]

for params in combos:
    r = client.post(f"{BASE}/product/ProductsByCategory", params=params)
    has_data = r.status_code == 200 and len(r.content) > 0
    print(f"  params={params} -> {r.status_code} size={len(r.content)} {'DATA!' if has_data else ''}")
    if has_data:
        data = try_decode(r)
        if data and isinstance(data, list) and len(data) > 0:
            print(f"    Products: {len(data)}")
            print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")

# 3. Try POST Search with various bodies
print("\n" + "=" * 60)
print("3. POST /product/Search with various bodies")
print("=" * 60)

search_bodies = [
    {"query": "rice"},
    {"keyword": "rice"},
    {"search": "rice"},
    {"q": "rice"},
    {"term": "rice"},
    {"text": "rice"},
    {"name": "rice"},
    {"Query": "rice"},
    {"SearchQuery": "rice"},
]

for body in search_bodies:
    try:
        r = client.post(f"{BASE}/product/Search", json=body)
        has_data = r.status_code == 200 and len(r.content) > 0
        print(f"  body={body} -> {r.status_code} size={len(r.content)} {'DATA!' if has_data else ''}")
        if has_data:
            data = try_decode(r)
            if data:
                if isinstance(data, list) and len(data) > 0:
                    print(f"    Results: {len(data)}")
                    print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")
                elif isinstance(data, dict):
                    print(f"    Dict: {json.dumps(data, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"  body={body} -> ERROR: {e}")

# 4. Try POST Search with query params instead
print("\n--- Search with query params ---")
for key in ["query", "q", "keyword", "search", "text"]:
    r = client.post(f"{BASE}/product/Search", params={key: "rice"})
    has_data = r.status_code == 200 and len(r.content) > 0
    print(f"  ?{key}=rice -> {r.status_code} size={len(r.content)} {'DATA!' if has_data else ''}")
    if has_data:
        data = try_decode(r)
        if data and isinstance(data, list) and len(data) > 0:
            print(f"    Results: {len(data)}")
            print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:500]}")

# 5. Explore more API paths
print("\n" + "=" * 60)
print("5. Exploring more API paths")
print("=" * 60)

paths_to_try = [
    ("GET", "/product/Items"),
    ("POST", "/product/Items"),
    ("GET", "/product/List"),
    ("POST", "/product/List"),
    ("GET", "/product/Catalog"),
    ("POST", "/product/Catalog"),
    ("GET", "/category/Products"),
    ("POST", "/category/Products"),
    ("GET", "/items"),
    ("POST", "/items"),
    ("GET", "/products"),
    ("POST", "/products"),
    ("GET", "/catalog"),
    ("POST", "/catalog"),
    ("GET", "/price/All"),
    ("POST", "/price/All"),
    ("GET", "/price/Items"),
    ("POST", "/price/Items"),
    ("GET", "/offer/Offers"),
    ("POST", "/offer/Offers"),
    ("GET", "/store/Products"),
    ("POST", "/store/Products"),
    ("GET", "/product/Details"),
    ("POST", "/product/Details"),
    ("GET", "/product/ByStore"),
    ("POST", "/product/ByStore"),
]

for method, path in paths_to_try:
    try:
        if method == "GET":
            r = client.get(f"{BASE}{path}", timeout=10.0)
        else:
            r = client.post(f"{BASE}{path}", timeout=10.0)
        if r.status_code not in (404,):
            has_data = r.status_code == 200 and len(r.content) > 0
            print(f"  [{r.status_code}] {method} {path} size={len(r.content)} {'DATA!' if has_data else ''}")
            if has_data:
                data = try_decode(r)
                if data:
                    preview = json.dumps(data, ensure_ascii=False)[:300]
                    print(f"    -> {preview}")
    except Exception as e:
        pass

# 6. Check if devapi has different behavior
print("\n" + "=" * 60)
print("6. Testing devapi.fustog.app")
print("=" * 60)
DEV_BASE = "https://devapi.fustog.app/api/v1"
dev_tests = [
    ("GET", "/category/Categories"),
    ("GET", "/product/ProductsByCategory?categoryId=12"),
    ("POST", "/product/ProductsByCategory?categoryId=12"),
    ("GET", "/product/ItemsPrices"),
    ("POST", "/product/ItemsPrices"),
    ("GET", "/retailer/Settings"),
]
for method, path in dev_tests:
    try:
        url = f"{DEV_BASE}{path}"
        if method == "GET":
            r = client.get(url, timeout=10.0)
        else:
            r = client.post(url, timeout=10.0)
        print(f"  [{r.status_code}] {method} {path} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 0:
            data = try_decode(r)
            if data:
                if isinstance(data, list):
                    print(f"    List of {len(data)} items")
                    if len(data) > 0:
                        print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:300]}")
                elif isinstance(data, dict):
                    print(f"    Keys: {list(data.keys())[:10]}")
    except Exception as e:
        print(f"  [ERR] {method} {path} -> {e}")

client.close()
print("\n=== DONE ===")
