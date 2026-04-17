#!/usr/bin/env python3
"""Carrefour: Get auth token and fetch products"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, re, time, csv
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
BASE = "https://www.carrefourksa.com"

client = httpx.Client(timeout=25.0, follow_redirects=True)

h = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.8",
}

# Step 1: Check the 400 error messages
print("=" * 60)
print("STEP 1: Check error responses for clues")
print("=" * 60)

r = client.get(f"{BASE}/api/v8/search?keyword=rice&storeId=mafsau&lang=ar&pageSize=5",
    headers={**h, "Accept": "application/json"}, timeout=10)
print(f"  Search 400: {r.text[:300]}")
print(f"  Headers: {dict(r.headers)}")

r = client.get(f"{BASE}/api/v1/menu",
    headers={**h, "Accept": "application/json"}, timeout=10)
print(f"\n  Menu 400: {r.text[:300]}")

r = client.get(f"{BASE}/v1/auto-suggest?keyword=rice&storeId=mafsau&lang=ar",
    headers={**h, "Accept": "application/json"}, timeout=10)
print(f"\n  AutoSuggest 400: {r.text[:300]}")

# Step 2: Get OAuth token (found /v2/oauth/token in JS)
print("\n" + "=" * 60)
print("STEP 2: Get OAuth token")
print("=" * 60)

# Try getting token
token_endpoints = [
    (f"{BASE}/v2/oauth/token", {"grant_type": "client_credentials"}),
    (f"{BASE}/v2/oauth/token", {"grant_type": "anonymous"}),
    (f"{BASE}/api/v2/oauth/token", {"grant_type": "client_credentials"}),
]

token = None
for url, body in token_endpoints:
    for method in ["POST"]:
        try:
            r = client.post(url, data=body, headers={
                **h, "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"
            }, timeout=10)
            print(f"  [{r.status_code}] POST {url.replace(BASE,'')} -> {r.text[:300]}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    token = d.get("access_token", d.get("token", ""))
                    if token:
                        print(f"  TOKEN FOUND: {token[:50]}...")
                except:
                    pass
        except Exception as e:
            print(f"  [ERR] {url.replace(BASE,'')} -> {type(e).__name__}")

# Step 3: Get the main page and extract any tokens/cookies from response
print("\n" + "=" * 60)
print("STEP 3: Extract tokens from page load")
print("=" * 60)

r = client.get(f"{BASE}/mafsau/ar/", headers={**h, "Accept": "text/html"}, timeout=15)
print(f"  Page: {r.status_code}, cookies: {dict(client.cookies)}")

# Check for tokens in HTML
html = r.text
token_patterns = re.findall(r'(?:token|apiKey|clientId|authorization)["\s:=]+["\']([a-zA-Z0-9._-]{20,})["\']', html, re.IGNORECASE)
print(f"  Tokens in HTML: {token_patterns[:5]}")

# Check for config/env variables
config_vars = re.findall(r'(?:window\.|process\.env\.)(\w+)\s*=\s*["\']([^"\']+)["\']', html)
print(f"  Config vars: {config_vars[:10]}")

# Check Set-Cookie headers
for key, value in r.headers.multi_items():
    if key.lower() == 'set-cookie':
        print(f"  Cookie: {value[:100]}")

# Step 4: Try with cookies from page load
print("\n" + "=" * 60)
print("STEP 4: Retry API with session cookies")
print("=" * 60)

session_h = {
    **h,
    "Accept": "application/json",
    "Referer": f"{BASE}/mafsau/ar/",
    "Origin": BASE,
}
if token:
    session_h["Authorization"] = f"Bearer {token}"

endpoints = [
    f"{BASE}/api/v1/menu",
    f"{BASE}/api/v8/search?keyword=rice&storeId=mafsau&lang=ar&pageSize=5",
    f"{BASE}/v1/auto-suggest?keyword=rice&storeId=mafsau&lang=ar",
]

for url in endpoints:
    try:
        r = client.get(url, headers=session_h, timeout=10)
        print(f"  [{r.status_code}] {url.replace(BASE,'')[:60]} size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 100:
            d = r.json()
            print(f"    Keys: {list(d.keys())[:10]}")
            print(f"    Preview: {json.dumps(d, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"  [ERR] -> {type(e).__name__}")

# Step 5: Check for Algolia (many Carrefour sites use Algolia for search)
print("\n" + "=" * 60)
print("STEP 5: Check for Algolia search")
print("=" * 60)

# Search for Algolia keys in HTML/JS
algolia_keys = re.findall(r'["\']([a-f0-9]{32})["\']', html)
algolia_refs = re.findall(r'algolia|algoliasearch', html, re.IGNORECASE)
print(f"  Algolia references: {len(algolia_refs)}")
print(f"  Potential Algolia keys: {algolia_keys[:5]}")

# Check JS bundles for Algolia config
scripts = re.findall(r'src="(https?://[^"]*\.js[^"]*)"', html)
scripts += [f"{BASE}{s}" for s in re.findall(r'src="(/[^"]*\.js[^"]*)"', html)]

for script_url in scripts[:15]:
    try:
        r2 = client.get(script_url, timeout=8)
        if r2.status_code == 200:
            js = r2.text
            if 'algolia' in js.lower():
                print(f"\n  Algolia found in: {script_url.split('/')[-1][:40]}")
                app_ids = re.findall(r'applicationId["\s:=]+["\']([A-Z0-9]+)["\']', js)
                api_keys = re.findall(r'apiKey["\s:=]+["\']([a-f0-9]+)["\']', js)
                index_names = re.findall(r'indexName["\s:=]+["\']([^"\']+)["\']', js)
                print(f"    App IDs: {app_ids[:3]}")
                print(f"    API Keys: {api_keys[:3]}")
                print(f"    Index Names: {index_names[:5]}")

                if app_ids and api_keys:
                    # Try Algolia direct search!
                    algolia_url = f"https://{app_ids[0].lower()}-dsn.algolia.net/1/indexes/{index_names[0] if index_names else '*'}/query"
                    try:
                        r3 = client.post(algolia_url, json={
                            "params": "query=rice&hitsPerPage=5"
                        }, headers={
                            "X-Algolia-Application-Id": app_ids[0],
                            "X-Algolia-API-Key": api_keys[0],
                            "Content-Type": "application/json",
                        }, timeout=10)
                        print(f"    Algolia search: {r3.status_code}, size={len(r3.content)}")
                        if r3.status_code == 200:
                            d = r3.json()
                            print(f"    HITS: {d.get('nbHits', '?')}")
                            hits = d.get("hits", [])
                            if hits:
                                print(f"    First hit keys: {list(hits[0].keys())[:15]}")
                                print(f"    Sample: {json.dumps(hits[0], ensure_ascii=False)[:500]}")
                    except Exception as e:
                        print(f"    Algolia ERR: {e}")
    except:
        pass

client.close()
print("\n=== DONE ===")
