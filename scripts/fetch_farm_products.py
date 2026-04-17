#!/usr/bin/env python3
"""Farm: Fetch all products with JWT token"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

# Load token
with open("data/farm_auth.json", "r") as f:
    auth = json.load(f)
TOKEN = auth["result"]["token"]

BASE = "https://go.farm.com.sa/public/api/v1.0"
client = httpx.Client(timeout=25.0, follow_redirects=True)
h = {
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}",
    "User-Agent": "FarmStores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
    "accept-language": "ar",
}

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 1. Discover available endpoints
# ============================================================
print("=" * 60)
print("FARM - Authenticated API Exploration")
print("=" * 60)

endpoints = [
    "/home",
    "/categories",
    "/products",
    "/stores",
    "/offers",
    "/brands",
    "/search",
    "/cart",
    "/user/profile",
    "/user/addresses",
    "/banners",
    "/settings",
    "/config",
]

working_endpoints = []
for ep in endpoints:
    try:
        r = client.get(f"{BASE}{ep}", headers=h, timeout=10)
        if len(r.content) > 50:
            try:
                d = r.json()
                msg = str(d)
                if "route" in msg.lower() and "not found" in msg.lower():
                    continue
                print(f"  [{r.status_code}] {ep} size={len(r.content)}")
                if r.status_code == 200:
                    working_endpoints.append(ep)
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        # Explore nested data
                        for k in d:
                            val = d[k]
                            if isinstance(val, list) and val:
                                print(f"    .{k} = List[{len(val)}]")
                                if isinstance(val[0], dict):
                                    print(f"    First keys: {list(val[0].keys())[:15]}")
                                    print(f"    Sample: {json.dumps(val[0], ensure_ascii=False)[:300]}")
                            elif isinstance(val, dict) and val:
                                print(f"    .{k} = Dict keys: {list(val.keys())[:10]}")
                    elif isinstance(d, list) and d:
                        print(f"    Array[{len(d)}]")
                        if isinstance(d[0], dict):
                            print(f"    First keys: {list(d[0].keys())[:15]}")
                            print(f"    Sample: {json.dumps(d[0], ensure_ascii=False)[:300]}")
                    save(f"farm_{ep.strip('/').replace('/','_')}.json", d)
                else:
                    print(f"    Status {r.status_code}: {r.text[:200]}")
            except:
                pass
    except:
        pass

print(f"\n  Working endpoints: {working_endpoints}")

# ============================================================
# 2. If home/categories work, fetch products
# ============================================================
if "/home" in working_endpoints:
    print("\n" + "=" * 60)
    print("FARM - Home data")
    print("=" * 60)

    r = client.get(f"{BASE}/home", headers=h, timeout=15)
    d = r.json()
    if isinstance(d, dict):
        # Look for categories, products, banners
        for k in d:
            val = d[k]
            if isinstance(val, list) and val:
                print(f"  .{k} = List[{len(val)}]")
                if isinstance(val[0], dict):
                    print(f"    Keys: {list(val[0].keys())[:15]}")

        # Extract categories from home
        categories = d.get("categories", d.get("data", {}).get("categories", []) if isinstance(d.get("data"), dict) else [])
        if isinstance(categories, list) and categories:
            print(f"\n  Found {len(categories)} categories!")
            save(f"farm_categories_{ts}.json", categories)

            # Fetch products for each category
            all_products = []
            seen_ids = set()

            for cat in categories:
                cat_id = cat.get("id") or cat.get("Id") or cat.get("category_id")
                cat_name = cat.get("name") or cat.get("title") or ""
                if not cat_id:
                    continue

                # Try different product endpoints
                for pep in [
                    f"/products?category_id={cat_id}",
                    f"/products?categoryId={cat_id}",
                    f"/categories/{cat_id}/products",
                    f"/category/{cat_id}/products",
                ]:
                    try:
                        r2 = client.get(f"{BASE}{pep}", headers=h, timeout=10)
                        if r2.status_code == 200 and len(r2.content) > 50:
                            d2 = r2.json()
                            msg = str(d2)
                            if "route" in msg.lower() and "not found" in msg.lower():
                                continue

                            products = []
                            if isinstance(d2, list):
                                products = d2
                            elif isinstance(d2, dict):
                                products = d2.get("products", d2.get("data", d2.get("items", d2.get("result", []))))
                                if isinstance(products, dict):
                                    products = products.get("data", products.get("products", products.get("items", [])))

                            if isinstance(products, list) and products:
                                new = 0
                                for p in products:
                                    pid = p.get("id") or p.get("Id") or p.get("product_id")
                                    if pid and pid not in seen_ids:
                                        seen_ids.add(pid)
                                        p["_category_id"] = cat_id
                                        p["_category_name"] = cat_name
                                        all_products.append(p)
                                        new += 1
                                if new > 0:
                                    print(f"    Cat {cat_id} ({cat_name[:25]}): +{new} (total: {len(all_products)})")
                                break  # Found working endpoint pattern
                    except:
                        pass

                # Also check subcategories
                subs = cat.get("sub_categories", cat.get("children", cat.get("subcategories", [])))
                if isinstance(subs, list):
                    for sub in subs:
                        sub_id = sub.get("id") or sub.get("Id")
                        sub_name = sub.get("name") or sub.get("title") or ""
                        if not sub_id:
                            continue
                        for pep in [
                            f"/products?category_id={sub_id}",
                            f"/products?categoryId={sub_id}",
                        ]:
                            try:
                                r3 = client.get(f"{BASE}{pep}", headers=h, timeout=10)
                                if r3.status_code == 200 and len(r3.content) > 100:
                                    d3 = r3.json()
                                    if "route" in str(d3).lower() and "not found" in str(d3).lower():
                                        continue
                                    products = d3 if isinstance(d3, list) else d3.get("products", d3.get("data", []))
                                    if isinstance(products, list) and products:
                                        new = 0
                                        for p in products:
                                            pid = p.get("id") or p.get("Id")
                                            if pid and pid not in seen_ids:
                                                seen_ids.add(pid)
                                                p["_category_id"] = sub_id
                                                p["_category_name"] = sub_name
                                                all_products.append(p)
                                                new += 1
                                        if new > 0:
                                            print(f"      Sub {sub_id} ({sub_name[:20]}): +{new} (total: {len(all_products)})")
                                        break
                            except:
                                pass

                time.sleep(0.2)

            print(f"\n  FARM TOTAL: {len(all_products)} products")
            if all_products:
                save(f"farm_products_{ts}.json", all_products)
                print(f"  Saved to data/farm_products_{ts}.json")
                if isinstance(all_products[0], dict):
                    print(f"  Product keys: {list(all_products[0].keys())[:15]}")
                    print(f"  Sample: {json.dumps(all_products[0], ensure_ascii=False)[:400]}")

                # Export CSV
                fn = list(all_products[0].keys())
                with open(f"data/farm_products.csv", "w", encoding="utf-8-sig", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=fn, extrasaction="ignore")
                    w.writeheader()
                    w.writerows(all_products)
                print(f"  CSV: data/farm_products.csv ({len(all_products)} rows)")

client.close()
print("\n=== DONE ===")
