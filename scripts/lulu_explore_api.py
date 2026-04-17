#!/usr/bin/env python3
"""Lulu: Explore Akinon API - find products without auth"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

LULU = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"
client = httpx.Client(timeout=20.0, follow_redirects=True)

h = {
    "Accept": "application/json",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
    "accept-language": "ar;q=1.0",
}

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 1. Get stores (already know this works)
# ============================================================
print("=" * 60)
print("1. LULU Stores")
print("=" * 60)

r = client.get(f"{LULU}/stores/", headers=h, timeout=15)
stores_data = r.json()
print(f"  Stores count: {stores_data.get('count', 0)}")

# Find SA stores
sa_stores = [s for s in stores_data.get("results", []) if "sa" in str(s).lower() or "saudi" in str(s).lower() or "riyadh" in str(s).lower() or "الرياض" in str(s).lower()]
riyadh_stores = [s for s in stores_data.get("results", []) if "riyadh" in str(s).lower() or "الرياض" in str(s).lower()]
print(f"  SA stores: {len(sa_stores)}, Riyadh: {len(riyadh_stores)}")

# Get a store pk for Riyadh
if riyadh_stores:
    store = riyadh_stores[0]
    print(f"  First Riyadh store: pk={store.get('pk')} name={store.get('name')}")
    store_pk = store.get("pk")
else:
    # Just use any store
    store_pk = stores_data["results"][0]["pk"] if stores_data.get("results") else None
    print(f"  Using first store: pk={store_pk}")

save("lulu_stores.json", stores_data)

# ============================================================
# 2. Try getting config
# ============================================================
print("\n" + "=" * 60)
print("2. Config")
print("=" * 60)

r = client.get(f"{LULU}/config/", headers=h, timeout=10)
config = r.json()
print(f"  Country: {config.get('country')}")
print(f"  Currencies: {config.get('available_currencies')}")
print(f"  Phone regex: {config.get('user_phone_regex', '')[:60]}")
save("lulu_config.json", config)

# ============================================================
# 3. Explore all Akinon standard endpoints
# ============================================================
print("\n" + "=" * 60)
print("3. Discover Akinon endpoints")
print("=" * 60)

# Standard Akinon e-commerce endpoints
endpoints = [
    # Product endpoints
    "/products/",
    "/products/?limit=10",
    "/products/?format=json",
    f"/products/?store={store_pk}",
    "/product/",

    # Category endpoints
    "/categories/",
    "/categories/tree/",
    "/category/",
    "/category/tree/",

    # Widget/Data source endpoints (common in Akinon)
    "/widgets/",
    "/widgets/home/",
    "/widgets/homepage/",
    "/data-sources/",
    "/data-source/",

    # Search
    "/search/",
    "/search/?q=milk",
    "/search/products/",
    "/search/products/?q=milk",
    "/search/auto-complete/?q=milk",

    # Catalogue
    "/catalogue/",
    "/catalogue/products/",
    "/catalogue/categories/",
    "/catalog/",
    "/catalog/products/",

    # Offers/promotions
    "/offers/",
    "/promotions/",
    "/campaigns/",
    "/discounts/",

    # Content
    "/pages/",
    "/flat-pages/",
    "/content/",
    "/banners/",
    "/sliders/",

    # Misc
    "/channels/",
    "/attributes/",
    "/brands/",
    "/options/",
    "/option-items/",

    # Basket (anon)
    "/baskets/",
    "/basket/",

    # Addresses/Cities
    "/addresses/",
    "/cities/",
    "/districts/",
    "/townships/",
    "/countries/",

    # Order
    "/orders/",

    # Payment
    "/payment/",
    "/payment-options/",

    # Slots
    "/slots/",
    "/delivery-options/",

    # Store specific
    f"/stores/{store_pk}/",
    f"/stores/{store_pk}/products/",
    f"/stores/{store_pk}/categories/",
]

working = {}
for ep in endpoints:
    try:
        r = client.get(f"{LULU}{ep}", headers=h, timeout=10)
        if r.status_code == 200 and len(r.content) > 20:
            try:
                d = r.json()
                text = json.dumps(d, ensure_ascii=False)[:200]

                # Determine data type
                if isinstance(d, dict):
                    count = d.get("count", 0)
                    results = d.get("results", [])
                    if count or results:
                        print(f"  [200] {ep}: count={count} results={len(results)}")
                        if results and isinstance(results[0], dict):
                            print(f"    Keys: {list(results[0].keys())[:12]}")
                        working[ep] = d
                    else:
                        keys = list(d.keys())[:10]
                        if len(keys) > 1:
                            print(f"  [200] {ep}: {keys}")
                            working[ep] = d
                elif isinstance(d, list):
                    print(f"  [200] {ep}: Array[{len(d)}]")
                    if d and isinstance(d[0], dict):
                        print(f"    Keys: {list(d[0].keys())[:12]}")
                    working[ep] = d
            except:
                pass
        elif r.status_code not in (404, 405, 403, 500, 301, 302):
            print(f"  [{r.status_code}] {ep}: {r.text[:100]}")
    except:
        pass

# Save all working endpoints
for ep, data in working.items():
    fname = f"lulu_{ep.strip('/').replace('/','_').replace('?','_')[:40]}.json"
    save(fname, data)

# ============================================================
# 4. Deep explore widgets (Akinon's main data delivery)
# ============================================================
print("\n" + "=" * 60)
print("4. Widgets deep explore")
print("=" * 60)

if "/widgets/" in working:
    widgets = working["/widgets/"]
    results = widgets.get("results", []) if isinstance(widgets, dict) else widgets
    if isinstance(results, list):
        print(f"  Found {len(results)} widgets")
        for w in results[:20]:
            if isinstance(w, dict):
                slug = w.get("slug", w.get("name", ""))
                pk = w.get("pk", w.get("id", ""))
                wtype = w.get("widget_type", w.get("type", ""))
                print(f"    Widget: pk={pk} slug={slug} type={wtype}")

                # Fetch widget data
                for wurl in [f"/widgets/{slug}/", f"/widgets/{pk}/"]:
                    try:
                        r = client.get(f"{LULU}{wurl}", headers=h, timeout=10)
                        if r.status_code == 200 and len(r.content) > 50:
                            wd = r.json()
                            save(f"lulu_widget_{slug or pk}.json", wd)

                            # Check for products in widget data
                            if isinstance(wd, dict):
                                for k in wd:
                                    val = wd[k]
                                    if isinstance(val, list) and val and isinstance(val[0], dict):
                                        keys = list(val[0].keys())
                                        if any(pk in keys for pk in ["price", "retail_price", "product", "name"]):
                                            print(f"      {wurl} .{k}: {len(val)} items with product data!")
                            break
                    except:
                        pass

# ============================================================
# 5. Try products with different params
# ============================================================
print("\n" + "=" * 60)
print("5. Products with various params")
print("=" * 60)

product_urls = [
    "/products/?limit=50&offset=0",
    "/products/?page=1&page_size=50",
    "/products/?ordering=-created_date",
    "/products/?in_stock=true",
    "/products/?search=milk",
    "/products/?search=حليب",
    f"/products/?store={store_pk}&limit=50",
    "/products/?category=1",
    "/products/?category_id=1",
    "/products/?is_active=true&limit=50",
    "/products/?format=json&limit=50",
]

for url in product_urls:
    try:
        r = client.get(f"{LULU}{url}", headers=h, timeout=15)
        if r.status_code == 200 and len(r.content) > 50:
            d = r.json()
            if isinstance(d, dict):
                count = d.get("count", 0)
                results = d.get("results", [])
                if count or len(results) > 0:
                    print(f"  [200] {url}: count={count} results={len(results)}")
                    if results and isinstance(results[0], dict):
                        print(f"    Keys: {list(results[0].keys())[:15]}")
                        print(f"    Sample: {json.dumps(results[0], ensure_ascii=False)[:300]}")
                    save(f"lulu_products_result.json", d)
                    break
            elif isinstance(d, list) and d:
                print(f"  [200] {url}: Array[{len(d)}]")
                save(f"lulu_products_result.json", d)
                break
        elif r.status_code != 404:
            print(f"  [{r.status_code}] {url}: {r.text[:100]}")
    except:
        pass

# ============================================================
# 6. Try search autocomplete and search
# ============================================================
print("\n" + "=" * 60)
print("6. Search")
print("=" * 60)

search_urls = [
    "/search/?q=milk&limit=20",
    "/search/?q=حليب&limit=20",
    "/search/products/?q=milk&limit=20",
    "/search/auto-complete/?q=milk",
    "/search/auto-complete/?q=حليب",
    "/search/suggestions/?q=milk",
    "/search-auto-complete/?q=milk",
    "/autocomplete/?q=milk",
]

for url in search_urls:
    try:
        r = client.get(f"{LULU}{url}", headers=h, timeout=10)
        if r.status_code == 200 and len(r.content) > 20:
            d = r.json()
            text = json.dumps(d, ensure_ascii=False)[:300]
            print(f"  [200] {url}")
            print(f"    {text}")
            save(f"lulu_search_{url.split('?')[0].strip('/').replace('/','_')}.json", d)
        elif r.status_code not in (404, 405):
            print(f"  [{r.status_code}] {url}: {r.text[:80]}")
    except:
        pass

# ============================================================
# 7. Try Akinon data-source endpoints (widgets with data)
# ============================================================
print("\n" + "=" * 60)
print("7. Data sources")
print("=" * 60)

for i in range(1, 30):
    try:
        r = client.get(f"{LULU}/data-sources/{i}/", headers=h, timeout=8)
        if r.status_code == 200 and len(r.content) > 50:
            d = r.json()
            name = d.get("name", d.get("slug", f"ds_{i}"))
            print(f"  DS {i}: {name}")
            save(f"lulu_ds_{i}.json", d)

            # Check for product data
            if isinstance(d, dict):
                for k in d:
                    val = d[k]
                    if isinstance(val, list) and val and isinstance(val[0], dict):
                        print(f"    .{k}: Array[{len(val)}] keys={list(val[0].keys())[:10]}")
    except:
        pass

client.close()
print("\n=== DONE ===")
