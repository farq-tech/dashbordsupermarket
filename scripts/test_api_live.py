#!/usr/bin/env python3
"""Quick API test - self-contained, no external deps except httpx"""
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
    if not s:
        return ""
    s = "".join(s.split())
    length = len(s)
    def gnv(i):
        return _lz_val(s[i])
    d = {0: chr(0), 1: chr(1), 2: chr(2)}
    ei = 4; ds = 4; nb = 3; w = ""; r = []
    dv = gnv(0); dp = 32; di = 1
    # read first entry
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

# ===== Main tests =====
BASE = "https://api.fustog.app/api/v1"
HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16)",
    "Accept": "application/json, */*;q=0.5",
    "Accept-Encoding": "identity",
}

client = httpx.Client(timeout=15.0, headers=HEADERS)

print("=== TEST 1: Categories ===")
r = client.get(f"{BASE}/category/Categories")
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
cats = try_decode(r)
all_sub_ids = []
if cats and isinstance(cats, list):
    print(f"Categories count: {len(cats)}")
    for cat in cats:
        for sub in cat.get("SubItmes", []):
            all_sub_ids.append((sub["CID"], sub.get("TitleEN", "")))
    print(f"Total sub-categories: {len(all_sub_ids)}")

print("\n=== TEST 2: Products - Parent Cat ID=1 ===")
r = client.get(f"{BASE}/product/ProductsByCategory", params={"categoryId": 1})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"Products count: {len(data)}")
    print(f"First item: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty or null. Raw: {r.content[:300]}")

print("\n=== TEST 3: Products - Sub Cat ID=12 (Fresh Fruits) ===")
r = client.get(f"{BASE}/product/ProductsByCategory", params={"categoryId": 12})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"Products count: {len(data)}")
    print(f"First item: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty or null. Raw: {r.content[:300]}")

print("\n=== TEST 4: Products - Sub Cat ID=23 (Rice) ===")
r = client.get(f"{BASE}/product/ProductsByCategory", params={"categoryId": 23})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"Products count: {len(data)}")
    print(f"First item: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty or null. Raw: {r.content[:300]}")

print("\n=== TEST 5: Products - Sub Cat ID=48 (Soft Drinks) ===")
r = client.get(f"{BASE}/product/ProductsByCategory", params={"categoryId": 48})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"Products count: {len(data)}")
    print(f"First item: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty or null. Raw: {r.content[:300]}")

print("\n=== TEST 6: ItemsPrices ===")
r = client.get(f"{BASE}/product/ItemsPrices")
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"Prices count: {len(data)}")
    print(f"First item: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty or null. Raw: {r.content[:300]}")

print("\n=== TEST 7: POST ProductsByCategory ID=12 ===")
r = client.post(f"{BASE}/product/ProductsByCategory", params={"categoryId": 12})
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"Products count: {len(data)}")
    print(f"First item: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty or null. Raw: {r.content[:300]}")

print("\n=== TEST 8: POST ItemsPrices ===")
r = client.post(f"{BASE}/product/ItemsPrices")
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"Prices count: {len(data)}")
    print(f"First item: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty or null. Raw: {r.content[:300]}")

# Test 9: Try with browser-like Origin/Referer headers
print("\n=== TEST 9: Products with Browser headers + Origin ===")
browser_headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "identity",
    "Origin": "https://trends.fustog.app",
    "Referer": "https://trends.fustog.app/",
}
r = httpx.get(f"{BASE}/product/ProductsByCategory", params={"categoryId": 12}, headers=browser_headers, timeout=15.0)
print(f"Status: {r.status_code}, Size: {len(r.content)}, CT: {r.headers.get('content-type')}")
data = try_decode(r)
if data and isinstance(data, list) and len(data) > 0:
    print(f"Products count: {len(data)}")
    print(f"First item: {json.dumps(data[0], ensure_ascii=False)[:500]}")
else:
    print(f"Empty or null. Raw: {r.content[:300]}")

client.close()
print("\n=== ALL TESTS DONE ===")
