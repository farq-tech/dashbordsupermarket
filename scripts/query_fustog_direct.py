#!/usr/bin/env python3
"""Query Fustog API directly for products and prices"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os
import httpx

os.makedirs("data", exist_ok=True)

# LZ-String decompression
_LZ_KEYSTR_BASE64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
_LZ_BASE_REVERSE_DICTIONARY = {}

def _lz_get_base_value(alphabet, character):
    if alphabet not in _LZ_BASE_REVERSE_DICTIONARY:
        _LZ_BASE_REVERSE_DICTIONARY[alphabet] = {c: i for i, c in enumerate(alphabet)}
    return _LZ_BASE_REVERSE_DICTIONARY[alphabet][character]

def lz_decompress_from_base64(input_str):
    if not input_str:
        return ""
    input_str = "".join(input_str.split())
    def get_next_value(index):
        return _lz_get_base_value(_LZ_KEYSTR_BASE64, input_str[index])
    return _lz_decompress(len(input_str), 32, get_next_value)

def _lz_decompress(length, reset_value, get_next_value):
    dictionary = {}
    enlarge_in = 4; dict_size = 4; num_bits = 3
    entry = ""; result = []
    data_val = get_next_value(0); data_position = reset_value; data_index = 1
    for i in range(3): dictionary[i] = chr(i)
    bits = 0; maxpower = 4; power = 1
    while power != maxpower:
        resb = data_val & data_position; data_position >>= 1
        if data_position == 0: data_position = reset_value; data_val = get_next_value(data_index); data_index += 1
        bits |= (1 if resb > 0 else 0) * power; power <<= 1
    next_ = bits
    if next_ == 0:
        bits = 0; maxpower = 256; power = 1
        while power != maxpower:
            resb = data_val & data_position; data_position >>= 1
            if data_position == 0: data_position = reset_value; data_val = get_next_value(data_index); data_index += 1
            bits |= (1 if resb > 0 else 0) * power; power <<= 1
        c = chr(bits)
    elif next_ == 1:
        bits = 0; maxpower = 65536; power = 1
        while power != maxpower:
            resb = data_val & data_position; data_position >>= 1
            if data_position == 0: data_position = reset_value; data_val = get_next_value(data_index); data_index += 1
            bits |= (1 if resb > 0 else 0) * power; power <<= 1
        c = chr(bits)
    elif next_ == 2: return ""
    else: return ""
    dictionary[3] = c; w = c; result.append(c)
    while True:
        if data_index > length: return "".join(result)
        bits = 0; maxpower = 2 ** num_bits; power = 1
        while power != maxpower:
            resb = data_val & data_position; data_position >>= 1
            if data_position == 0:
                data_position = reset_value
                if data_index < length: data_val = get_next_value(data_index); data_index += 1
                else: data_val = 0
            bits |= (1 if resb > 0 else 0) * power; power <<= 1
        cc = bits
        if cc == 0:
            bits = 0; maxpower = 256; power = 1
            while power != maxpower:
                resb = data_val & data_position; data_position >>= 1
                if data_position == 0: data_position = reset_value; data_val = get_next_value(data_index); data_index += 1
                bits |= (1 if resb > 0 else 0) * power; power <<= 1
            dictionary[dict_size] = chr(bits); cc = dict_size; dict_size += 1; enlarge_in -= 1
        elif cc == 1:
            bits = 0; maxpower = 65536; power = 1
            while power != maxpower:
                resb = data_val & data_position; data_position >>= 1
                if data_position == 0: data_position = reset_value; data_val = get_next_value(data_index); data_index += 1
                bits |= (1 if resb > 0 else 0) * power; power <<= 1
            dictionary[dict_size] = chr(bits); cc = dict_size; dict_size += 1; enlarge_in -= 1
        elif cc == 2: return "".join(result)
        if enlarge_in == 0: enlarge_in = 2 ** num_bits; num_bits += 1
        if cc in dictionary: entry = dictionary[cc]
        elif cc == dict_size: entry = w + w[0]
        else: return ""
        result.append(entry)
        dictionary[dict_size] = w + entry[0]; dict_size += 1; enlarge_in -= 1; w = entry
        if enlarge_in == 0: enlarge_in = 2 ** num_bits; num_bits += 1

def fetch_fustog(endpoint, method="GET", params=None):
    BASE = "https://api.fustog.app/api/v1"
    h = {
        "Accept": "application/json, */*;q=0.5",
        "Accept-Encoding": "identity",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16)",
    }
    url = f"{BASE}{endpoint}"
    client = httpx.Client(timeout=30.0)
    try:
        if method == "GET":
            r = client.get(url, headers=h, params=params)
        else:
            r = client.post(url, headers=h, params=params)

        if r.status_code == 200 and len(r.content) > 0:
            try:
                return r.json()
            except:
                text = r.text
                if text:
                    decompressed = lz_decompress_from_base64(text)
                    return json.loads(decompressed)
        return None
    finally:
        client.close()

# ============================================================
# 1. Get ALL categories
# ============================================================
print("=" * 60)
print("FUSTOG API - Direct Query")
print("=" * 60)

print("\n1. Categories:")
cats = fetch_fustog("/category/Categories")
if isinstance(cats, list):
    print(f"   Got {len(cats)} categories")
    with open("data/fustog_categories_full.json", "w", encoding="utf-8") as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)
    for c in cats:
        cid = c.get("CID", c.get("id", ""))
        name = c.get("Name", c.get("name", ""))
        name_ar = c.get("NameAr", c.get("nameAr", ""))
        subs = c.get("SubCategories", c.get("subCategories", []))
        print(f"   CID={cid}: {name_ar or name}")
        if isinstance(subs, list):
            for s in subs:
                sid = s.get("CID", s.get("id", ""))
                sname = s.get("Name", s.get("name", ""))
                sname_ar = s.get("NameAr", s.get("nameAr", ""))
                print(f"      Sub CID={sid}: {sname_ar or sname}")
else:
    print(f"   Failed: {cats}")

# ============================================================
# 2. Products by each category (POST with query param)
# ============================================================
print("\n2. Products by category:")
all_products = []
if isinstance(cats, list):
    for c in cats:
        cid = c.get("CID", c.get("id"))
        cname = c.get("NameAr", c.get("Name", ""))
        if not cid:
            continue

        prods = fetch_fustog("/product/ProductsByCategory", method="POST", params={"categoryId": cid})
        if isinstance(prods, list) and prods:
            print(f"   Cat {cid} ({cname}): {len(prods)} products!")
            if prods[0] and isinstance(prods[0], dict):
                print(f"      Keys: {list(prods[0].keys())[:15]}")
                print(f"      Sample: {json.dumps(prods[0], ensure_ascii=False)[:300]}")
            all_products.extend(prods)
        elif prods is None:
            print(f"   Cat {cid} ({cname}): empty")
        else:
            print(f"   Cat {cid} ({cname}): {type(prods)}")

        # Also try subcategories
        subs = c.get("SubCategories", c.get("subCategories", []))
        if isinstance(subs, list):
            for s in subs:
                sid = s.get("CID", s.get("id"))
                sname = s.get("NameAr", s.get("Name", ""))
                if not sid:
                    continue
                sprods = fetch_fustog("/product/ProductsByCategory", method="POST", params={"categoryId": sid})
                if isinstance(sprods, list) and sprods:
                    print(f"      Sub {sid} ({sname}): {len(sprods)} products!")
                    all_products.extend(sprods)

print(f"\n   TOTAL: {len(all_products)} products from Fustog API")
if all_products:
    with open("data/fustog_all_products.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

# ============================================================
# 3. Item Prices
# ============================================================
print("\n3. Item Prices:")
prices = fetch_fustog("/product/ItemsPrices", method="POST")
if isinstance(prices, list) and prices:
    print(f"   Got {len(prices)} price entries!")
    if isinstance(prices[0], dict):
        print(f"   Keys: {list(prices[0].keys())[:15]}")
        print(f"   Sample: {json.dumps(prices[0], ensure_ascii=False)[:300]}")
    with open("data/fustog_all_prices.json", "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
else:
    print(f"   No prices: {prices}")

# ============================================================
# 4. Retailer Settings
# ============================================================
print("\n4. Retailer Settings:")
settings = fetch_fustog("/retailer/Settings")
if isinstance(settings, dict):
    print(f"   Stores: {list(settings.keys())}")
    with open("data/fustog_retailer_settings.json", "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

print("\n=== DONE ===")
