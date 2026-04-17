#!/usr/bin/env python3
"""Farm: Try every possible way to send Customer Location"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os
import httpx

os.makedirs("data", exist_ok=True)

# Load token
with open("data/farm_auth.json", "r") as f:
    auth = json.load(f)
TOKEN = auth["result"]["token"]

BASE = "https://go.farm.com.sa/public/api/v1.0"
client = httpx.Client(timeout=15.0, follow_redirects=True)

LAT = "24.7136"
LNG = "46.6753"

def try_request(desc, method, url, headers=None, params=None, json_body=None, data=None):
    h = {
        "Accept": "application/json",
        "Authorization": f"Bearer {TOKEN}",
        "accept-encoding": "deflate",
        "accept-language": "en-US,en;q=0.9",
    }
    if headers:
        h.update(headers)
    try:
        if method == "GET":
            r = client.get(url, headers=h, params=params, timeout=10)
        elif method == "POST":
            r = client.post(url, headers=h, params=params, json=json_body, data=data, timeout=10)
        elif method == "PUT":
            r = client.put(url, headers=h, params=params, json=json_body, data=data, timeout=10)
        elif method == "PATCH":
            r = client.patch(url, headers=h, params=params, json=json_body, data=data, timeout=10)

        text = r.text[:300]
        try:
            d = r.json()
            success = d.get("status", {}).get("success", False) if isinstance(d.get("status"), dict) else False
            msg = d.get("status", {}).get("otherTxt", "") if isinstance(d.get("status"), dict) else ""
            if success or ("location" not in msg.lower() and "route" not in text.lower()):
                print(f"  [OK {r.status_code}] {desc}")
                print(f"    Response: {text}")
                return d
            elif "location" in msg.lower():
                pass  # Still needs location, skip
            else:
                print(f"  [{r.status_code}] {desc}: {msg or text[:100]}")
        except:
            if r.status_code == 200 and len(r.content) > 100:
                print(f"  [{r.status_code}] {desc}: non-JSON {len(r.content)}b")
    except Exception as e:
        pass
    return None

# ============================================================
# 1. Try different query param names for /home
# ============================================================
print("=" * 60)
print("1. Query param variations for /home")
print("=" * 60)

param_combos = [
    {"lat": LAT, "lng": LNG},
    {"latitude": LAT, "longitude": LNG},
    {"Lat": LAT, "Lng": LNG},
    {"Latitude": LAT, "Longitude": LNG},
    {"customer_lat": LAT, "customer_lng": LNG},
    {"location_lat": LAT, "location_lng": LNG},
    {"lat": LAT, "long": LNG},
    {"lat": LAT, "lon": LNG},
    {"lat": LAT, "lng": LNG, "city_id": "1"},
    {"lat": LAT, "lng": LNG, "store_id": "1"},
    {"lat": LAT, "lng": LNG, "branch_id": "1"},
]

for params in param_combos:
    desc = f"GET /home?{'&'.join(f'{k}={v}' for k,v in params.items())}"
    try_request(desc, "GET", f"{BASE}/home", params=params)

# ============================================================
# 2. Try location as custom headers
# ============================================================
print("\n" + "=" * 60)
print("2. Location as headers")
print("=" * 60)

header_combos = [
    {"latitude": LAT, "longitude": LNG},
    {"Latitude": LAT, "Longitude": LNG},
    {"X-Latitude": LAT, "X-Longitude": LNG},
    {"x-latitude": LAT, "x-longitude": LNG},
    {"X-Customer-Latitude": LAT, "X-Customer-Longitude": LNG},
    {"customer-latitude": LAT, "customer-longitude": LNG},
    {"X-Location": f"{LAT},{LNG}"},
    {"Location": f"{LAT},{LNG}"},
    {"X-Location-Lat": LAT, "X-Location-Lng": LNG},
    {"lat": LAT, "lng": LNG},
    {"X-Lat": LAT, "X-Lng": LNG},
    {"User-Latitude": LAT, "User-Longitude": LNG},
    {"x-lat": LAT, "x-lng": LNG},
    {"x-user-lat": LAT, "x-user-lng": LNG},
    {"X-City-Id": "1"},
    {"X-Store-Id": "1"},
    {"X-Branch-Id": "1"},
    {"city_id": "1"},
    {"store_id": "1"},
    {"branch-id": "1"},
]

for hdrs in header_combos:
    desc = f"GET /home headers={hdrs}"
    try_request(desc, "GET", f"{BASE}/home", headers=hdrs)

# ============================================================
# 3. Try setting user location/address first
# ============================================================
print("\n" + "=" * 60)
print("3. Set user location endpoints")
print("=" * 60)

location_endpoints = [
    "/user/location",
    "/user/set-location",
    "/user/update-location",
    "/user/address",
    "/user/addresses",
    "/user/address/add",
    "/user/store",
    "/user/select-store",
    "/user/set-store",
    "/location",
    "/set-location",
    "/store/select",
    "/stores/nearest",
    "/stores/select",
    "/user/city",
    "/cities",
    "/branches",
    "/nearest-store",
]

location_bodies = [
    {"lat": float(LAT), "lng": float(LNG)},
    {"latitude": float(LAT), "longitude": float(LNG)},
    {"lat": LAT, "lng": LNG, "city": "Riyadh"},
    {"lat": LAT, "lng": LNG, "city_id": 1},
    {"address": "Riyadh", "lat": float(LAT), "lng": float(LNG)},
    {"location": {"lat": float(LAT), "lng": float(LNG)}},
]

for ep in location_endpoints:
    for body in location_bodies[:2]:  # Try first 2 body formats
        for method in ["POST", "PUT"]:
            desc = f"{method} {ep} body={list(body.keys())}"
            result = try_request(desc, method, f"{BASE}{ep}", json_body=body)
            if result:
                # If we successfully set location, try /home again
                print("  >>> Trying /home after setting location...")
                try_request("GET /home (after set)", "GET", f"{BASE}/home")

    # Also try GET
    desc = f"GET {ep}?lat={LAT}&lng={LNG}"
    result = try_request(desc, "GET", f"{BASE}{ep}", params={"lat": LAT, "lng": LNG})
    if result:
        print(f"  >>> Got data from {ep}!")

# ============================================================
# 4. Try with User-Agent from iOS app
# ============================================================
print("\n" + "=" * 60)
print("4. With exact Farm iOS app User-Agent + variations")
print("=" * 60)

ua_combos = [
    "FarmStores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
    "FarmStores/2 CFNetwork/1404.0.5 Darwin/22.3.0",
    "Farm Stores/1.0 (com.farm.stores; build:1; iOS 16.3.1) Alamofire/5.6.4",
    "okhttp/4.10.0",
]

for ua in ua_combos:
    desc = f"GET /home UA={ua[:30]}..."
    try_request(desc, "GET", f"{BASE}/home",
                headers={"User-Agent": ua, "latitude": LAT, "longitude": LNG},
                params={"lat": LAT, "lng": LNG})

# ============================================================
# 5. Try stores endpoint (maybe we need store_id first)
# ============================================================
print("\n" + "=" * 60)
print("5. Discover stores")
print("=" * 60)

store_endpoints = [
    "/stores",
    "/store",
    "/branches",
    "/branch",
    "/user/nearest-store",
    "/nearest-store",
    "/stores/nearest",
]

for ep in store_endpoints:
    desc = f"GET {ep}?lat={LAT}&lng={LNG}"
    result = try_request(desc, "GET", f"{BASE}{ep}",
                         params={"lat": LAT, "lng": LNG},
                         headers={"latitude": LAT, "longitude": LNG})
    if result:
        # Save and analyze
        with open(f"data/farm_stores.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  Saved stores data!")

        # Extract store IDs
        stores = result if isinstance(result, list) else result.get("data", result.get("result", result.get("stores", [])))
        if isinstance(stores, list):
            for s in stores[:5]:
                if isinstance(s, dict):
                    sid = s.get("id", s.get("Id", s.get("store_id", "")))
                    sname = s.get("name", s.get("title", ""))
                    print(f"    Store {sid}: {sname}")

# ============================================================
# 6. Try form-urlencoded body for /home
# ============================================================
print("\n" + "=" * 60)
print("6. Form-urlencoded body for /home (POST/PUT)")
print("=" * 60)

form_bodies = [
    f"lat={LAT}&lng={LNG}",
    f"latitude={LAT}&longitude={LNG}",
    f"lat={LAT}&lng={LNG}&city_id=1",
    f"lat={LAT}&lng={LNG}&store_id=1",
]

for fb in form_bodies:
    for method in ["POST", "PUT"]:
        desc = f"{method} /home form={fb[:40]}"
        h = {
            "Accept": "application/json",
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded",
            "accept-encoding": "deflate",
            "accept-language": "en-US,en;q=0.9",
        }
        try:
            if method == "POST":
                r = client.post(f"{BASE}/home", headers=h, content=fb, timeout=10)
            else:
                r = client.put(f"{BASE}/home", headers=h, content=fb, timeout=10)
            text = r.text[:300]
            if "location" not in text.lower() and "not supported" not in text.lower():
                print(f"  [{r.status_code}] {desc}: {text}")
        except:
            pass

# ============================================================
# 7. Try with different endpoints that might work with location
# ============================================================
print("\n" + "=" * 60)
print("7. Other endpoints with location")
print("=" * 60)

for ep in ["/products", "/categories", "/offers", "/brands", "/search", "/banners", "/settings"]:
    for loc_method in ["params", "headers"]:
        if loc_method == "params":
            desc = f"GET {ep}?lat&lng"
            result = try_request(desc, "GET", f"{BASE}{ep}",
                                 params={"lat": LAT, "lng": LNG})
        else:
            desc = f"GET {ep} h:lat,lng"
            result = try_request(desc, "GET", f"{BASE}{ep}",
                                 headers={"latitude": LAT, "longitude": LNG})
        if result:
            with open(f"data/farm_{ep.strip('/')}.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"  >>> Saved farm_{ep.strip('/')}.json!")

# ============================================================
# 8. Try user profile and addresses
# ============================================================
print("\n" + "=" * 60)
print("8. User profile & addresses")
print("=" * 60)

for ep in ["/user/profile", "/user/addresses", "/user/orders", "/user/favorites"]:
    desc = f"GET {ep}"
    result = try_request(desc, "GET", f"{BASE}{ep}")
    if result:
        with open(f"data/farm_{ep.replace('/', '_').strip('_')}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

# ============================================================
# 9. Add address for user, then try /home
# ============================================================
print("\n" + "=" * 60)
print("9. Add address then try /home")
print("=" * 60)

address_bodies = [
    {
        "title": "Home",
        "lat": float(LAT),
        "lng": float(LNG),
        "address": "Riyadh, Saudi Arabia",
        "city": "Riyadh",
        "city_id": 1,
    },
    {
        "name": "Home",
        "latitude": float(LAT),
        "longitude": float(LNG),
        "address": "Riyadh",
    },
    {
        "title": "Home",
        "latitude": float(LAT),
        "longitude": float(LNG),
        "address_line": "Riyadh",
        "city_id": 1,
        "is_default": 1,
    },
]

for body in address_bodies:
    desc = f"POST /user/addresses body={list(body.keys())[:4]}"
    result = try_request(desc, "POST", f"{BASE}/user/addresses", json_body=body)
    if result:
        print("  >>> Address added! Trying /home...")
        try_request("GET /home (after addr)", "GET", f"{BASE}/home")

client.close()
print("\n=== DONE ===")
