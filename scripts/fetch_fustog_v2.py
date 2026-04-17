#!/usr/bin/env python3
"""Fetch ALL data from Fustog API using subcategory IDs"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time
from datetime import datetime
import httpx

# Copy LZ decompression from the main script
_LZ_KEYSTR_BASE64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
_LZ_BASE_REVERSE_DICTIONARY = {}
def _lz_get_base_value(a, c):
    if a not in _LZ_BASE_REVERSE_DICTIONARY:
        _LZ_BASE_REVERSE_DICTIONARY[a] = {ch: i for i, ch in enumerate(a)}
    return _LZ_BASE_REVERSE_DICTIONARY[a][c]
def lz_decompress_from_base64(s):
    if not s: return ""
    s = "".join(s.split())
    def gnv(i): return _lz_get_base_value(_LZ_KEYSTR_BASE64, s[i])
    return _lz_decompress(len(s), 32, gnv)
def _lz_decompress(length, rv, gnv):
    d={}; ei=4; ds=4; nb=3; e=""; r=[]
    dv=gnv(0); dp=rv; di=1
    for i in range(3): d[i]=chr(i)
    b=0; mp=4; pw=1
    while pw!=mp:
        rb=dv&dp; dp>>=1
        if dp==0: dp=rv; dv=gnv(di); di+=1
        b|=(1 if rb>0 else 0)*pw; pw<<=1
    n=b
    if n==0:
        b=0;mp=256;pw=1
        while pw!=mp:
            rb=dv&dp;dp>>=1
            if dp==0:dp=rv;dv=gnv(di);di+=1
            b|=(1 if rb>0 else 0)*pw;pw<<=1
        c=chr(b)
    elif n==1:
        b=0;mp=65536;pw=1
        while pw!=mp:
            rb=dv&dp;dp>>=1
            if dp==0:dp=rv;dv=gnv(di);di+=1
            b|=(1 if rb>0 else 0)*pw;pw<<=1
        c=chr(b)
    elif n==2: return ""
    else: return ""
    d[3]=c;w=c;r.append(c)
    while True:
        if di>length: return "".join(r)
        b=0;mp=2**nb;pw=1
        while pw!=mp:
            rb=dv&dp;dp>>=1
            if dp==0:
                dp=rv
                if di<length:dv=gnv(di);di+=1
                else:dv=0
            b|=(1 if rb>0 else 0)*pw;pw<<=1
        cc=b
        if cc==0:
            b=0;mp=256;pw=1
            while pw!=mp:
                rb=dv&dp;dp>>=1
                if dp==0:dp=rv;dv=gnv(di);di+=1
                b|=(1 if rb>0 else 0)*pw;pw<<=1
            d[ds]=chr(b);cc=ds;ds+=1;ei-=1
        elif cc==1:
            b=0;mp=65536;pw=1
            while pw!=mp:
                rb=dv&dp;dp>>=1
                if dp==0:dp=rv;dv=gnv(di);di+=1
                b|=(1 if rb>0 else 0)*pw;pw<<=1
            d[ds]=chr(b);cc=ds;ds+=1;ei-=1
        elif cc==2: return "".join(r)
        if ei==0:ei=2**nb;nb+=1
        if cc in d:e=d[cc]
        elif cc==ds:e=w+w[0]
        else:return ""
        r.append(e);d[ds]=w+e[0];ds+=1;ei-=1;w=e
        if ei==0:ei=2**nb;nb+=1

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

def api_call(endpoint, params=None, method="GET"):
    url = f"{BASE}{endpoint}"
    try:
        if method == "POST":
            r = client.post(url, params=params, headers=h, timeout=30)
        else:
            r = client.get(url, params=params, headers=h, timeout=30)
        if r.status_code != 200:
            return None
        if len(r.content) == 0:
            return []
        try:
            return r.json()
        except:
            text = r.text or ""
            if text:
                try:
                    return json.loads(lz_decompress_from_base64(text))
                except:
                    return None
            return None
    except:
        return None

# ============================================================
# 1. Get categories (already have them)
# ============================================================
print("=" * 60)
print("FUSTOG API - Full Product Extraction")
print("=" * 60)

categories = api_call("/category/Categories")
if not categories:
    print("ERROR: Could not fetch categories")
    sys.exit(1)

# Collect ALL subcategory IDs
all_cat_ids = []
for cat in categories:
    all_cat_ids.append({"id": cat["CID"], "name": cat.get("TitleEN", ""), "parent": ""})
    for sub in cat.get("SubItmes", []):
        all_cat_ids.append({"id": sub["CID"], "name": sub.get("TitleEN", ""), "parent": cat.get("TitleEN", "")})

print(f"  Total category IDs to query: {len(all_cat_ids)}")

# ============================================================
# 2. Fetch products for ALL subcategory IDs
# ============================================================
print("\n  Fetching products by subcategory...")
all_products = []
seen_ids = set()

for cat in all_cat_ids:
    cid = cat["id"]
    cname = cat["name"]

    # Try both GET and POST
    products = api_call("/product/ProductsByCategory", params={"categoryId": cid}, method="GET")
    if not products:
        products = api_call("/product/ProductsByCategory", params={"categoryId": cid}, method="POST")

    if products and isinstance(products, list):
        new_count = 0
        for p in products:
            pid = p.get("Id") or p.get("id") or p.get("productId") or p.get("PID")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                p["_category_id"] = cid
                p["_category_name"] = cname
                p["_parent_category"] = cat["parent"]
                all_products.append(p)
                new_count += 1
        if new_count > 0:
            print(f"    Cat {cid:3d} ({cname[:25]:25s}): +{new_count:4d} (total: {len(all_products)})")
    time.sleep(0.15)

print(f"\n  TOTAL UNIQUE PRODUCTS: {len(all_products)}")

if all_products:
    print(f"  Product keys: {list(all_products[0].keys())[:15]}")
    print(f"  Sample: {json.dumps(all_products[0], ensure_ascii=False)[:500]}")
    save(f"fustog_products_{ts}.json", all_products)

# ============================================================
# 3. Fetch Item Prices
# ============================================================
print("\n  Fetching prices...")
prices = api_call("/product/ItemsPrices", method="GET")
if not prices:
    prices = api_call("/product/ItemsPrices", method="POST")

if prices and isinstance(prices, list):
    print(f"  Got {len(prices)} price entries")
    if isinstance(prices[0], dict):
        print(f"  Price keys: {list(prices[0].keys())[:15]}")
        print(f"  Sample: {json.dumps(prices[0], ensure_ascii=False)[:500]}")
    save(f"fustog_prices_{ts}.json", prices)
else:
    print("  No prices data")
    prices = []

# ============================================================
# 4. Fetch retailer/store info
# ============================================================
print("\n  Fetching retailer info...")
retailers = api_call("/retailer/Settings")
if retailers and isinstance(retailers, dict):
    print(f"  Retailer keys: {list(retailers.keys())}")
    save(f"fustog_retailers_{ts}.json", retailers)

stores = api_call("/store/Stores")
if stores:
    print(f"  Stores: {len(stores) if isinstance(stores, list) else 'dict'}")
    save(f"fustog_stores_{ts}.json", stores)

# ============================================================
# 5. Export
# ============================================================
print("\n" + "=" * 60)
print("EXPORT")
print("=" * 60)

if all_products:
    # Build store name lookup from retailers
    store_names = {}
    if retailers and isinstance(retailers, dict):
        for key, val in retailers.items():
            if isinstance(val, dict):
                rid = val.get("retailerId") or val.get("RetailerId") or val.get("id")
                sname = val.get("name") or val.get("Name") or key
                if rid:
                    store_names[str(rid)] = sname

    # Export products
    fieldnames = list(all_products[0].keys())
    with open(f"data/fustog_products_{ts}.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_products)
    print(f"  Products: data/fustog_products_{ts}.csv ({len(all_products)} rows)")

if prices:
    # Export prices
    fieldnames = list(prices[0].keys())
    with open(f"data/fustog_prices_{ts}.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(prices)
    print(f"  Prices: data/fustog_prices_{ts}.csv ({len(prices)} rows)")

    # Count per store
    store_counts = {}
    for p in prices:
        sid = str(p.get("StoreId") or p.get("storeId") or p.get("storeid") or p.get("RetailerId") or "?")
        sn = store_names.get(sid, sid)
        store_counts[sn] = store_counts.get(sn, 0) + 1

    print(f"\n  Prices by store:")
    for store, count in sorted(store_counts.items(), key=lambda x: -x[1]):
        print(f"    {store}: {count}")

    # Merge products + prices
    if all_products:
        product_map = {}
        for p in all_products:
            pid = p.get("Id") or p.get("id") or p.get("PID")
            if pid:
                product_map[pid] = p

        merged = []
        for price in prices:
            pid = price.get("ProductId") or price.get("productId") or price.get("PID")
            sid = price.get("StoreId") or price.get("storeId") or price.get("RetailerId")
            prod = product_map.get(pid, {})

            merged.append({
                "product_id": pid,
                "name_ar": prod.get("Name") or prod.get("name") or prod.get("TitleAR") or "",
                "name_en": prod.get("NameEN") or prod.get("TitleEN") or "",
                "category": prod.get("_category_name", ""),
                "parent_category": prod.get("_parent_category", ""),
                "store_id": sid,
                "store_name": store_names.get(str(sid), str(sid)),
                "price": price.get("Price") or price.get("price") or "",
                "unit": prod.get("Unit") or prod.get("unit") or "",
                "size": prod.get("Size") or prod.get("size") or "",
                "barcode": prod.get("Barcode") or prod.get("barcode") or "",
                "image": prod.get("Image") or prod.get("image") or "",
            })

        if merged:
            fn = list(merged[0].keys())
            with open(f"data/fustog_merged_{ts}.csv", "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fn)
                w.writeheader()
                w.writerows(merged)
            print(f"\n  Merged: data/fustog_merged_{ts}.csv ({len(merged)} rows)")

client.close()
print("\n=== DONE ===")
