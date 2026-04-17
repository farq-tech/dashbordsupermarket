#!/usr/bin/env python3
"""Force extract products from remaining stores using every technique"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, re, time, csv
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

client = httpx.Client(
    timeout=25.0,
    follow_redirects=True,
    headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
)

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_next_data(html):
    if "__NEXT_DATA__" not in html:
        return None
    s = html.index('__NEXT_DATA__')
    ss = html.rfind('<script', 0, s)
    se = html.find('</script>', s)
    js = html.index('>', ss) + 1
    try:
        return json.loads(html[js:se].strip())
    except:
        return None

# ============================================================
# 1. CARREFOUR KSA - Full browser simulation
# ============================================================
print("=" * 60)
print("1. CARREFOUR KSA")
print("=" * 60)

# Step 1: Get the main page and find the real API
r = client.get("https://www.carrefourksa.com/mafsau/ar/")
html = r.text
print(f"  Main page: {len(html)} bytes")

# Find all script bundles
scripts = re.findall(r'src="(https?://[^"]*\.js[^"]*)"', html)
scripts += [f"https://www.carrefourksa.com{s}" for s in re.findall(r'src="(/[^"]*\.js[^"]*)"', html)]
print(f"  Found {len(scripts)} JS bundles")

# Search JS bundles for API URL patterns
api_urls = set()
for script_url in scripts[:20]:
    try:
        r2 = client.get(script_url, timeout=10)
        if r2.status_code == 200:
            js = r2.text
            # Look for API base URLs
            matches = re.findall(r'["\'](https?://[a-zA-Z0-9._-]+(?:mafrservices|mafretail|carrefour)[^"\']*)["\']', js)
            matches += re.findall(r'["\']([^"\']*(?:/api/|/v\d/|/bff/|/graphql)[^"\']*)["\']', js)
            matches += re.findall(r'baseURL:\s*["\']([^"\']+)["\']', js)
            matches += re.findall(r'BASE_URL["\s:=]+["\']([^"\']+)["\']', js)
            matches += re.findall(r'API_URL["\s:=]+["\']([^"\']+)["\']', js)
            matches += re.findall(r'GATEWAY["\s:=]+["\']([^"\']+)["\']', js)
            for m in matches:
                if len(m) > 5 and not m.endswith('.js') and not m.endswith('.css'):
                    api_urls.add(m)
    except:
        pass

print(f"\n  API URLs found in JS bundles:")
for u in sorted(api_urls):
    print(f"    {u}")

# Try all discovered API URLs for products/categories
print("\n  Testing APIs...")
carrefour_products = []
for base_url in sorted(api_urls):
    if not base_url.startswith('http'):
        base_url = f"https://www.carrefourksa.com{base_url}"
    for suffix in ["", "/categories", "/products", "/products?pageSize=20", "/search?q=milk&pageSize=5"]:
        url = f"{base_url.rstrip('/')}{suffix}"
        try:
            r2 = client.get(url, headers={
                "Accept": "application/json",
                "Origin": "https://www.carrefourksa.com",
                "Referer": "https://www.carrefourksa.com/mafsau/ar/",
            }, timeout=8)
            if r2.status_code == 200 and len(r2.content) > 100:
                try:
                    d = r2.json()
                    has_products = False
                    if isinstance(d, dict):
                        for k in ["products", "items", "results", "data", "hits"]:
                            if k in d and isinstance(d[k], list) and d[k]:
                                print(f"  FOUND! [{r2.status_code}] {url[:80]} -> .{k}[{len(d[k])}]")
                                has_products = True
                                break
                    if has_products:
                        save(f"carrefour_found_{len(carrefour_products)}.json", d)
                except:
                    pass
        except:
            pass

# Try direct MAF Services API (common for Carrefour worldwide)
print("\n  --- MAF Services API ---")
maf_h = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
    "x-ibm-client-id": "mafsau",
    "lang": "ar",
    "storeId": "mafsau",
    "country": "SA",
}
maf_endpoints = [
    "https://api.mafrservices.com/api/v2/categories?storeId=mafsau&lang=ar",
    "https://api.mafrservices.com/api/v2/products?storeId=mafsau&lang=ar&pageSize=5",
    "https://api.mafrservices.com/api/v1/categories?storeId=mafsau",
    "https://api.mafrservices.com/api/v1/products?storeId=mafsau&pageSize=5",
    "https://api.mafrservices.com/api/categories",
    "https://api.mafrservices.com/api/products",
    "https://cdn.mafrservices.com/api/categories",
    "https://cdn.mafrservices.com/api/products",
]
for url in maf_endpoints:
    try:
        r2 = client.get(url, headers=maf_h, timeout=8)
        if r2.status_code not in (404, 403) and len(r2.content) > 50:
            print(f"  [{r2.status_code}] {url.split('//')[1][:60]} size={len(r2.content)}")
            if r2.status_code == 200:
                try:
                    d = r2.json()
                    print(f"    {json.dumps(d, ensure_ascii=False)[:400]}")
                except:
                    pass
    except Exception as e:
        if "Connect" not in str(type(e).__name__):
            print(f"  [ERR] {url.split('//')[1][:60]} -> {type(e).__name__}")

# ============================================================
# 2. LULU - Try website catalog pages
# ============================================================
print("\n" + "=" * 60)
print("2. LULU HYPERMARKET")
print("=" * 60)

# Try catalog/category pages on luluhypermarket.com
lulu_urls = [
    "https://www.luluhypermarket.com/en-sa/grocery/c/HY00214301",
    "https://www.luluhypermarket.com/en-sa/department/grocery/c/HY00214301",
    "https://www.luluhypermarket.com/en-sa/fresh-food/c/HY00214302",
    "https://www.luluhypermarket.com/api/search?q=rice&lang=en&country=sa",
    "https://www.luluhypermarket.com/api/product/search?q=rice",
    "https://www.luluhypermarket.com/api/v1/products?q=rice",
]
lulu_h = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36",
    "Accept-Language": "en-SA,en;q=0.9,ar;q=0.8",
}
for url in lulu_urls:
    try:
        r = client.get(url, headers=lulu_h, timeout=10)
        print(f"  [{r.status_code}] {url.replace('https://www.luluhypermarket.com','')[:60]} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 500:
            nd = extract_next_data(r.text)
            if nd:
                print(f"    __NEXT_DATA__ found!")
                pp = nd.get("props", {}).get("pageProps", {})
                print(f"    pageProps: {list(pp.keys())[:10]}")
                save("lulu_nextdata.json", nd)
            # Check for product data in HTML
            prod_count = len(re.findall(r'"sku":|"productId":|"price":', r.text))
            if prod_count > 5:
                print(f"    Found {prod_count} product-like fields in HTML!")
    except Exception as e:
        print(f"  [{type(e).__name__}] {url.replace('https://','')[:60]}")

# ============================================================
# 3. FARM - Try different API versions
# ============================================================
print("\n" + "=" * 60)
print("3. FARM SUPERSTORES")
print("=" * 60)

# Farm website might have product data
farm_h = {
    "Accept": "text/html",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36",
}
# Try the farm.com.sa website
try:
    r = client.get("https://farm.com.sa", headers=farm_h, timeout=10)
    print(f"  farm.com.sa: {r.status_code}, size={len(r.content)}")
    if r.status_code == 200:
        nd = extract_next_data(r.text)
        if nd:
            print(f"  __NEXT_DATA__!")
            save("farm_web_nextdata.json", nd)
        # Check for API base
        api_bases = set(re.findall(r'https?://[^\s"\'<>]+', r.text))
        farm_apis = [a for a in api_bases if 'farm' in a.lower() and ('api' in a.lower() or 'product' in a.lower())]
        for a in sorted(farm_apis)[:10]:
            print(f"    {a}")
        # Look for app store links
        app_links = [a for a in api_bases if 'play.google' in a or 'apple.com/app' in a]
        for a in app_links[:3]:
            print(f"    App: {a}")
except Exception as e:
    print(f"  ERR: {e}")

# Try go.farm.com.sa with different API versions
farm_api_h = {"Accept": "application/json", "User-Agent": "okhttp/5.0.0-alpha.6"}
for version in ["v1.0", "v1.1", "v1.2", "v2.0", "v2", "v3"]:
    for endpoint in ["categories", "products", "home"]:
        url = f"https://go.farm.com.sa/public/api/{version}/{endpoint}"
        try:
            r = client.get(url, headers=farm_api_h, timeout=5)
            if r.status_code == 200:
                try:
                    d = r.json()
                    if d.get("status") != False:  # Skip "route not found" errors
                        print(f"  [{r.status_code}] /api/{version}/{endpoint} DATA!")
                        print(f"    {json.dumps(d, ensure_ascii=False)[:300]}")
                except:
                    pass
        except:
            pass

# Also try POST
for endpoint in ["categories", "products", "home", "search"]:
    for base in ["https://go.farm.com.sa/api", "https://go.farm.com.sa/public/api"]:
        for version in ["v1", "v1.0", "v2"]:
            url = f"{base}/{version}/{endpoint}"
            try:
                r = client.post(url, json={}, headers=farm_api_h, timeout=5)
                if r.status_code == 200:
                    try:
                        d = r.json()
                        if d.get("status") != False:
                            print(f"  [{r.status_code}] POST {url.split('.sa')[1]} DATA!")
                            print(f"    {json.dumps(d, ensure_ascii=False)[:300]}")
                    except:
                        pass
            except:
                pass

# ============================================================
# 4. RAMEZ - Try website
# ============================================================
print("\n" + "=" * 60)
print("4. RAMEZ")
print("=" * 60)

for url in [
    "https://ramezonline.com",
    "https://www.ramezonline.com",
    "https://ramez.com",
    "https://www.ramez.com",
    "https://shop.ramez.com",
    "https://ramez.sa",
    "https://www.ramez.sa",
]:
    try:
        r = client.get(url, headers=farm_h, timeout=8)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 500:
            nd = extract_next_data(r.text)
            if nd:
                print(f"    __NEXT_DATA__!")
            apis = set(re.findall(r'https?://[^\s"\'<>]*(?:api|product|categor)[^\s"\'<>]*', r.text))
            for a in sorted(apis)[:5]:
                print(f"    API: {a}")
    except Exception as e:
        print(f"  [{type(e).__name__}] {url}")

# Try risteh API with auth header variations
print("\n  --- Risteh API variations ---")
ramez_variations = [
    {"apikey": "^~>h2q=m[h=>3?bU/!M'X!m~?4GjKJP{Q@y;~fa3Vjs/M#`8FuB;x[LKwJ&>gNrxBt8!5PZ:9QLuHBUtu{TPc2s]k74]Br?PGe6+NcFUT-8",
     "Accept": "application/json", "User-Agent": "Ramez/8 CFNetwork/1404.0.5 Darwin/22.3.0",
     "app_version": "5.9.4", "device_type": "iOS", "accept-language": "ar",
     "country_id": "SA"},
]
for h in ramez_variations:
    for base in ["https://risteh.com/SA/GroceryStoreApi", "https://risteh.com"]:
        for p in ["/api/v9/Home/index", "/api/v9/Categories/list", "/api/v8/Home/index",
                  "/api/v7/Home/index", "/api/v10/Home/index"]:
            for method in ["POST", "GET"]:
                try:
                    if method == "POST":
                        r = client.post(f"{base}{p}", json={"country_id": "SA", "lang": "ar"},
                                       headers=h, timeout=5)
                    else:
                        r = client.get(f"{base}{p}", headers=h, timeout=5)
                    if r.status_code == 200 and len(r.content) > 50:
                        print(f"  [{r.status_code}] {method} {base.split('//')[1][:20]}{p} size={len(r.content)}")
                        try:
                            d = r.json()
                            print(f"    {json.dumps(d, ensure_ascii=False)[:400]}")
                        except:
                            pass
                except:
                    pass

# ============================================================
# 5. SADHAN - Try website directly
# ============================================================
print("\n" + "=" * 60)
print("5. AL SADHAN")
print("=" * 60)

for url in [
    "https://alsadhan.com",
    "https://www.alsadhanstores.com",
    "https://alsadhanstores.com",
    "https://shop.alsadhan.com",
    "https://alsadhan.witheldokan.com",
]:
    try:
        r = client.get(url, headers=farm_h, timeout=8)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 500:
            nd = extract_next_data(r.text)
            if nd:
                print(f"    __NEXT_DATA__!")
                save("sadhan_nextdata.json", nd)
            # Check for Angular/React app
            if "ng-app" in r.text or "react" in r.text.lower() or "__NUXT__" in r.text:
                print(f"    SPA app detected")
            apis = set(re.findall(r'https?://[^\s"\'<>]*(?:api|product|categor)[^\s"\'<>]*', r.text))
            for a in sorted(apis)[:5]:
                print(f"    API: {a}")
    except Exception as e:
        print(f"  [{type(e).__name__}] {url}")

# Try Eldokan API patterns
print("\n  --- Eldokan API ---")
for base in ["https://alsadhan.witheldokan.com", "https://sadhanmarketapi.witheldokan.com"]:
    for p in ["/api/v1/home", "/api/v1/categories", "/api/v1/products",
              "/api/v2/home", "/api/v2/categories", "/api/v2/products",
              "/home", "/categories", "/products"]:
        try:
            r = client.get(f"{base}{p}", headers={"Accept": "application/json"}, timeout=5)
            ct = r.headers.get("content-type", "")
            if "json" in ct and r.status_code == 200 and len(r.content) > 50:
                d = r.json()
                print(f"  [{r.status_code}] {base.split('//')[1][:25]}{p} JSON! size={len(r.content)}")
                print(f"    {json.dumps(d, ensure_ascii=False)[:400]}")
        except:
            pass

client.close()
print("\n=== DONE ===")
