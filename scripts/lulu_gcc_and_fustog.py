#!/usr/bin/env python3
"""Try Lulu GCC website API + Fustog backend for all stores"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time, zlib, base64
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

client = httpx.Client(timeout=25.0, follow_redirects=True)

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# PART 1: Lulu GCC Website API
# ============================================================
print("=" * 60)
print("PART 1: Lulu GCC Website API")
print("=" * 60)

gcc_h = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "accept-language": "ar-SA,ar;q=0.9,en;q=0.8",
    "Referer": "https://gcc.luluhypermarket.com/en-sa/grocery",
}

gcc_urls = [
    # Main page widgets
    "https://gcc.luluhypermarket.com/api/client/widgets/?location=homepage&page_type=homepage",
    "https://gcc.luluhypermarket.com/api/client/widgets/?location=all_pages&page_type=all_pages",

    # Category tree
    "https://gcc.luluhypermarket.com/api/client/category-tree/",
    "https://gcc.luluhypermarket.com/api/client/categories/",

    # Products
    "https://gcc.luluhypermarket.com/api/client/products/?limit=20",
    "https://gcc.luluhypermarket.com/api/client/products/?limit=20&page=1",

    # Search
    "https://gcc.luluhypermarket.com/api/client/search/?q=milk&limit=20",
    "https://gcc.luluhypermarket.com/api/client/search/?q=حليب&limit=20",
    "https://gcc.luluhypermarket.com/api/client/auto-complete/?q=milk",
    "https://gcc.luluhypermarket.com/api/client/auto-complete/?q=حليب",

    # Store selector
    "https://gcc.luluhypermarket.com/api/client/stores/",
    "https://gcc.luluhypermarket.com/api/client/config/",

    # Other patterns
    "https://gcc.luluhypermarket.com/api/client/data-sources/",
    "https://gcc.luluhypermarket.com/api/client/channels/",
    "https://gcc.luluhypermarket.com/api/v1/products/",
    "https://gcc.luluhypermarket.com/api/v2/products/",

    # Non-API paths
    "https://gcc.luluhypermarket.com/api/en-sa/grocery",
    "https://gcc.luluhypermarket.com/api/en-sa/products",

    # Alternative base paths
    "https://www.luluhypermarket.com/api/client/products/?limit=20",
    "https://www.luluhypermarket.com/api/client/category-tree/",
    "https://www.luluhypermarket.com/api/client/config/",
    "https://www.luluhypermarket.com/api/client/widgets/?location=homepage",
    "https://www.luluhypermarket.com/api/client/auto-complete/?q=milk",
    "https://www.luluhypermarket.com/api/client/search/?q=milk&limit=20",
]

for url in gcc_urls:
    try:
        r = client.get(url, headers=gcc_h, timeout=15)
        if r.status_code == 200 and len(r.content) > 50:
            try:
                d = r.json()
                text = json.dumps(d, ensure_ascii=False)[:300]

                # Check if it's meaningful data
                if isinstance(d, dict):
                    count = d.get("count", 0)
                    results = d.get("results", d.get("data", []))
                    if isinstance(results, list) and results:
                        print(f"  [200] {url.split('.com')[1][:60]}")
                        print(f"    count={count} results={len(results)}")
                        if isinstance(results[0], dict):
                            print(f"    Keys: {list(results[0].keys())[:12]}")
                            print(f"    Sample: {json.dumps(results[0], ensure_ascii=False)[:250]}")
                        # Save
                        fname = url.split(".com")[1].strip("/").replace("/", "_").replace("?", "_")[:40]
                        save(f"lulu_gcc_{fname}.json", d)
                    elif d.get("groups") or d.get("categories") or d.get("widgets"):
                        print(f"  [200] {url.split('.com')[1][:60]}")
                        print(f"    Keys: {list(d.keys())[:10]}")
                        for k in d:
                            v = d[k]
                            if isinstance(v, list):
                                print(f"    .{k}: Array[{len(v)}]")
                        fname = url.split(".com")[1].strip("/").replace("/", "_").replace("?", "_")[:40]
                        save(f"lulu_gcc_{fname}.json", d)
                    else:
                        keys = list(d.keys())
                        if len(keys) > 2:
                            print(f"  [200] {url.split('.com')[1][:60]}: {keys[:10]}")
                elif isinstance(d, list) and d:
                    print(f"  [200] {url.split('.com')[1][:60]}: Array[{len(d)}]")
                    if isinstance(d[0], dict):
                        print(f"    Keys: {list(d[0].keys())[:12]}")
                    fname = url.split(".com")[1].strip("/").replace("/", "_").replace("?", "_")[:40]
                    save(f"lulu_gcc_{fname}.json", d)
            except:
                # Not JSON
                if r.status_code == 200:
                    ct = r.headers.get("content-type", "")
                    if "html" not in ct:
                        print(f"  [200] {url.split('.com')[1][:60]}: {ct} {len(r.content)}b")
        elif r.status_code == 403:
            pass  # Cloudflare blocked
        elif r.status_code not in (404, 405, 301, 302, 403):
            print(f"  [{r.status_code}] {url.split('.com')[1][:60]}: {r.text[:80]}")
    except Exception as e:
        if "timeout" not in str(e).lower():
            print(f"  ERR {url.split('.com')[1][:50]}: {type(e).__name__}")

# ============================================================
# PART 2: Fustog API - try more endpoints
# ============================================================
print("\n" + "=" * 60)
print("PART 2: Fustog API - all endpoints")
print("=" * 60)

FUSTOG = "https://api.fustog.app/api/v1"
fh = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "okhttp/4.10.0",
}

# Try various Fustog endpoints
fustog_endpoints = [
    ("GET", "/category/Categories", None),
    ("POST", "/product/ProductsByCategory", {"categoryId": 1}),
    ("POST", "/product/ProductsByCategory", {"categoryId": 2}),
    ("POST", "/product/ProductsByCategory", {"CategoryId": 1}),
    ("POST", "/product/ProductsByCategory", {"category_id": 1}),
    ("GET", "/product/ProductsByCategory?categoryId=1", None),
    ("POST", "/product/ItemsPrices", {"categoryId": 1}),
    ("POST", "/product/ItemsPrices", {"productIds": [1, 2, 3]}),
    ("GET", "/product/ItemsPrices?categoryId=1", None),
    ("GET", "/retailer/Settings", None),
    ("GET", "/retailer/Retailers", None),
    ("GET", "/retailer/List", None),
    ("POST", "/product/Search", {"query": "milk"}),
    ("POST", "/product/Search", {"keyword": "milk"}),
    ("GET", "/product/Search?q=milk", None),
    ("GET", "/product/Products", None),
    ("GET", "/product/All", None),
    ("GET", "/product/List", None),
    ("POST", "/product/Products", {"page": 1}),
    ("GET", "/category/SubCategories?parentId=1", None),
    ("POST", "/category/SubCategories", {"parentId": 1}),
    ("GET", "/price/Prices", None),
    ("GET", "/price/Compare", None),
    ("POST", "/price/Compare", {"productId": 1}),
    ("GET", "/store/Stores", None),
    ("GET", "/store/List", None),
    ("GET", "/retailer/Products", None),
    ("POST", "/retailer/Products", {"retailerId": 1}),
]

# LZ-String decompression (from scrape_products_prices_compare.py)
def try_decompress(data):
    """Try to decompress LZ-String compressed data"""
    if isinstance(data, str) and len(data) > 10:
        try:
            # Try base64 decode + zlib
            decoded = base64.b64decode(data)
            return zlib.decompress(decoded).decode("utf-8")
        except:
            pass
        try:
            # Try raw zlib
            return zlib.decompress(data.encode("utf-8")).decode("utf-8")
        except:
            pass
    return None

for method, ep, body in fustog_endpoints:
    try:
        if method == "GET":
            r = client.get(f"{FUSTOG}{ep}", headers=fh, timeout=15)
        else:
            r = client.post(f"{FUSTOG}{ep}", headers=fh, json=body, timeout=15)

        if r.status_code == 200:
            content = r.content
            if len(content) > 0:
                try:
                    d = r.json()
                    text = json.dumps(d, ensure_ascii=False)[:300]
                    print(f"  [200] {method} {ep}: {text[:200]}")

                    # Check if it's LZ compressed
                    if isinstance(d, str):
                        decompressed = try_decompress(d)
                        if decompressed:
                            print(f"    Decompressed: {decompressed[:200]}")
                            try:
                                parsed = json.loads(decompressed)
                                fname = ep.strip("/").replace("/", "_")
                                save(f"fustog_{fname}.json", parsed)
                                print(f"    >>> Saved fustog_{fname}.json!")
                            except:
                                pass
                    elif isinstance(d, dict) or isinstance(d, list):
                        fname = ep.strip("/").replace("/", "_")
                        save(f"fustog_{fname}.json", d)
                except:
                    # Raw binary - might be LZ compressed
                    print(f"  [200] {method} {ep}: binary {len(content)}b")
                    text = content.decode("utf-8", errors="replace")
                    decompressed = try_decompress(text)
                    if decompressed:
                        print(f"    LZ Decompressed: {decompressed[:200]}")
            else:
                pass  # Empty response, skip
        elif r.status_code != 404:
            print(f"  [{r.status_code}] {method} {ep}: {r.text[:100]}")
    except Exception as e:
        if "timeout" not in str(e).lower():
            print(f"  ERR {method} {ep}: {type(e).__name__}")

# ============================================================
# PART 3: Farm - Last attempts with cookie/session approach
# ============================================================
print("\n" + "=" * 60)
print("PART 3: Farm - Cookie and session approach")
print("=" * 60)

with open("data/farm_auth.json", "r") as f:
    auth = json.load(f)
TOKEN = auth["result"]["token"]

# Try login again and capture cookies
farm_h = {
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
    "accept-encoding": "deflate",
    "accept-language": "en-US,en;q=0.9",
    "User-Agent": "FarmStores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
}

# Try with session (cookies)
session = httpx.Client(timeout=15.0, follow_redirects=True)

# First set auth
farm_h_auth = {
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}",
    "accept-encoding": "deflate",
    "accept-language": "ar",
    "User-Agent": "FarmStores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
}

# Try /home with form-urlencoded content type and location in various ways
# Maybe the app sends location as part of initial handshake

# Try including store_id in URL path
for sid in [1, 2, 3, 4, 5, 10, 15, 20]:
    for ep in [f"/home/{sid}", f"/home?store_id={sid}", f"/store/{sid}/home", f"/{sid}/home"]:
        try:
            r = session.get(f"https://go.farm.com.sa/public/api/v1.0{ep}", headers=farm_h_auth, timeout=8)
            text = r.text
            if "location" not in text.lower() and "not found" not in text.lower():
                print(f"  [{r.status_code}] GET {ep}: {text[:200]}")
            elif "location" in text.lower() and "not found" not in text.lower():
                pass  # Still needs location
        except:
            pass

# Try completely different approach - maybe it's a POST with content-type form
for ct in ["application/x-www-form-urlencoded", "multipart/form-data"]:
    for body in [
        f"lat=24.7136&lng=46.6753",
        f"latitude=24.7136&longitude=46.6753",
        f"store_id=1",
        f"city_id=1",
    ]:
        try:
            r = session.request(
                "GET",
                "https://go.farm.com.sa/public/api/v1.0/home",
                headers={**farm_h_auth, "Content-Type": ct},
                content=body,
                timeout=8,
            )
            text = r.text
            if "location" not in text.lower() and "not found" not in text.lower():
                print(f"  [GET+body {ct[:20]}] /home: {text[:200]}")
        except:
            pass

session.close()
client.close()
print("\n=== DONE ===")
