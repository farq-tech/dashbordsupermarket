#!/usr/bin/env python3
"""Fetch ALL data from Fustog's own API (aggregates all stores)"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time
from datetime import datetime
import httpx

# LZ-String decompression (Fustog API returns compressed data)
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
    enlarge_in = 4
    dict_size = 4
    num_bits = 3
    entry = ""
    result = []
    data_val = get_next_value(0)
    data_position = reset_value
    data_index = 1
    for i in range(3):
        dictionary[i] = chr(i)
    bits = 0
    maxpower = 2 ** 2
    power = 1
    while power != maxpower:
        resb = data_val & data_position
        data_position >>= 1
        if data_position == 0:
            data_position = reset_value
            data_val = get_next_value(data_index)
            data_index += 1
        bits |= (1 if resb > 0 else 0) * power
        power <<= 1
    next_ = bits
    if next_ == 0:
        bits = 0
        maxpower = 2 ** 8
        power = 1
        while power != maxpower:
            resb = data_val & data_position
            data_position >>= 1
            if data_position == 0:
                data_position = reset_value
                data_val = get_next_value(data_index)
                data_index += 1
            bits |= (1 if resb > 0 else 0) * power
            power <<= 1
        c = chr(bits)
    elif next_ == 1:
        bits = 0
        maxpower = 2 ** 16
        power = 1
        while power != maxpower:
            resb = data_val & data_position
            data_position >>= 1
            if data_position == 0:
                data_position = reset_value
                data_val = get_next_value(data_index)
                data_index += 1
            bits |= (1 if resb > 0 else 0) * power
            power <<= 1
        c = chr(bits)
    elif next_ == 2:
        return ""
    else:
        return ""
    dictionary[3] = c
    w = c
    result.append(c)
    while True:
        if data_index > length:
            return "".join(result)
        bits = 0
        maxpower = 2 ** num_bits
        power = 1
        while power != maxpower:
            resb = data_val & data_position
            data_position >>= 1
            if data_position == 0:
                data_position = reset_value
                if data_index < length:
                    data_val = get_next_value(data_index)
                    data_index += 1
                else:
                    data_val = 0
            bits |= (1 if resb > 0 else 0) * power
            power <<= 1
        cc = bits
        if cc == 0:
            bits = 0
            maxpower = 2 ** 8
            power = 1
            while power != maxpower:
                resb = data_val & data_position
                data_position >>= 1
                if data_position == 0:
                    data_position = reset_value
                    data_val = get_next_value(data_index)
                    data_index += 1
                bits |= (1 if resb > 0 else 0) * power
                power <<= 1
            dictionary[dict_size] = chr(bits)
            cc = dict_size
            dict_size += 1
            enlarge_in -= 1
        elif cc == 1:
            bits = 0
            maxpower = 2 ** 16
            power = 1
            while power != maxpower:
                resb = data_val & data_position
                data_position >>= 1
                if data_position == 0:
                    data_position = reset_value
                    data_val = get_next_value(data_index)
                    data_index += 1
                bits |= (1 if resb > 0 else 0) * power
                power <<= 1
            dictionary[dict_size] = chr(bits)
            cc = dict_size
            dict_size += 1
            enlarge_in -= 1
        elif cc == 2:
            return "".join(result)
        if enlarge_in == 0:
            enlarge_in = 2 ** num_bits
            num_bits += 1
        if cc in dictionary:
            entry = dictionary[cc]
        elif cc == dict_size:
            entry = w + w[0]
        else:
            return ""
        result.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        enlarge_in -= 1
        w = entry
        if enlarge_in == 0:
            enlarge_in = 2 ** num_bits
            num_bits += 1

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

BASE = "https://api.fustog.app/api/v1"
client = httpx.Client(timeout=30.0, follow_redirects=True)
h = {
    "Accept": "application/json, */*;q=0.5",
    "Accept-Encoding": "identity",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 16)",
}

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def api_get(endpoint, params=None, method="GET"):
    """Make API call, handle LZ-compressed responses"""
    url = f"{BASE}{endpoint}"
    if method == "POST":
        r = client.post(url, params=params, headers=h, timeout=30)
    else:
        r = client.get(url, params=params, headers=h, timeout=30)

    if r.status_code != 200:
        return None

    if len(r.content) == 0:
        return []

    ct = (r.headers.get("content-type") or "").lower()
    try:
        return r.json()
    except:
        # Try LZ-String decompression
        text = r.text or ""
        if text:
            try:
                decompressed = lz_decompress_from_base64(text)
                return json.loads(decompressed)
            except:
                print(f"  [WARN] Could not parse response from {endpoint}: ct={ct}, size={len(r.content)}")
                return None
        return None

# ============================================================
# 1. Get Categories
# ============================================================
print("=" * 60)
print("FUSTOG API - Fetching ALL data")
print("=" * 60)

print("\n1. Fetching categories...")
categories = None
for method in ["GET", "POST"]:
    categories = api_get("/category/Categories", method=method)
    if categories:
        break

if not categories:
    print("  ERROR: Could not fetch categories")
    sys.exit(1)

print(f"  Got {len(categories)} categories")
if categories and isinstance(categories[0], dict):
    print(f"  Keys: {list(categories[0].keys())}")
    print(f"  Sample: {json.dumps(categories[0], ensure_ascii=False)[:300]}")
save(f"fustog_categories_{ts}.json", categories)

# ============================================================
# 2. Get Products by Category
# ============================================================
print("\n2. Fetching products by category...")
all_products = []
seen_ids = set()

for i, cat in enumerate(categories):
    cat_id = cat.get("id") or cat.get("CID") or cat.get("categoryId") or cat.get("Id")
    cat_name = cat.get("name") or cat.get("Name") or cat.get("categoryName") or ""
    if not cat_id:
        continue

    products = None
    for method in ["GET", "POST"]:
        products = api_get("/product/ProductsByCategory", params={"categoryId": cat_id}, method=method)
        if products:
            break

    if products and isinstance(products, list):
        new_count = 0
        for p in products:
            pid = p.get("id") or p.get("Id") or p.get("productId") or id(p)
            if pid not in seen_ids:
                seen_ids.add(pid)
                all_products.append(p)
                new_count += 1
        if new_count > 0 or i < 3:
            print(f"  Cat {cat_id} ({cat_name[:30]}): +{new_count} new (total: {len(all_products)})")
    elif i < 5:
        print(f"  Cat {cat_id} ({cat_name[:30]}): no products")

    if i > 0 and i % 20 == 0:
        print(f"  ... processed {i}/{len(categories)} categories, {len(all_products)} products so far")

    time.sleep(0.2)  # Be gentle

print(f"\n  TOTAL PRODUCTS: {len(all_products)}")
if all_products:
    if isinstance(all_products[0], dict):
        print(f"  Product keys: {list(all_products[0].keys())}")
        print(f"  Sample: {json.dumps(all_products[0], ensure_ascii=False)[:500]}")
    save(f"fustog_products_{ts}.json", all_products)

# ============================================================
# 3. Get Item Prices (all stores)
# ============================================================
print("\n3. Fetching item prices...")
prices = None
for method in ["GET", "POST"]:
    prices = api_get("/product/ItemsPrices", method=method)
    if prices:
        break

if prices and isinstance(prices, list):
    print(f"  Got {len(prices)} price entries")
    if prices and isinstance(prices[0], dict):
        print(f"  Price keys: {list(prices[0].keys())}")
        print(f"  Sample: {json.dumps(prices[0], ensure_ascii=False)[:500]}")
    save(f"fustog_prices_{ts}.json", prices)
else:
    print("  No prices data returned")
    prices = []

# ============================================================
# 4. Try other endpoints
# ============================================================
print("\n4. Checking other endpoints...")

other_endpoints = [
    "/retailer/Settings",
    "/retailer/Retailers",
    "/store/Stores",
    "/store/StoresByRetailer",
]

for ep in other_endpoints:
    for method in ["GET", "POST"]:
        result = api_get(ep, method=method)
        if result:
            count = len(result) if isinstance(result, list) else "dict"
            print(f"  [{method}] {ep}: {count}")
            if isinstance(result, list) and result and isinstance(result[0], dict):
                print(f"    Keys: {list(result[0].keys())[:12]}")
                print(f"    Sample: {json.dumps(result[0], ensure_ascii=False)[:300]}")
            elif isinstance(result, dict):
                print(f"    Keys: {list(result.keys())[:12]}")
            save(f"fustog_{ep.strip('/').replace('/', '_').lower()}_{ts}.json", result)
            break

# ============================================================
# 5. Merge and export
# ============================================================
print("\n" + "=" * 60)
print("EXPORTING")
print("=" * 60)

if all_products:
    # Export products CSV
    if isinstance(all_products[0], dict):
        fieldnames = list(all_products[0].keys())
        with open(f"data/fustog_all_products_{ts}.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(all_products)
        print(f"  Products CSV: data/fustog_all_products_{ts}.csv ({len(all_products)} rows)")

if prices:
    # Export prices CSV
    if isinstance(prices[0], dict):
        fieldnames = list(prices[0].keys())
        with open(f"data/fustog_all_prices_{ts}.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(prices)
        print(f"  Prices CSV: data/fustog_all_prices_{ts}.csv ({len(prices)} rows)")

    # Merge products with prices
    if all_products and prices:
        # Build product lookup
        product_map = {}
        for p in all_products:
            pid = p.get("id") or p.get("Id") or p.get("productId")
            if pid:
                product_map[pid] = p

        merged = []
        for price in prices:
            pid = price.get("productId") or price.get("ProductId") or price.get("productid")
            sid = price.get("storeId") or price.get("StoreId") or price.get("storeid")
            p = product_map.get(pid, {})

            row = {
                "product_id": pid,
                "product_name": p.get("name") or p.get("Name") or "",
                "category_id": p.get("categoryId") or p.get("CategoryId") or "",
                "store_id": sid,
                "price": price.get("price") or price.get("Price") or "",
                "sale_price": price.get("salePrice") or price.get("discountPrice") or "",
                "store_name": price.get("storeName") or price.get("StoreName") or "",
                "retailer_id": price.get("retailerId") or price.get("RetailerId") or "",
            }
            merged.append(row)

        if merged:
            fieldnames = list(merged[0].keys())
            with open(f"data/fustog_merged_{ts}.csv", "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                w.writerows(merged)
            print(f"  Merged CSV: data/fustog_merged_{ts}.csv ({len(merged)} rows)")

            # Count by store
            store_counts = {}
            for row in merged:
                sn = row.get("store_name") or row.get("store_id") or "unknown"
                store_counts[sn] = store_counts.get(sn, 0) + 1

            print(f"\n  Products per store:")
            for store, count in sorted(store_counts.items(), key=lambda x: -x[1]):
                print(f"    {store}: {count}")

client.close()
print("\n=== DONE ===")
