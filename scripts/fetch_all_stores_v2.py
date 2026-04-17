#!/usr/bin/env python3
"""Aggressive fetch for ALL remaining stores"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time, re
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
client = httpx.Client(timeout=20.0, follow_redirects=True)

def save_json(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_next_data(html):
    """Extract __NEXT_DATA__ from HTML"""
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
# 1. FARM - returned 200 with 7626 bytes earlier!
# ============================================================
print("=" * 60)
print("1. FARM SUPERSTORES")
print("=" * 60)
farm_products = []
farm_h = {"Accept": "application/json", "accept-language": "ar", "User-Agent": "okhttp/5.0.0-alpha.6"}

# The stores endpoint worked - let's see what it returns
try:
    r = client.get("https://go.farm.com.sa/public/api/v1.0/stores", headers=farm_h, timeout=10)
    print(f"  /stores: {r.status_code}, size={len(r.content)}")
    if r.status_code == 200:
        d = r.json()
        save_json("farm_stores.json", d)
        if isinstance(d, dict):
            print(f"  Keys: {list(d.keys())[:10]}")
            for k in ["data", "stores", "results"]:
                if k in d:
                    print(f"  .{k} type={type(d[k]).__name__}")
                    if isinstance(d[k], list) and d[k]:
                        print(f"  .{k}[0] keys: {list(d[k][0].keys())[:10]}")
        elif isinstance(d, list) and d:
            print(f"  List[{len(d)}], first keys: {list(d[0].keys())[:10]}")
        print(f"  Preview: {json.dumps(d, ensure_ascii=False)[:800]}")
except Exception as e:
    print(f"  stores ERR: {e}")

# Try more Farm endpoints
farm_paths = [
    "/public/api/v1.0/categories", "/public/api/v1.0/products",
    "/public/api/v1.0/products?page=1", "/public/api/v1.0/home",
    "/public/api/v1.0/banners", "/public/api/v1.0/offers",
    "/public/api/v1.0/search?q=milk", "/public/api/v1.0/search?keyword=milk",
]
for p in farm_paths:
    try:
        r = client.get(f"https://go.farm.com.sa{p}", headers=farm_h, timeout=8)
        if r.status_code == 200 and len(r.content) > 50:
            print(f"  [{r.status_code}] {p} size={len(r.content)} DATA!")
            d = r.json()
            print(f"    Preview: {json.dumps(d, ensure_ascii=False)[:500]}")
    except:
        pass

# Try Farm website
print("\n  --- Farm website ---")
try:
    r = client.get("https://farm.com.sa", headers={"Accept":"text/html","User-Agent":"Mozilla/5.0"}, timeout=10)
    print(f"  farm.com.sa: {r.status_code}, size={len(r.content)}")
    if r.status_code in (301, 302):
        print(f"  Redirect: {r.headers.get('location')}")
    elif r.status_code == 200:
        nd = extract_next_data(r.text)
        if nd:
            print(f"  Has __NEXT_DATA__!")
            save_json("farm_nextdata.json", nd)
        # Find API URLs
        apis = set(re.findall(r'https?://[^\s"\'<>]*api[^\s"\'<>]*', r.text))
        for a in sorted(apis)[:10]:
            print(f"    API: {a}")
except Exception as e:
    print(f"  ERR: {e}")

# ============================================================
# 2. CARREFOUR KSA
# ============================================================
print("\n" + "=" * 60)
print("2. CARREFOUR KSA")
print("=" * 60)

# Carrefour KSA uses MAF (Majid Al Futtaim) platform
# Try their known API patterns
carrefour_h = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
    "Accept-Language": "ar",
}

# Try the main website first
print("  --- Website scraping ---")
try:
    r = client.get("https://www.carrefourksa.com/mafsau/ar/", headers={
        "Accept": "text/html", "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"}, timeout=15)
    print(f"  carrefourksa.com: {r.status_code}, size={len(r.content)}")
    if r.status_code == 200 and len(r.content) > 100:
        html = r.text
        nd = extract_next_data(html)
        if nd:
            print(f"  Has __NEXT_DATA__!")
            save_json("carrefour_nextdata.json", nd)
        # Find API URLs in HTML/JS
        apis = set(re.findall(r'https?://[^\s"\'<>]+', html))
        api_urls = [a for a in apis if 'api' in a.lower() or 'product' in a.lower() or 'categor' in a.lower()]
        for a in sorted(api_urls)[:15]:
            print(f"    URL: {a}")
        # Find JSON data
        json_blocks = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL)
        for i, block in enumerate(json_blocks[:3]):
            if len(block) > 100:
                print(f"    JSON block {i}: {len(block)} bytes")
                try:
                    d = json.loads(block)
                    if isinstance(d, dict):
                        print(f"      Keys: {list(d.keys())[:10]}")
                except:
                    pass
except Exception as e:
    print(f"  ERR: {e}")

# Try Carrefour API with Hybris patterns (MAF uses SAP Hybris)
print("\n  --- Hybris/MAF API patterns ---")
hybris_paths = [
    "/api/v7/categories?lang=ar&storeId=mafsau",
    "/api/v7/products?currentPage=0&pageSize=5&lang=ar&storeId=mafsau",
    "/api/v4/categories?lang=ar",
    "/api/v4/products?currentPage=0&pageSize=5&lang=ar",
    "/api/v2/products?currentPage=0&pageSize=5",
    "/api/v1/categories",
    "/rest/v2/mafsau/categories",
    "/rest/v2/mafsau/products/search?pageSize=5",
    "/occ/v2/mafsau/categories",
    "/occ/v2/mafsau/products/search?pageSize=5",
]
for base in ["https://www.carrefourksa.com", "https://api.carrefourksa.com"]:
    for p in hybris_paths:
        try:
            r = client.get(f"{base}{p}", headers=carrefour_h, timeout=8)
            if r.status_code == 200 and len(r.content) > 50:
                print(f"  [{r.status_code}] {base.split('//')[1].split('/')[0]}{p} size={len(r.content)} DATA!")
                d = r.json()
                print(f"    Preview: {json.dumps(d, ensure_ascii=False)[:500]}")
                save_json(f"carrefour_data_{p.replace('/','_')[:30]}.json", d)
        except:
            pass

# ============================================================
# 3. LULU HYPERMARKET
# ============================================================
print("\n" + "=" * 60)
print("3. LULU HYPERMARKET")
print("=" * 60)

# Try luluhypermarket.com website (not the Akinon API)
print("  --- Website ---")
lulu_web_h = {
    "Accept": "text/html",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "ar",
}
for url in [
    "https://www.luluhypermarket.com/en-sa",
    "https://www.luluhypermarket.com/en-sa/grocery",
    "https://www.lulu-saudi.com",
    "https://saudi.luluhypermarket.com",
]:
    try:
        r = client.get(url, headers=lulu_web_h, timeout=10)
        print(f"  [{r.status_code}] {url.replace('https://','')[:50]} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 500:
            nd = extract_next_data(r.text)
            if nd:
                print(f"    Has __NEXT_DATA__!")
                save_json("lulu_nextdata.json", nd)
                pp = nd.get("props", {}).get("pageProps", {})
                print(f"    pageProps keys: {list(pp.keys())[:15]}")
            # Find API URLs
            apis = set(re.findall(r'https?://[^\s"\'<>]+api[^\s"\'<>]*', r.text))
            for a in sorted(apis)[:5]:
                print(f"    API: {a}")
    except Exception as e:
        print(f"  [{type(e).__name__}] {url.replace('https://','')[:50]}")

# Try Akinon commerce cloud API patterns
print("\n  --- Akinon Commerce API ---")
lulu_base = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"
lulu_h = {
    "Accept": "application/json",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "accept-language": "ar",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
}
akinon_paths = [
    "/ccm/api/v1/products/?limit=5",
    "/ccm/api/v1/categories/",
    "/ccm/api/products/",
    "/ccm/api/categories/",
    "/users/otp-login/",
    "/api/product/search/?q=rice",
    "/api/search/?q=rice",
]
for p in akinon_paths:
    for method in ["GET"]:
        try:
            r = client.get(f"{lulu_base}{p}", headers=lulu_h, timeout=8)
            if r.status_code not in (404,) and len(r.content) > 10:
                print(f"  [{r.status_code}] {p} size={len(r.content)}")
                if r.status_code == 200 and len(r.content) > 50:
                    print(f"    Preview: {r.content[:300]}")
        except:
            pass

# ============================================================
# 4. RAMEZ
# ============================================================
print("\n" + "=" * 60)
print("4. RAMEZ")
print("=" * 60)
ramez_h = {
    "Accept": "application/json",
    "apikey": "^~>h2q=m[h=>3?bU/!M'X!m~?4GjKJP{Q@y;~fa3Vjs/M#`8FuB;x[LKwJ&>gNrxBt8!5PZ:9QLuHBUtu{TPc2s]k74]Br?PGe6+NcFUT-8",
    "User-Agent": "Ramez/8 CFNetwork/1404.0.5 Darwin/22.3.0",
    "app_version": "5.9.4",
    "device_type": "iOS",
    "accept-language": "ar",
}
ramez_base = "https://risteh.com/SA/GroceryStoreApi"

# Try POST instead (many mobile APIs are POST-only)
print("  --- POST endpoints ---")
for p in [
    "/api/v9/Home/index",
    "/api/v9/Categories/list",
    "/api/v9/Products/list",
    "/api/v9/Home",
]:
    for method in ["POST", "GET"]:
        try:
            if method == "POST":
                r = client.post(f"{ramez_base}{p}", json={}, headers=ramez_h, timeout=8)
            else:
                r = client.get(f"{ramez_base}{p}", headers=ramez_h, timeout=8)
            if r.status_code != 404 and len(r.content) > 0:
                has = r.status_code == 200 and len(r.content) > 50
                print(f"  [{r.status_code}] {method} {p} size={len(r.content)} {'DATA!' if has else ''}")
                if has:
                    try:
                        d = r.json()
                        print(f"    Preview: {json.dumps(d, ensure_ascii=False)[:500]}")
                    except:
                        print(f"    Raw: {r.content[:200]}")
        except:
            pass

# Try with body params
print("\n  --- POST with body ---")
bodies = [
    {"country_id": "SA", "language": "ar"},
    {"country_id": 1, "lang": "ar"},
    {"store_id": 1},
    {},
]
for body in bodies:
    try:
        r = client.post(f"{ramez_base}/api/v9/Home/index", json=body, headers=ramez_h, timeout=8)
        if r.status_code != 404:
            print(f"  [{r.status_code}] POST Home/index body={body} size={len(r.content)}")
            if r.status_code == 200 and len(r.content) > 50:
                print(f"    {r.json() if len(r.content) < 500 else r.content[:300]}")
    except:
        pass

# Try ramez.com.sa
print("\n  --- ramez.com.sa ---")
for url in ["https://www.ramez.com.sa", "https://ramez.com.sa"]:
    try:
        r = client.get(url, headers={"Accept":"text/html","User-Agent":"Mozilla/5.0"}, timeout=8)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
        if r.status_code == 200:
            nd = extract_next_data(r.text)
            if nd:
                print(f"    __NEXT_DATA__ found!")
            apis = set(re.findall(r'https?://[^\s"\'<>]*api[^\s"\'<>]*', r.text))
            for a in sorted(apis)[:5]:
                print(f"    API: {a}")
    except Exception as e:
        print(f"  [{type(e).__name__}] {url}")

# ============================================================
# 5. SADHAN (AL SADHAN)
# ============================================================
print("\n" + "=" * 60)
print("5. AL SADHAN")
print("=" * 60)
sadhan_h = {
    "Accept": "application/json",
    "User-Agent": "Alsadhan%20Stores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
    "accept-language": "ar",
}

# Try the Eldokan API with different patterns
for base in [
    "https://sadhanmarketapi.witheldokan.com",
    "https://alsadhan.witheldokan.com",
]:
    for p in ["/api/home", "/api/categories", "/api/products", "/api/guest/home"]:
        try:
            r = client.get(f"{base}{p}", headers=sadhan_h, timeout=8)
            if r.status_code != 404:
                has = r.status_code == 200 and len(r.content) > 50
                print(f"  [{r.status_code}] {base.split('//')[1][:30]}{p} size={len(r.content)} {'DATA!' if has else ''}")
                if has:
                    d = r.json()
                    print(f"    Preview: {json.dumps(d, ensure_ascii=False)[:500]}")
        except Exception as e:
            print(f"  [{type(e).__name__}] {base.split('//')[1][:30]}{p}")

# Try alsadhan.com
print("\n  --- alsadhan.com ---")
for url in ["https://www.alsadhan.com", "https://alsadhan.com", "https://shop.alsadhan.com"]:
    try:
        r = client.get(url, headers={"Accept":"text/html","User-Agent":"Mozilla/5.0"}, timeout=8)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 500:
            nd = extract_next_data(r.text)
            if nd:
                print(f"    __NEXT_DATA__!")
    except Exception as e:
        print(f"  [{type(e).__name__}] {url}")

# ============================================================
# 6. SPAR
# ============================================================
print("\n" + "=" * 60)
print("6. SPAR SAUDI")
print("=" * 60)
for url in ["https://www.spar.sa", "https://spar.sa", "https://www.sparhypermarket.sa", "https://shop.spar.sa"]:
    try:
        r = client.get(url, headers={"Accept":"text/html","User-Agent":"Mozilla/5.0"}, timeout=8)
        print(f"  [{r.status_code}] {url} size={len(r.content)}")
    except Exception as e:
        print(f"  [{type(e).__name__}] {url}")

client.close()
print("\n=== DONE ===")
