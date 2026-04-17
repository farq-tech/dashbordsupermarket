#!/usr/bin/env python3
"""Creative approaches to crack remaining store APIs"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, time
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

client = httpx.Client(timeout=20.0, follow_redirects=True)

# ============================================================
# 1. LULU - Akinon anonymous token
# ============================================================
print("=" * 60)
print("1. LULU - Akinon Anonymous Token")
print("=" * 60)

LULU = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"
lulu_h = {
    "Accept": "application/json",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "accept-language": "ar;q=1.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
}

# Akinon typically issues tokens via these endpoints
token_endpoints = [
    ("POST", "/users/token/", {}),
    ("POST", "/users/token/", {"grant_type": "anonymous"}),
    ("POST", "/users/anonymous-login/", {}),
    ("POST", "/users/guest/", {}),
    ("POST", "/auth/token/", {}),
    ("POST", "/auth/anonymous/", {}),
    ("POST", "/oauth/token/", {"grant_type": "client_credentials"}),
    ("GET", "/users/token/", None),
    ("POST", "/users/register/", {"is_guest": True}),
    ("POST", "/token/", {}),
    ("POST", "/api-token/", {}),
    ("POST", "/api/v1/token/", {}),
    ("POST", "/api/v1/auth/token/", {}),
]

lulu_token = None
for method, ep, body in token_endpoints:
    try:
        if method == "POST":
            r = client.post(f"{LULU}{ep}", json=body if body else None, headers=lulu_h, timeout=8)
        else:
            r = client.get(f"{LULU}{ep}", headers=lulu_h, timeout=8)
        if r.status_code not in (404, 405) and len(r.content) > 10:
            print(f"  [{r.status_code}] {method} {ep} size={len(r.content)}")
            try:
                d = r.json()
                print(f"    Response: {json.dumps(d, ensure_ascii=False)[:300]}")
                # Look for token in response
                for tk in ["token", "access_token", "key", "auth_token", "access", "Token"]:
                    if tk in d:
                        lulu_token = d[tk]
                        print(f"    TOKEN FOUND: {tk} = {str(lulu_token)[:60]}...")
                        break
                if lulu_token:
                    break
            except:
                pass
    except:
        pass

# Try with content-type form-urlencoded (Akinon often uses this)
if not lulu_token:
    print("\n  Trying form-urlencoded...")
    form_h = {**lulu_h, "Content-Type": "application/x-www-form-urlencoded"}
    form_endpoints = [
        ("/users/token/", ""),
        ("/users/token/", "grant_type=anonymous"),
        ("/users/otp-login/", "phone=+966500000000"),  # Dummy to see error format
    ]
    for ep, body in form_endpoints:
        try:
            r = client.post(f"{LULU}{ep}", content=body, headers=form_h, timeout=8)
            if r.status_code not in (404,) and len(r.content) > 10:
                print(f"  [{r.status_code}] POST {ep} size={len(r.content)}")
                try:
                    d = r.json()
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:300]}")
                except:
                    print(f"    Text: {r.text[:200]}")
        except:
            pass

# If we got a token, try fetching products
if lulu_token:
    print(f"\n  Using token to fetch products...")
    auth_h = {**lulu_h, "Authorization": f"Token {lulu_token}"}
    for ep in ["/products/?limit=50", "/categories/", "/search/?q=rice"]:
        try:
            r = client.get(f"{LULU}{ep}", headers=auth_h, timeout=10)
            print(f"  [{r.status_code}] {ep} size={len(r.content)}")
            if r.status_code == 200:
                d = r.json()
                if isinstance(d, dict):
                    print(f"    Keys: {list(d.keys())[:10]}")
                    for k in ["products", "results", "items", "data", "count"]:
                        if k in d:
                            val = d[k]
                            if isinstance(val, list):
                                print(f"    .{k} = List[{len(val)}]")
                                if val and isinstance(val[0], dict):
                                    print(f"    First keys: {list(val[0].keys())[:12]}")
                                    print(f"    Sample: {json.dumps(val[0], ensure_ascii=False)[:300]}")
                            elif isinstance(val, (int, float)):
                                print(f"    .{k} = {val}")
                    save(f"lulu_products_token.json", d)
        except:
            pass

# Also try: maybe products don't need auth, just the right URL format
print("\n  Trying direct product URLs (no auth)...")
direct_endpoints = [
    "/products/",
    "/products/?limit=50&page=1",
    "/products/?page_size=50",
    "/catalogue/products/",
    "/catalogue/category/",
    "/catalogue/",
    "/widgets/",
    "/widgets/home/",
    "/data-sources/",
    "/data-sources/products/",
    "/content-types/",
    "/landing-pages/",
    "/flat-pages/",
]
for ep in direct_endpoints:
    try:
        r = client.get(f"{LULU}{ep}", headers=lulu_h, timeout=8)
        if r.status_code == 200 and len(r.content) > 100:
            print(f"  [{r.status_code}] {ep} size={len(r.content)}")
            try:
                d = r.json()
                if isinstance(d, dict):
                    print(f"    Keys: {list(d.keys())[:10]}")
                    for k in ["products", "results", "items", "data", "count"]:
                        if k in d:
                            val = d[k]
                            if isinstance(val, list):
                                print(f"    .{k} = List[{len(val)}]")
                elif isinstance(d, list) and d:
                    print(f"    Array[{len(d)}]")
                    if isinstance(d[0], dict):
                        print(f"    First keys: {list(d[0].keys())[:12]}")
                save(f"lulu_direct_{ep.strip('/').replace('/','_')}.json", d)
            except:
                pass
    except:
        pass

# ============================================================
# 2. FARM - Guest session / token
# ============================================================
print("\n" + "=" * 60)
print("2. FARM - Guest Session")
print("=" * 60)

FARM = "https://go.farm.com.sa"
farm_h = {
    "Accept": "application/json",
    "User-Agent": "FarmStores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
    "accept-language": "ar",
    "Content-Type": "application/json",
}

# Try guest login / anonymous token
farm_token_endpoints = [
    ("POST", "/public/api/v1.0/user/login", {"email": "guest@farm.com.sa", "password": "guest"}),
    ("POST", "/public/api/v1.0/user/login", {}),
    ("POST", "/public/api/v1.0/user/guest", {}),
    ("POST", "/public/api/v1.0/auth/guest", {}),
    ("POST", "/public/api/v1.0/auth/token", {}),
    ("GET", "/public/api/v1.0/user/guest", None),
    ("GET", "/public/api/v1.0/home", None),
    ("POST", "/public/api/v1.0/home", {}),
    # Try v2
    ("GET", "/public/api/v2.0/home", None),
    ("GET", "/public/api/v2.0/categories", None),
    ("GET", "/public/api/v2.0/products", None),
    # Try without /public
    ("GET", "/api/v1.0/home", None),
    ("GET", "/api/v1.0/categories", None),
    ("GET", "/api/v1/home", None),
    ("GET", "/api/v1/categories", None),
    ("GET", "/api/v1/products", None),
    # Try with different base
    ("GET", "/api/home", None),
    ("GET", "/api/categories", None),
]

farm_token = None
for method, ep, body in farm_token_endpoints:
    try:
        if method == "POST":
            r = client.post(f"{FARM}{ep}", json=body, headers=farm_h, timeout=8)
        else:
            r = client.get(f"{FARM}{ep}", headers=farm_h, timeout=8)
        if len(r.content) > 10:
            try:
                d = r.json()
                # Skip "route not found" errors
                if isinstance(d, dict) and d.get("message", "").startswith("The route"):
                    continue
                print(f"  [{r.status_code}] {method} {ep} size={len(r.content)}")
                print(f"    Response: {json.dumps(d, ensure_ascii=False)[:300]}")
                # Look for token
                for tk in ["token", "access_token", "api_token", "bearer", "data"]:
                    if tk in d:
                        val = d[tk]
                        if isinstance(val, str) and len(val) > 10:
                            farm_token = val
                            print(f"    TOKEN: {farm_token[:50]}...")
                            break
                        elif isinstance(val, dict) and "token" in val:
                            farm_token = val["token"]
                            print(f"    TOKEN: {farm_token[:50]}...")
                            break
                if farm_token:
                    break
            except:
                if r.status_code not in (401, 403, 404, 500):
                    print(f"  [{r.status_code}] {method} {ep} size={len(r.content)} (not json)")
    except Exception as e:
        err = type(e).__name__
        if "connect" not in err.lower() and "timeout" not in err.lower():
            print(f"  [{err}] {method} {ep}")

# ============================================================
# 3. SADHAN - Find correct store identifier
# ============================================================
print("\n" + "=" * 60)
print("3. SADHAN - Store Identifier")
print("=" * 60)

SADHAN_API = "https://masterapi.witheldokan.com"
sadhan_h = {
    "Accept": "application/json",
    "User-Agent": "Alsadhan%20Stores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
    "Referer": "https://alsadhan.witheldokan.com/",
    "Origin": "https://alsadhan.witheldokan.com",
}

# The error was "Store Not Found" - need correct store identifier
# Try passing store in different ways
sadhan_patterns = [
    # Headers
    ({"store": "alsadhan"}, "/api/home", None),
    ({"store-slug": "alsadhan"}, "/api/home", None),
    ({"x-store": "alsadhan"}, "/api/home", None),
    ({"x-store-slug": "alsadhan"}, "/api/home", None),
    ({"x-subdomain": "alsadhan"}, "/api/home", None),
    ({"subdomain": "alsadhan"}, "/api/home", None),
    ({"host": "alsadhan.witheldokan.com"}, "/api/home", None),
    # Query params
    ({}, "/api/home?store=alsadhan", None),
    ({}, "/api/home?store_slug=alsadhan", None),
    ({}, "/api/home?subdomain=alsadhan", None),
    ({}, "/api/home?domain=alsadhan", None),
    # URL path
    ({}, "/api/alsadhan/home", None),
    ({}, "/api/v1/alsadhan/home", None),
    ({}, "/api/store/alsadhan/home", None),
    ({}, "/api/stores/alsadhan/home", None),
    ({}, "/api/vendor/alsadhan/home", None),
    # POST with body
    ({}, "/api/home", {"store": "alsadhan"}),
    ({}, "/api/home", {"store_slug": "alsadhan"}),
    ({}, "/api/home", {"subdomain": "alsadhan"}),
]

for extra_headers, ep, body in sadhan_patterns:
    try:
        h = {**sadhan_h, **extra_headers}
        if body:
            r = client.post(f"{SADHAN_API}{ep}", json=body, headers=h, timeout=8)
        else:
            r = client.get(f"{SADHAN_API}{ep}", headers=h, timeout=8)
        if r.status_code == 200 and len(r.content) > 50:
            try:
                d = r.json()
                msg = d.get("message", "")
                if "Store Not Found" not in msg and "Referer" not in msg:
                    hdr_info = list(extra_headers.items())[0] if extra_headers else ""
                    print(f"  [{r.status_code}] {ep} headers={hdr_info} size={len(r.content)}")
                    print(f"    Keys: {list(d.keys())[:10]}")
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:300]}")
                    save(f"sadhan_crack.json", d)
                    break
            except:
                pass
    except:
        pass
else:
    # Try the sadhanmarketapi subdomain with store headers
    print("  masterapi didn't work. Trying sadhanmarketapi...")
    SADHAN2 = "https://sadhanmarketapi.witheldokan.com"
    for extra_headers, ep in [
        ({"store": "alsadhan"}, "/api/home"),
        ({"x-store": "alsadhan"}, "/api/home"),
        ({"subdomain": "alsadhan"}, "/api/home"),
        ({}, "/api/home?store=alsadhan"),
    ]:
        try:
            h = {**sadhan_h, **extra_headers}
            r = client.get(f"{SADHAN2}{ep}", headers=h, timeout=10)
            if len(r.content) > 50:
                print(f"  [{r.status_code}] {ep} headers={list(extra_headers.items())} size={len(r.content)}")
                try:
                    d = r.json()
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:200]}")
                except:
                    pass
        except Exception as e:
            err = type(e).__name__
            if "timeout" in err.lower():
                print(f"  [TIMEOUT] sadhanmarketapi - server unreachable")
                break

# ============================================================
# 4. RAMEZ - Alternative routes/domains
# ============================================================
print("\n" + "=" * 60)
print("4. RAMEZ - Alternative approaches")
print("=" * 60)

ramez_h = {
    "Accept": "application/json",
    "apikey": "^~>h2q=m[h=>3?bU/!M'X!m~?4GjKJP{Q@y;~fa3Vjs/M#`8FuB;x[LKwJ&>gNrxBt8!5PZ:9QLuHBUtu{TPc2s]k74]Br?PGe6+NcFUT-8",
    "User-Agent": "Ramez/8 CFNetwork/1404.0.5 Darwin/22.3.0",
    "accept-language": "ar",
    "device_type": "iOS",
    "app_version": "5.9.4",
}

ramez_urls = [
    "https://risteh.com/SA/GroceryStoreApi/api/v9/Home",
    "https://risteh.com/SA/GroceryStoreApi/api/v10/Home",
    "https://risteh.com/SA/GroceryStoreApi/api/v8/Home",
    "https://risteh.com/SA/GroceryStoreApi/api/v7/Home",
    "https://api.risteh.com/SA/GroceryStoreApi/api/v9/Home",
    "https://risteh.com/api/v9/Home",
    "https://ramez.risteh.com/api/v9/Home",
    # Try ramez own domain
    "https://api.ramezgroup.com/api/v9/Home",
    "https://api.ramezonline.com/api/v9/Home",
    "https://ramezonline.com/api/Home",
]

for url in ramez_urls:
    try:
        r = client.get(url, headers=ramez_h, timeout=8)
        if r.status_code != 404 and len(r.content) > 50:
            print(f"  [{r.status_code}] {url.split('//')[1][:50]} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    print(f"    Keys: {list(d.keys())[:10]}")
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:300]}")
                    save("ramez_home.json", d)
                except:
                    pass
    except Exception as e:
        err = type(e).__name__
        if "connect" in err.lower() or "timeout" in err.lower():
            pass  # Skip connection errors silently
        else:
            print(f"  [{err}] {url.split('//')[1][:40]}")

client.close()
print("\n=== DONE ===")
