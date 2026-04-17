#!/usr/bin/env python3
"""Carrefour: Use correct app headers from retailer settings"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, re, time, csv
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
BASE = "https://www.carrefourksa.com"

# Don't use cookie jar to avoid conflicts
client = httpx.Client(timeout=25.0, follow_redirects=True)

# From retailer settings: appid=IOS, storeid=mafsau, currency=SAR, env=PROD
app_headers = {
    "Accept": "application/json",
    "User-Agent": "Carrefour/3 CFNetwork/1410.0.3 Darwin/22.6.0",
    "accept-language": "ar",
    "storeid": "mafsau",
    "currency": "SAR",
    "langcode": "ar",
    "appid": "IOS",
    "env": "PROD",
    "userid": "",
    "token": "",
    "mafcountry": "SA",
    "x-appversion": "3.0",
}

# Also try with "appId" capitalization variations
header_sets = [
    {**app_headers},
    {**app_headers, "appId": "IOS"},
    {**app_headers, "app-id": "IOS"},
    {**app_headers, "x-app-id": "IOS"},
    {**app_headers, "x-appid": "IOS", "x-storeid": "mafsau"},
]

print("=" * 60)
print("Carrefour: Testing with app headers")
print("=" * 60)

endpoints = [
    "/api/v1/menu",
    "/api/v8/search?keyword=rice&storeId=mafsau&lang=ar&pageSize=5",
    "/v1/auto-suggest?keyword=rice&storeId=mafsau&lang=ar",
    "/v2/oauth/token",
]

for i, headers in enumerate(header_sets):
    print(f"\n--- Header set {i+1} ---")
    for ep in endpoints:
        try:
            if "oauth" in ep:
                r = client.post(f"{BASE}{ep}",
                    data={"grant_type": "client_credentials"},
                    headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10)
            else:
                r = client.get(f"{BASE}{ep}", headers=headers, timeout=10)
            print(f"  [{r.status_code}] {ep[:50]} size={len(r.content)}")
            if r.status_code == 200 and len(r.content) > 100:
                try:
                    d = r.json()
                    print(f"    Keys: {list(d.keys())[:10]}")
                    print(f"    Preview: {json.dumps(d, ensure_ascii=False)[:500]}")
                except:
                    print(f"    Raw: {r.content[:200]}")
        except:
            pass

# Step 2: Try getting token with app headers
print("\n" + "=" * 60)
print("Step 2: OAuth with app headers")
print("=" * 60)

token = None
for grant in ["client_credentials", "anonymous", "guest"]:
    try:
        r = client.post(f"{BASE}/v2/oauth/token",
            data={"grant_type": grant},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "appid": "IOS",
                "storeid": "mafsau",
                "langcode": "ar",
                "mafcountry": "SA",
                "env": "PROD",
                "User-Agent": "Carrefour/3 CFNetwork/1410.0.3 Darwin/22.6.0",
            }, timeout=10)
        print(f"  [{r.status_code}] grant={grant}: {r.text[:300]}")
        if r.status_code == 200:
            d = r.json()
            token = d.get("access_token", d.get("token", d.get("data", {}).get("token", "")))
            if token:
                print(f"  TOKEN: {token[:60]}...")
                break
    except:
        pass

# Step 3: If got token, use it
if token:
    print(f"\n  Using token to fetch products...")
    auth_h = {
        **app_headers,
        "Authorization": f"Bearer {token}",
    }
    for ep in ["/api/v1/menu", "/api/v8/search?keyword=&storeId=mafsau&lang=ar&pageSize=50"]:
        try:
            r = client.get(f"{BASE}{ep}", headers=auth_h, timeout=15)
            print(f"  [{r.status_code}] {ep[:50]} size={len(r.content)}")
            if r.status_code == 200:
                d = r.json()
                print(f"    {json.dumps(d, ensure_ascii=False)[:500]}")
        except:
            pass

# Step 4: Search JS for exact required headers
print("\n" + "=" * 60)
print("Step 3: Find exact headers from JS")
print("=" * 60)

r = client.get(f"{BASE}/mafsau/ar/", headers={
    "Accept": "text/html", "User-Agent": "Mozilla/5.0"}, timeout=15)
html = r.text
scripts = re.findall(r'src="([^"]*\.js[^"]*)"', html)

for script_url in scripts[:20]:
    if not script_url.startswith('http'):
        script_url = f"{BASE}{script_url}"
    try:
        r2 = client.get(script_url, timeout=8)
        if r2.status_code == 200:
            js = r2.text
            # Search for header configuration
            header_configs = re.findall(r'(?:headers|HEADERS)[^{]*\{([^}]{20,500})\}', js)
            for hc in header_configs:
                if any(k in hc.lower() for k in ['appid', 'storeid', 'langcode', 'mafcountry', 'authorization']):
                    short = script_url.split('/')[-1][:30]
                    print(f"\n  In {short}:")
                    print(f"    {hc[:300]}")
            # Also find specific header value assignments
            appid_vals = re.findall(r'(?:appid|app-id|appId|APP_ID)["\s:=]+["\']([^"\']+)["\']', js, re.IGNORECASE)
            if appid_vals:
                short = script_url.split('/')[-1][:30]
                print(f"\n  In {short}: appId values = {appid_vals[:3]}")
    except:
        pass

client.close()
print("\n=== DONE ===")
