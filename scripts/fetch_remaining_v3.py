#!/usr/bin/env python3
"""Check Carrefour embedded data, Sadhan response, Spar website"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, re
import httpx

os.makedirs("data", exist_ok=True)
client = httpx.Client(timeout=20.0, follow_redirects=True)

# ============================================================
# 1. CARREFOUR - Check for embedded product data in 706KB HTML
# ============================================================
print("=" * 60)
print("1. CARREFOUR - Checking embedded data")
print("=" * 60)
r = client.get("https://www.carrefourksa.com/mafsau/ar/", headers={
    "Accept": "text/html", "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"}, timeout=15)

html = r.text
print(f"  Size: {len(html)}")

# Check for __NEXT_DATA__, __NUXT__, or other SSR data
for pattern in ["__NEXT_DATA__", "__NUXT__", "window.__INITIAL_STATE__", "window.__APP_STATE__",
                "window.__PRELOADED_STATE__", "window.__data", "window.__props"]:
    if pattern in html:
        print(f"  FOUND: {pattern}")
        idx = html.index(pattern)
        print(f"    Context: {html[idx:idx+200]}")

# Look for <script type="application/json">
json_scripts = re.findall(r'<script[^>]*type="application/(?:json|ld\+json)"[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"  JSON scripts: {len(json_scripts)}")
for i, js in enumerate(json_scripts):
    if len(js) > 100:
        try:
            d = json.loads(js)
            print(f"    Script {i}: {len(js)} bytes, keys={list(d.keys())[:10] if isinstance(d, dict) else type(d)}")
        except:
            print(f"    Script {i}: {len(js)} bytes (parse failed)")

# Look for mafretailproxy API calls
api_refs = set(re.findall(r'https?://[^\s"\'\\]+mafretailproxy[^\s"\'\\]+', html))
print(f"\n  MAF Retail Proxy URLs: {len(api_refs)}")
for a in sorted(api_refs)[:10]:
    print(f"    {a}")

# Try MAF retail proxy API
print("\n  --- MAF Retail Proxy API ---")
proxy_bases = set()
for a in api_refs:
    base = re.match(r'(https?://[^/]+)', a)
    if base:
        proxy_bases.add(base.group(1))
print(f"  Proxy bases: {proxy_bases}")

for base in proxy_bases:
    for p in ["/api/categories", "/api/products", "/v1/categories", "/v1/products",
              "/api/v1/categories", "/api/v1/products", "/bff/categories", "/bff/products"]:
        try:
            r2 = client.get(f"{base}{p}", headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0",
                "Origin": "https://www.carrefourksa.com",
            }, timeout=5)
            if r2.status_code not in (404, 403, 405) and len(r2.content) > 50:
                print(f"    [{r2.status_code}] {base.split('//')[1]}{p} size={len(r2.content)}")
        except:
            pass

# Try BFF pattern (Backend for Frontend)
print("\n  --- BFF/GraphQL ---")
bff_urls = set(re.findall(r'https?://[^\s"\'\\]+(?:bff|graphql|gateway)[^\s"\'\\]*', html))
for a in sorted(bff_urls)[:5]:
    print(f"    BFF: {a}")

# Check for any product-like JSON embedded
product_json = re.findall(r'"products?":\s*\[', html)
category_json = re.findall(r'"categories?":\s*\[', html)
print(f"\n  Embedded 'product(s)' arrays: {len(product_json)}")
print(f"  Embedded 'category(ies)' arrays: {len(category_json)}")

# ============================================================
# 2. SADHAN - Check what the 8333 byte response contains
# ============================================================
print("\n" + "=" * 60)
print("2. SADHAN - Check response content")
print("=" * 60)
try:
    r = client.get("https://alsadhan.witheldokan.com/api/home", headers={
        "Accept": "application/json", "User-Agent": "Mozilla/5.0"}, timeout=10)
    print(f"  Status: {r.status_code}, size={len(r.content)}")
    print(f"  Content-Type: {r.headers.get('content-type')}")
    print(f"  First 500 bytes: {r.text[:500]}")
    # Is it HTML?
    if "<html" in r.text.lower() or "<!doctype" in r.text.lower():
        print("  -> It's HTML, not JSON API")
        if "__NEXT_DATA__" in r.text:
            print("  -> Has __NEXT_DATA__!")
    else:
        try:
            d = r.json()
            print(f"  JSON: {json.dumps(d, ensure_ascii=False)[:500]}")
        except:
            print("  -> Not valid JSON")
except Exception as e:
    print(f"  ERR: {e}")

# ============================================================
# 3. SPAR - Check 24KB website
# ============================================================
print("\n" + "=" * 60)
print("3. SPAR - Check website")
print("=" * 60)
try:
    r = client.get("https://spar.sa", headers={
        "Accept": "text/html", "User-Agent": "Mozilla/5.0"}, timeout=10)
    print(f"  Status: {r.status_code}, size={len(r.content)}")
    # Check for app/store
    if "spar" in r.text.lower():
        # Find API URLs
        apis = set(re.findall(r'https?://[^\s"\'<>]+', r.text))
        api_like = [a for a in apis if any(x in a.lower() for x in ['api', 'product', 'categor', 'store'])]
        print(f"  API-like URLs:")
        for a in sorted(api_like)[:10]:
            print(f"    {a}")
        # Check for app store links
        store_links = [a for a in apis if 'play.google' in a or 'apps.apple' in a or 'app' in a.lower()]
        for a in store_links[:5]:
            print(f"  App: {a}")
except Exception as e:
    print(f"  ERR: {e}")

# ============================================================
# 4. Try Carrefour proper BFF/API
# ============================================================
print("\n" + "=" * 60)
print("4. CARREFOUR - Try product API patterns")
print("=" * 60)

# MAF uses a specific API structure. Let me check the JS bundles
r = client.get("https://www.carrefourksa.com/mafsau/ar/", headers={
    "Accept": "text/html", "User-Agent": "Mozilla/5.0"}, timeout=15)
html = r.text

# Find script src for main bundle
scripts = re.findall(r'src="([^"]*\.js[^"]*)"', html)
print(f"  JS bundles: {len(scripts)}")

# Check first few for API patterns
api_patterns = set()
for script_url in scripts[:10]:
    if not script_url.startswith('http'):
        script_url = f"https://www.carrefourksa.com{script_url}"
    try:
        r2 = client.get(script_url, timeout=8)
        if r2.status_code == 200:
            js = r2.text
            # Find API base URLs
            matches = re.findall(r'["\'](https?://[^"\']+(?:api|bff|gateway|graphql)[^"\']*)["\']', js)
            matches += re.findall(r'["\'](/api/[^"\']{3,})["\']', js)
            for m in matches:
                api_patterns.add(m)
    except:
        pass

print(f"\n  API patterns from JS:")
for p in sorted(api_patterns):
    print(f"    {p}")

# Try the discovered APIs
for url in sorted(api_patterns):
    if not url.startswith('http'):
        url = f"https://www.carrefourksa.com{url}"
    if 'product' in url.lower() or 'categor' in url.lower() or 'search' in url.lower():
        try:
            r2 = client.get(url, headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0",
            }, timeout=5)
            if r2.status_code == 200 and len(r2.content) > 50:
                print(f"  [{r2.status_code}] {url[:80]} size={len(r2.content)} DATA!")
                try:
                    d = r2.json()
                    print(f"    Preview: {json.dumps(d, ensure_ascii=False)[:300]}")
                except:
                    pass
        except:
            pass

client.close()
print("\n=== DONE ===")
