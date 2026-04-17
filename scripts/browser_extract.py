#!/usr/bin/env python3
"""Use Playwright to extract products from Carrefour, Lulu, and other stores"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time, re
from datetime import datetime
from playwright.sync_api import sync_playwright

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

all_store_products = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        locale="ar-SA",
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    )

    # Intercept API responses
    api_responses = []

    def handle_response(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if "json" in ct and response.status == 200:
            if any(k in url.lower() for k in ["product", "search", "categor", "menu", "catalog"]):
                try:
                    data = response.json()
                    api_responses.append({"url": url, "data": data, "size": len(response.body())})
                except:
                    pass

    # ============================================================
    # 1. CARREFOUR
    # ============================================================
    print("=" * 60)
    print("1. CARREFOUR KSA (Playwright)")
    print("=" * 60)

    page = context.new_page()
    page.on("response", handle_response)
    api_responses.clear()

    try:
        # Navigate to search page
        print("  Loading search page...")
        page.goto("https://www.carrefourksa.com/mafsau/ar/v4/search?keyword=rice&pageSize=60", timeout=30000)
        page.wait_for_timeout(5000)  # Wait for API calls

        print(f"  Intercepted {len(api_responses)} API responses")
        for resp in api_responses:
            url = resp["url"]
            data = resp["data"]
            print(f"    {url[:80]} size={resp['size']}")
            if isinstance(data, dict):
                print(f"      Keys: {list(data.keys())[:10]}")
                for k in ["products", "items", "results", "data", "hits", "numFound"]:
                    if k in data:
                        val = data[k]
                        if isinstance(val, list):
                            print(f"      .{k} = List[{len(val)}]")
                            if val and isinstance(val[0], dict):
                                print(f"      First keys: {list(val[0].keys())[:12]}")
                        elif isinstance(val, (int, float)):
                            print(f"      .{k} = {val}")
            save(f"carrefour_intercepted_{len(all_store_products)}.json", data)

        # Check if we got products from intercepted responses
        carrefour_products = []
        for resp in api_responses:
            data = resp["data"]
            if isinstance(data, dict):
                prods = data.get("products", data.get("items", data.get("hits", [])))
                if isinstance(prods, list) and prods and isinstance(prods[0], dict):
                    if any(k in prods[0] for k in ["price", "name", "sku", "id"]):
                        carrefour_products.extend(prods)
                        print(f"  Got {len(prods)} products from {resp['url'][:60]}")

        if carrefour_products:
            all_store_products["carrefour"] = carrefour_products
            save(f"carrefour_raw_{ts}.json", carrefour_products)
            print(f"  CARREFOUR TOTAL: {len(carrefour_products)} products!")

            # Now paginate
            print("  Paginating...")
            for pg in range(1, 200):
                api_responses.clear()
                page.goto(f"https://www.carrefourksa.com/mafsau/ar/v4/search?keyword=&pageSize=60&currentPage={pg}", timeout=30000)
                page.wait_for_timeout(3000)

                page_prods = []
                for resp in api_responses:
                    data = resp["data"]
                    if isinstance(data, dict):
                        prods = data.get("products", data.get("items", data.get("hits", [])))
                        if isinstance(prods, list) and prods:
                            page_prods.extend(prods)

                if not page_prods:
                    print(f"  Page {pg}: No products, done!")
                    break

                carrefour_products.extend(page_prods)
                if pg % 10 == 0:
                    print(f"  Page {pg}: +{len(page_prods)} (total: {len(carrefour_products)})")
                time.sleep(0.5)

            all_store_products["carrefour"] = carrefour_products
            save(f"carrefour_raw_{ts}.json", carrefour_products)
            print(f"\n  CARREFOUR FINAL: {len(carrefour_products)} products")

    except Exception as e:
        print(f"  Carrefour ERR: {type(e).__name__}: {e}")
    finally:
        page.close()

    # ============================================================
    # 2. LULU
    # ============================================================
    print("\n" + "=" * 60)
    print("2. LULU HYPERMARKET (Playwright)")
    print("=" * 60)

    page = context.new_page()
    page.on("response", handle_response)
    api_responses.clear()

    try:
        print("  Loading Lulu website...")
        page.goto("https://www.luluhypermarket.com/en-sa", timeout=30000)
        page.wait_for_timeout(5000)

        print(f"  Intercepted {len(api_responses)} API responses")
        for resp in api_responses[:10]:
            print(f"    {resp['url'][:80]} size={resp['size']}")

        # Try grocery section
        api_responses.clear()
        print("\n  Navigating to grocery...")
        try:
            page.goto("https://www.luluhypermarket.com/en-sa/grocery/c/HY00214301", timeout=30000)
            page.wait_for_timeout(5000)
            print(f"  Intercepted {len(api_responses)} API responses")
            for resp in api_responses:
                print(f"    {resp['url'][:80]} size={resp['size']}")
        except:
            pass

        lulu_products = []
        for resp in api_responses:
            data = resp["data"]
            if isinstance(data, dict):
                prods = data.get("products", data.get("items", data.get("hits", [])))
                if isinstance(prods, list) and prods:
                    lulu_products.extend(prods)
                    print(f"  Got {len(prods)} products!")

        if lulu_products:
            all_store_products["lulu"] = lulu_products
            save(f"lulu_raw_{ts}.json", lulu_products)
            print(f"  LULU TOTAL: {len(lulu_products)} products!")

    except Exception as e:
        print(f"  Lulu ERR: {type(e).__name__}: {e}")
    finally:
        page.close()

    # ============================================================
    # 3. SADHAN
    # ============================================================
    print("\n" + "=" * 60)
    print("3. AL SADHAN (Playwright)")
    print("=" * 60)

    page = context.new_page()
    page.on("response", handle_response)
    api_responses.clear()

    try:
        print("  Loading Sadhan website...")
        page.goto("https://alsadhan.witheldokan.com", timeout=30000)
        page.wait_for_timeout(5000)

        print(f"  Intercepted {len(api_responses)} API responses")
        for resp in api_responses[:10]:
            url = resp["url"]
            data = resp["data"]
            print(f"    {url[:80]} size={resp['size']}")
            if isinstance(data, dict):
                print(f"      Keys: {list(data.keys())[:10]}")

        sadhan_products = []
        for resp in api_responses:
            data = resp["data"]
            if isinstance(data, dict):
                for k in ["products", "items", "data"]:
                    if k in data and isinstance(data[k], list) and data[k]:
                        sadhan_products.extend(data[k])

        if sadhan_products:
            all_store_products["sadhan"] = sadhan_products
            save(f"sadhan_raw_{ts}.json", sadhan_products)
            print(f"  SADHAN TOTAL: {len(sadhan_products)} products!")

    except Exception as e:
        print(f"  Sadhan ERR: {type(e).__name__}: {e}")
    finally:
        page.close()

    browser.close()

# ============================================================
# Normalize and merge all
# ============================================================
print("\n" + "=" * 60)
print("NORMALIZING & MERGING")
print("=" * 60)

for store, products in all_store_products.items():
    print(f"  {store}: {len(products)} raw products")
    if products and isinstance(products[0], dict):
        print(f"    Sample keys: {list(products[0].keys())[:15]}")
        print(f"    Sample: {json.dumps(products[0], ensure_ascii=False)[:400]}")

    normalized = []
    for p in products:
        row = {
            "product_id": p.get("id", p.get("productId", p.get("sku", ""))),
            "sku": p.get("sku", p.get("code", p.get("barcode", ""))),
            "name_ar": p.get("name", p.get("title", p.get("nameAr", ""))),
            "name_en": p.get("nameEn", p.get("englishName", "")),
            "category_id": p.get("categoryId", p.get("category_id", "")),
            "category_name": p.get("category", p.get("categoryName", p.get("department", ""))),
            "parent_category": "",
            "brand_id": "",
            "brand_name": p.get("brand", p.get("brandName", "")),
            "description": p.get("description", ""),
            "image_url": p.get("image", p.get("imageUrl", p.get("thumbnail", p.get("img", "")))),
            "price": p.get("price", p.get("currentPrice", p.get("mrp", ""))),
            "sale_price": p.get("salePrice", p.get("discountPrice", p.get("offerPrice", ""))),
            "currency": "SAR",
            "size": p.get("size", p.get("weight", "")),
            "unit": p.get("unit", p.get("unitOfMeasure", "")),
            "in_stock": 1 if p.get("inStock", p.get("available", True)) else 0,
            "variety_id": "",
            "barcode": p.get("barcode", p.get("ean", "")),
            "store": store,
            "store_name": {"carrefour": "Carrefour", "lulu": "Lulu Hypermarket",
                          "sadhan": "Al Sadhan", "farm": "Farm", "ramez": "Ramez",
                          "spar": "Spar"}.get(store, store),
            "city": "Riyadh",
            "source_endpoint": f"{store} website",
            "fetched_at": datetime.now().isoformat(),
            "varieties_count": 1,
        }
        normalized.append(row)

    if normalized:
        fn = list(normalized[0].keys())
        with open(f"data/{store}_products.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fn)
            w.writeheader()
            w.writerows(normalized)
        save(f"{store}_products.json", {"metadata": {"total": len(normalized), "store": store}, "products": normalized})
        print(f"  Saved {store}: {len(normalized)} rows")

print("\n=== DONE ===")
