#!/usr/bin/env python3
"""Use Playwright to extract products from Carrefour, Lulu, Sadhan - v2"""
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

    # ============================================================
    # 1. CARREFOUR - Load actual website, intercept API calls
    # ============================================================
    print("=" * 60)
    print("1. CARREFOUR KSA")
    print("=" * 60)

    api_responses = []

    def handle_carrefour_response(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if "json" in ct and response.status == 200:
            try:
                body = response.body()
                if len(body) > 100:
                    data = response.json()
                    api_responses.append({"url": url, "data": data, "size": len(body)})
            except:
                pass

    page = context.new_page()
    page.on("response", handle_carrefour_response)

    try:
        # Load the actual website first
        print("  Loading Carrefour homepage...")
        page.goto("https://www.carrefourksa.com/mafsau/ar/", timeout=60000, wait_until="networkidle")
        print(f"  Homepage loaded, intercepted {len(api_responses)} JSON responses")

        for resp in api_responses[:5]:
            print(f"    {resp['url'][:100]} size={resp['size']}")

        # Now try search
        api_responses.clear()
        print("\n  Searching for products...")
        page.goto("https://www.carrefourksa.com/mafsau/ar/v4/search?keyword=rice&pageSize=60", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)
        print(f"  Search page: intercepted {len(api_responses)} JSON responses")

        for resp in api_responses:
            url = resp["url"]
            data = resp["data"]
            print(f"    {url[:100]} size={resp['size']}")
            if isinstance(data, dict):
                print(f"      Keys: {list(data.keys())[:10]}")
                for k in ["products", "items", "results", "data", "hits"]:
                    if k in data:
                        val = data[k]
                        if isinstance(val, list):
                            print(f"      .{k} = List[{len(val)}]")
                            if val and isinstance(val[0], dict):
                                print(f"      First keys: {list(val[0].keys())[:12]}")
                save(f"carrefour_intercepted.json", data)

        # Also try browsing a category
        if not api_responses:
            api_responses.clear()
            print("\n  Trying category browse...")
            page.goto("https://www.carrefourksa.com/mafsau/ar/v4/c/NFKSA1100000?pageSize=60", timeout=60000, wait_until="networkidle")
            page.wait_for_timeout(5000)
            print(f"  Category: intercepted {len(api_responses)} JSON responses")
            for resp in api_responses[:5]:
                print(f"    {resp['url'][:100]} size={resp['size']}")

        # Check __NEXT_DATA__ or embedded data
        print("\n  Checking embedded data...")
        html = page.content()
        if "__NEXT_DATA__" in html:
            print("  Found __NEXT_DATA__!")
            nd = page.evaluate("() => window.__NEXT_DATA__")
            if nd:
                save("carrefour_next_data.json", nd)
                print(f"  Keys: {list(nd.keys()) if isinstance(nd, dict) else type(nd)}")

        # Extract products from intercepted responses
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

    except Exception as e:
        print(f"  Carrefour ERR: {type(e).__name__}: {e}")
    finally:
        page.close()

    # ============================================================
    # 2. LULU
    # ============================================================
    print("\n" + "=" * 60)
    print("2. LULU HYPERMARKET")
    print("=" * 60)

    api_responses.clear()

    def handle_lulu_response(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200:
            try:
                if "json" in ct and len(response.body()) > 100:
                    data = response.json()
                    api_responses.append({"url": url, "data": data, "size": len(response.body())})
            except:
                pass

    page = context.new_page()
    page.on("response", handle_lulu_response)

    try:
        print("  Loading Lulu website...")
        page.goto("https://www.luluhypermarket.com/en-sa", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)
        print(f"  Page loaded, status title: {page.title()}")
        print(f"  Intercepted {len(api_responses)} JSON responses")

        for resp in api_responses[:10]:
            print(f"    {resp['url'][:100]} size={resp['size']}")

        # Check if page loaded or got blocked
        html = page.content()
        print(f"  HTML size: {len(html)}")
        if "403" in page.title() or "forbidden" in html.lower()[:500]:
            print("  -> 403 Forbidden!")

        # Check for __NEXT_DATA__
        if "__NEXT_DATA__" in html:
            print("  Found __NEXT_DATA__!")
            nd = page.evaluate("() => window.__NEXT_DATA__")
            if nd:
                save("lulu_next_data.json", nd)

        # Try grocery category
        api_responses.clear()
        print("\n  Trying grocery category...")
        page.goto("https://www.luluhypermarket.com/en-sa/grocery/c/HY00214301", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)
        print(f"  Intercepted {len(api_responses)} JSON responses")

        for resp in api_responses[:10]:
            print(f"    {resp['url'][:100]} size={resp['size']}")

        # Try search
        api_responses.clear()
        print("\n  Trying search...")
        page.goto("https://www.luluhypermarket.com/en-sa/search?q=rice", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)
        print(f"  Intercepted {len(api_responses)} JSON responses")

        for resp in api_responses[:10]:
            url = resp["url"]
            data = resp["data"]
            print(f"    {url[:100]} size={resp['size']}")
            if isinstance(data, dict):
                print(f"      Keys: {list(data.keys())[:10]}")

        lulu_products = []
        for resp in api_responses:
            data = resp["data"]
            if isinstance(data, dict):
                prods = data.get("products", data.get("items", data.get("hits", data.get("results", []))))
                if isinstance(prods, list) and prods:
                    lulu_products.extend(prods)

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
    print("3. AL SADHAN")
    print("=" * 60)

    api_responses.clear()

    def handle_sadhan_response(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200:
            try:
                if "json" in ct and len(response.body()) > 50:
                    data = response.json()
                    api_responses.append({"url": url, "data": data, "size": len(response.body())})
            except:
                pass

    page = context.new_page()
    page.on("response", handle_sadhan_response)

    try:
        print("  Loading Sadhan website...")
        page.goto("https://alsadhan.witheldokan.com", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(8000)
        print(f"  Page loaded, title: {page.title()}")
        print(f"  Intercepted {len(api_responses)} JSON responses")

        for resp in api_responses:
            url = resp["url"]
            data = resp["data"]
            print(f"    {url[:100]} size={resp['size']}")
            if isinstance(data, dict):
                print(f"      Keys: {list(data.keys())[:10]}")
                for k in ["products", "items", "data", "categories"]:
                    if k in data:
                        val = data[k]
                        if isinstance(val, list):
                            print(f"      .{k} = List[{len(val)}]")
                            if val and isinstance(val[0], dict):
                                print(f"      First item keys: {list(val[0].keys())[:12]}")
                        elif isinstance(val, dict):
                            print(f"      .{k} keys = {list(val.keys())[:10]}")
            save(f"sadhan_intercepted_{api_responses.index(resp)}.json", data)

        # Navigate to a category if homepage loaded
        if api_responses:
            # Look for category links in intercepted data
            for resp in api_responses:
                data = resp["data"]
                if isinstance(data, dict):
                    cats = data.get("categories", data.get("data", {}).get("categories", []) if isinstance(data.get("data"), dict) else [])
                    if isinstance(cats, list) and cats:
                        print(f"\n  Found {len(cats)} categories!")
                        for cat in cats[:3]:
                            if isinstance(cat, dict):
                                print(f"    Cat: {cat.get('name', cat.get('title', ''))}")

        sadhan_products = []
        for resp in api_responses:
            data = resp["data"]
            if isinstance(data, dict):
                for k in ["products", "items", "data"]:
                    if k in data and isinstance(data[k], list) and data[k]:
                        if isinstance(data[k][0], dict) and any(pk in data[k][0] for pk in ["name", "price", "title", "id"]):
                            sadhan_products.extend(data[k])
                            print(f"  Got {len(data[k])} products from .{k}")

        if sadhan_products:
            all_store_products["sadhan"] = sadhan_products
            save(f"sadhan_raw_{ts}.json", sadhan_products)
            print(f"  SADHAN TOTAL: {len(sadhan_products)} products!")

    except Exception as e:
        print(f"  Sadhan ERR: {type(e).__name__}: {e}")
    finally:
        page.close()

    # ============================================================
    # 4. FARM
    # ============================================================
    print("\n" + "=" * 60)
    print("4. FARM SUPERSTORES")
    print("=" * 60)

    api_responses.clear()

    def handle_farm_response(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200:
            try:
                if "json" in ct and len(response.body()) > 50:
                    data = response.json()
                    api_responses.append({"url": url, "data": data, "size": len(response.body())})
            except:
                pass

    page = context.new_page()
    page.on("response", handle_farm_response)

    try:
        print("  Loading Farm website...")
        page.goto("https://www.farm.com.sa", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)
        print(f"  Page loaded, title: {page.title()}")
        print(f"  URL: {page.url}")
        print(f"  Intercepted {len(api_responses)} JSON responses")

        for resp in api_responses[:10]:
            print(f"    {resp['url'][:100]} size={resp['size']}")
            if isinstance(resp["data"], dict):
                print(f"      Keys: {list(resp['data'].keys())[:10]}")

        # Check for app download redirect
        html = page.content()
        print(f"  HTML size: {len(html)}")

        # Try the go subdomain
        api_responses.clear()
        print("\n  Trying go.farm.com.sa...")
        page.goto("https://go.farm.com.sa", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)
        print(f"  URL: {page.url}")
        print(f"  Intercepted {len(api_responses)} JSON responses")

        for resp in api_responses[:10]:
            print(f"    {resp['url'][:100]} size={resp['size']}")

    except Exception as e:
        print(f"  Farm ERR: {type(e).__name__}: {e}")
    finally:
        page.close()

    browser.close()

# ============================================================
# Normalize and save
# ============================================================
print("\n" + "=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)

if all_store_products:
    for store, products in all_store_products.items():
        print(f"  {store}: {len(products)} products")
        if products and isinstance(products[0], dict):
            print(f"    Sample keys: {list(products[0].keys())[:15]}")
            print(f"    Sample: {json.dumps(products[0], ensure_ascii=False)[:300]}")
else:
    print("  No products extracted from any store via browser.")
    print("  Stores with Akamai/CloudFlare protection cannot be scraped easily.")

print("\n=== DONE ===")
