#!/usr/bin/env python3
"""Try to fetch from Lulu (POST) and Farm (inspect response)"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import httpx

client = httpx.Client(timeout=15.0, follow_redirects=True)

# ============ LULU - Try POST ============
print("=" * 70)
print("LULU - POST ENDPOINTS")
print("=" * 70)
lulu_h = {
    "Accept": "*/*",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "accept-language": "ar;q=1.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
    "Content-Type": "application/json",
}
lulu_base = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"
lulu_endpoints = [
    ("/api/v1/categories/", {}),
    ("/api/v1/products/", {}),
    ("/api/v1/categories/", {"page": 1}),
    ("/api/v1/products/", {"page": 1}),
    ("/api/v1/products/", {"limit": 20}),
    ("/api/v1/search/", {"q": "rice"}),
    ("/api/v1/home/", {}),
    ("/api/v1/catalog/", {}),
]
for path, body in lulu_endpoints:
    try:
        r = client.post(f"{lulu_base}{path}", json=body, headers=lulu_h, timeout=10)
        has_data = r.status_code == 200 and len(r.content) > 10
        print(f"  [{r.status_code}] POST {path} body={body} size={len(r.content)} {'DATA!' if has_data else ''}")
        if has_data:
            data = r.json()
            if isinstance(data, list):
                print(f"       List[{len(data)}]")
                if data:
                    print(f"       Sample: {json.dumps(data[0], ensure_ascii=False)[:300]}")
            elif isinstance(data, dict):
                print(f"       Keys: {list(data.keys())[:15]}")
                for k in ["results", "products", "items", "data", "categories", "count"]:
                    if k in data:
                        val = data[k]
                        if isinstance(val, list):
                            print(f"       .{k} = List[{len(val)}]")
                            if val:
                                print(f"       First: {json.dumps(val[0], ensure_ascii=False)[:400]}")
                        else:
                            print(f"       .{k} = {val}")
    except Exception as e:
        print(f"  [ERR] POST {path} -> {type(e).__name__}: {e}")

# Also try some known Akinon API patterns
print("\n--- Akinon standard patterns ---")
akinon_paths = [
    "/api/v1/product-list/",
    "/api/v1/product/list/",
    "/api/v1/category/list/",
    "/api/v1/widget/home/",
    "/api/v1/store/list/",
    "/api/v1/city/list/",
]
for path in akinon_paths:
    for method in ["GET", "POST"]:
        try:
            if method == "GET":
                r = client.get(f"{lulu_base}{path}", headers=lulu_h, timeout=10)
            else:
                r = client.post(f"{lulu_base}{path}", json={}, headers=lulu_h, timeout=10)
            if r.status_code not in (404,):
                has_data = r.status_code == 200 and len(r.content) > 10
                print(f"  [{r.status_code}] {method} {path} size={len(r.content)} {'DATA!' if has_data else ''}")
                if has_data:
                    data = r.json()
                    if isinstance(data, dict):
                        print(f"       Keys: {list(data.keys())[:15]}")
        except:
            pass

# ============ FARM - Inspect response ============
print("\n" + "=" * 70)
print("FARM - INSPECT RESPONSES")
print("=" * 70)
farm_h = {"Accept": "application/json", "accept-language": "ar"}
farm_base = "https://go.farm.com.sa/public/api/v1.0"

for path in ["/categories", "/products", "/stores"]:
    r = client.get(f"{farm_base}{path}", headers=farm_h, timeout=10)
    print(f"\n--- {path} ---")
    print(f"Status: {r.status_code}, Size: {len(r.content)}")
    try:
        data = r.json()
        print(f"Full response: {json.dumps(data, ensure_ascii=False)[:2000]}")
    except:
        print(f"Raw: {r.content[:500]}")

# ============ TAMIMI - Scrape HTML ============
print("\n" + "=" * 70)
print("TAMIMI - Check for API in HTML")
print("=" * 70)
r = client.get("https://shop.tamimimarkets.com/categories", timeout=15)
print(f"Status: {r.status_code}, Size: {len(r.content)}")
# Look for API URLs in the HTML
html = r.text
import re
api_urls = set(re.findall(r'https?://[^\s"\'<>]+api[^\s"\'<>]*', html))
for url in sorted(api_urls)[:20]:
    print(f"  Found API URL: {url}")

# Look for __NEXT_DATA__ or similar
if "__NEXT_DATA__" in html:
    start = html.index("__NEXT_DATA__")
    chunk = html[start:start+5000]
    print(f"\n  __NEXT_DATA__ found! Preview:\n{chunk[:2000]}")
elif "window.__" in html:
    matches = re.findall(r'window\.__\w+\s*=\s*', html)
    for m in matches[:5]:
        idx = html.index(m)
        print(f"  Found: {html[idx:idx+200]}")

client.close()
print("\n=== DONE ===")
