#!/usr/bin/env python3
"""Tamimi: Try ZopSmart catalogue API with storeId"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import httpx

client = httpx.Client(timeout=30.0, follow_redirects=True)
BASE = "https://shop.tamimimarkets.com"

headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
    "Accept-Language": "ar,en;q=0.9",
}

# ZopSmart APIs typically need storeId in header or query
# Store IDs from the store endpoint: 73 (Riyadh), etc.
store_ids = [73, 2, 1, "V167"]

print("=" * 60)
print("Testing ZopSmart product API patterns")
print("=" * 60)

# Pattern 1: Category products via API with storeId
for sid in store_ids:
    paths = [
        f"/api/categories?storeId={sid}",
        f"/api/products?storeId={sid}&limit=5",
        f"/api/products?storeId={sid}&categoryId=247&limit=5",
        f"/api/catalogue?storeId={sid}",
    ]
    print(f"\n--- storeId={sid} ---")
    for path in paths:
        try:
            r = client.get(f"{BASE}{path}", headers=headers, timeout=10)
            has = r.status_code == 200 and len(r.content) > 50
            if r.status_code not in (404,):
                print(f"  [{r.status_code}] {path} size={len(r.content)} {'DATA!' if has else ''}")
                if has:
                    d = r.json()
                    print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
        except:
            pass

# Pattern 2: ZopSmart uses /api with specific headers
print("\n\n--- Headers with storeId ---")
for sid in store_ids[:2]:
    h = dict(headers)
    h["storeId"] = str(sid)
    h["x-store-id"] = str(sid)
    for path in ["/api/categories", "/api/products?limit=5", "/api/products?categoryId=247&limit=5"]:
        try:
            r = client.get(f"{BASE}{path}", headers=h, timeout=10)
            has = r.status_code == 200 and len(r.content) > 50
            if r.status_code not in (404,):
                print(f"  [{r.status_code}] {path} (storeId={sid} in header) size={len(r.content)} {'DATA!' if has else ''}")
                if has:
                    d = r.json()
                    print(f"       {json.dumps(d, ensure_ascii=False)[:400]}")
        except:
            pass

# Pattern 3: Direct ZopSmart API host
print("\n\n--- Try direct ZopSmart API ---")
zop_bases = [
    "https://api.zopsmart.com",
    "https://tamimimarkets.zopsmart.com",
    "https://tm.zopsmart.com",
]
for base in zop_bases:
    for path in ["/api/categories", "/api/products", "/v1/categories", "/v1/products"]:
        try:
            r = client.get(f"{base}{path}", headers=headers, timeout=5)
            if r.status_code not in (404, 502, 503):
                print(f"  [{r.status_code}] {base}{path} size={len(r.content)}")
        except Exception as e:
            print(f"  [ERR] {base}{path} -> {type(e).__name__}")

# Pattern 4: Look at what _next/data routes are actually available
print("\n\n--- _next/data routes ---")
build_id = "KKet2UOH4fkWP9Kag2Bbl"
next_routes = [
    f"/_next/data/{build_id}/index.json",
    f"/_next/data/{build_id}/categories.json",
    f"/_next/data/{build_id}/category/pets.json",
    f"/_next/data/{build_id}/category/pets.json?slug=pets",
    f"/_next/data/{build_id}/product/test.json",
    f"/_next/data/{build_id}/categories/pets.json",
]
for path in next_routes:
    try:
        r = client.get(f"{BASE}{path}", headers=headers, timeout=10)
        has = r.status_code == 200 and len(r.content) > 50
        print(f"  [{r.status_code}] {path.replace(build_id, 'BID')} size={len(r.content)} {'DATA!' if has else ''}")
        if has:
            d = r.json()
            pp = d.get("pageProps", {})
            print(f"       pageProps keys: {list(pp.keys())[:10]}")
            if "layouts" in pp:
                layouts = pp["layouts"]
                print(f"       layouts: {len(layouts)} items")
                for l in layouts:
                    if isinstance(l, dict):
                        print(f"         type={l.get('type','?')} name={l.get('name','?')} keys={list(l.keys())[:10]}")
    except:
        pass

# Pattern 5: Check the layouts content more carefully from a category page
print("\n\n--- Deep inspect category page layouts ---")
r = client.get(f"{BASE}/category/pets", headers={
    "Accept": "text/html",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
}, timeout=15)

if r.status_code == 200 and "__NEXT_DATA__" in r.text:
    html = r.text
    nd_start = html.index('__NEXT_DATA__')
    sc_start = html.rfind('<script', 0, nd_start)
    sc_end = html.find('</script>', nd_start)
    j_start = html.index('>', sc_start) + 1
    nd = json.loads(html[j_start:sc_end].strip())
    pp = nd.get("props", {}).get("pageProps", {})

    print(f"  pageProps: {json.dumps(pp, ensure_ascii=False)[:2000]}")

    # Check organizationData and navData in props
    org = nd.get("props", {}).get("organizationData", {})
    nav = nd.get("props", {}).get("navData", {})
    print(f"\n  organizationData keys: {list(org.keys())[:15] if isinstance(org, dict) else type(org)}")
    print(f"  navData type: {type(nav)}, len={len(nav) if isinstance(nav, (list, dict)) else '?'}")

client.close()
print("\n=== DONE ===")
