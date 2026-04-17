#!/usr/bin/env python3
"""Scrape Lulu, Sadhan, Farm, Ramez via browser DOM + API intercept"""
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

    # ============================================================
    # 1. LULU - Browse categories, scrape product DOM
    # ============================================================
    print("=" * 60)
    print("1. LULU HYPERMARKET - DOM Scraping")
    print("=" * 60)

    context = browser.new_context(
        locale="en-SA",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

    api_data = []
    def lulu_intercept(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200 and "json" in ct:
            try:
                body = response.body()
                if len(body) > 100:
                    data = response.json()
                    api_data.append({"url": url, "data": data, "size": len(body)})
            except:
                pass

    page = context.new_page()
    page.on("response", lulu_intercept)

    lulu_products = []

    # Category URLs from Lulu SA
    lulu_categories = [
        "https://gcc.luluhypermarket.com/en-sa/grocery/",
        "https://gcc.luluhypermarket.com/en-sa/fresh-food/",
        "https://gcc.luluhypermarket.com/en-sa/electronics-home-appliances/",
        "https://gcc.luluhypermarket.com/en-sa/home-kitchen/",
        "https://gcc.luluhypermarket.com/en-sa/health-beauty/",
        "https://gcc.luluhypermarket.com/en-sa/baby-toys/",
        "https://gcc.luluhypermarket.com/en-sa/fashion-lifestyle/",
    ]

    for cat_url in lulu_categories:
        cat_name = cat_url.rstrip("/").split("/")[-1]
        print(f"\n  Category: {cat_name}")
        api_data.clear()

        try:
            page.goto(cat_url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            # Check for API responses
            print(f"    API responses: {len(api_data)}")
            for resp in api_data:
                print(f"      {resp['url'][:80]} size={resp['size']}")
                if isinstance(resp["data"], dict):
                    for k in ["products", "items", "data", "results"]:
                        if k in resp["data"]:
                            val = resp["data"][k]
                            if isinstance(val, list) and val:
                                print(f"      .{k} = List[{len(val)}]")
                                lulu_products.extend(val)

            # Scrape product cards from DOM
            products_from_dom = page.evaluate("""() => {
                const products = [];
                // Try various selectors
                const selectors = [
                    '[data-testid*="product"]',
                    '.product-card',
                    '.product-item',
                    '[class*="ProductCard"]',
                    '[class*="productCard"]',
                    'article[class*="product"]',
                    '[class*="plp-card"]',
                    '[class*="item-card"]',
                ];
                let elements = [];
                for (const sel of selectors) {
                    elements = document.querySelectorAll(sel);
                    if (elements.length > 0) break;
                }

                elements.forEach(el => {
                    const nameEl = el.querySelector('h2, h3, h4, [class*="name"], [class*="title"], a[class*="product"]');
                    const priceEl = el.querySelector('[class*="price"], [class*="Price"], span[class*="amount"]');
                    const imgEl = el.querySelector('img');
                    const linkEl = el.querySelector('a[href]');

                    if (nameEl) {
                        products.push({
                            name: nameEl.textContent.trim(),
                            price: priceEl ? priceEl.textContent.trim() : '',
                            image: imgEl ? imgEl.src : '',
                            link: linkEl ? linkEl.href : '',
                            html: el.innerHTML.substring(0, 500),
                        });
                    }
                });
                return products;
            }""")
            print(f"    DOM products: {len(products_from_dom)}")
            if products_from_dom:
                for p in products_from_dom[:3]:
                    print(f"      {p.get('name', '')[:60]} | {p.get('price', '')}")

            # Also try subcategory links
            sub_links = page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links
                    .map(a => ({href: a.href, text: a.textContent.trim().substring(0, 50)}))
                    .filter(l => l.href.includes('/en-sa/') && l.href.includes('/c/'))
                    .slice(0, 30);
            }""")
            print(f"    Subcategory links: {len(sub_links)}")
            for sl in sub_links[:5]:
                print(f"      {sl['text']}: {sl['href'][:60]}")

            # Navigate to subcategories and scrape
            for sub in sub_links[:10]:
                api_data.clear()
                try:
                    page.goto(sub["href"], timeout=20000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)

                    # Scroll to load more
                    for _ in range(3):
                        page.evaluate("window.scrollBy(0, 1000)")
                        page.wait_for_timeout(500)

                    sub_products = page.evaluate("""() => {
                        const products = [];
                        const selectors = ['[data-testid*="product"]', '.product-card', '[class*="ProductCard"]', '[class*="plp-card"]', 'article'];
                        let elements = [];
                        for (const sel of selectors) {
                            elements = document.querySelectorAll(sel);
                            if (elements.length > 2) break;
                        }
                        elements.forEach(el => {
                            const nameEl = el.querySelector('h2, h3, h4, [class*="name"], [class*="title"]');
                            const priceEl = el.querySelector('[class*="price"], [class*="Price"]');
                            const imgEl = el.querySelector('img');
                            if (nameEl && nameEl.textContent.trim().length > 2) {
                                products.push({
                                    name: nameEl.textContent.trim(),
                                    price: priceEl ? priceEl.textContent.trim().replace(/[^0-9.]/g, '') : '',
                                    image: imgEl ? imgEl.src : '',
                                });
                            }
                        });
                        return products;
                    }""")

                    # Check API responses
                    for resp in api_data:
                        if isinstance(resp["data"], dict):
                            for k in ["products", "items", "data", "results"]:
                                if k in resp["data"]:
                                    val = resp["data"][k]
                                    if isinstance(val, list) and val:
                                        lulu_products.extend(val)
                                        print(f"    {sub['text']}: +{len(val)} from API")

                    if sub_products:
                        lulu_products.extend(sub_products)
                        print(f"    {sub['text']}: +{len(sub_products)} from DOM")

                except Exception as e:
                    pass

        except Exception as e:
            print(f"    ERR: {type(e).__name__}: {e}")

    page.close()
    context.close()

    if lulu_products:
        all_store_products["lulu"] = lulu_products
        save(f"lulu_raw_{ts}.json", lulu_products)
        print(f"\n  LULU TOTAL: {len(lulu_products)} products!")
    else:
        print("\n  LULU: No products extracted")

    # ============================================================
    # 2. SADHAN - Try public store URL (not admin panel)
    # ============================================================
    print("\n" + "=" * 60)
    print("2. AL SADHAN")
    print("=" * 60)

    context = browser.new_context(
        locale="ar-SA",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

    api_data.clear()
    def sadhan_intercept(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200 and ("json" in ct or url.endswith(".json")):
            try:
                body = response.body()
                if len(body) > 50:
                    data = response.json()
                    api_data.append({"url": url, "data": data, "size": len(body)})
            except:
                pass

    page = context.new_page()
    page.on("response", sadhan_intercept)

    try:
        # The admin panel was at alsadhan.witheldokan.com
        # Try the public-facing store
        sadhan_urls = [
            "https://alsadhanmarket.com",
            "https://www.alsadhanmarket.com",
            "https://store.alsadhan.com",
            "https://shop.alsadhan.com",
            "https://alsadhan.com",
            "https://www.alsadhan.com",
        ]

        for url in sadhan_urls:
            api_data.clear()
            try:
                print(f"  Trying {url}...")
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                final_url = page.url
                title = page.title()
                print(f"    -> {final_url} title={title[:50]}")
                print(f"    API responses: {len(api_data)}")

                for resp in api_data[:5]:
                    print(f"      {resp['url'][:80]} size={resp['size']}")

                if "alsadhan" in final_url.lower() and title:
                    html = page.content()
                    print(f"    HTML: {len(html)} bytes")
                    if "__NEXT_DATA__" in html:
                        print("    Found __NEXT_DATA__!")
                    break
            except Exception as e:
                print(f"    ERR: {type(e).__name__}")

        # Try Eldokan API directly (the platform Sadhan uses)
        print("\n  Trying Eldokan API patterns...")
        import httpx
        hclient = httpx.Client(timeout=10, follow_redirects=True)
        eldokan_endpoints = [
            "https://sadhanmarketapi.witheldokan.com/api/home",
            "https://sadhanmarketapi.witheldokan.com/api/categories",
            "https://sadhanmarketapi.witheldokan.com/api/products",
            "https://masterapi.witheldokan.com/api/home",
            "https://masterapi.witheldokan.com/api/store/alsadhan/home",
            "https://masterapi.witheldokan.com/api/store/alsadhan/categories",
        ]
        for ep in eldokan_endpoints:
            try:
                r = hclient.get(ep, headers={
                    "Accept": "application/json",
                    "User-Agent": "okhttp/5.0.0",
                    "x-platform": "android",
                }, timeout=8)
                if r.status_code != 404 and len(r.content) > 50:
                    print(f"    [{r.status_code}] {ep.split('.com')[1]} size={len(r.content)}")
                    if r.status_code == 200:
                        try:
                            d = r.json()
                            if isinstance(d, dict):
                                print(f"      Keys: {list(d.keys())[:10]}")
                                print(f"      Preview: {json.dumps(d, ensure_ascii=False)[:300]}")
                        except:
                            pass
            except Exception as e:
                if "timeout" not in str(e).lower():
                    print(f"    [ERR] {ep.split('.com')[1]}: {type(e).__name__}")
        hclient.close()

    except Exception as e:
        print(f"  Sadhan ERR: {type(e).__name__}: {e}")
    finally:
        page.close()
        context.close()

    # ============================================================
    # 3. FARM - Check app/website
    # ============================================================
    print("\n" + "=" * 60)
    print("3. FARM SUPERSTORES")
    print("=" * 60)

    context = browser.new_context(
        locale="ar-SA",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

    api_data.clear()
    def farm_intercept(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200 and "json" in ct:
            try:
                body = response.body()
                if len(body) > 50:
                    data = response.json()
                    api_data.append({"url": url, "data": data, "size": len(body)})
            except:
                pass

    page = context.new_page()
    page.on("response", farm_intercept)

    try:
        print("  Loading Farm website...")
        page.goto("https://www.farm.com.sa", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        print(f"  Title: {page.title()}")
        print(f"  URL: {page.url}")
        html = page.content()
        print(f"  HTML: {len(html)} bytes")

        # Check for product data in HTML
        if "__NEXT_DATA__" in html:
            print("  Found __NEXT_DATA__!")
            nd = page.evaluate("() => window.__NEXT_DATA__")
            save("farm_next_data.json", nd)

        # Look for links to online store
        links = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => ({href: a.href, text: a.textContent.trim().substring(0, 50)}))
                .filter(l => l.href.includes('shop') || l.href.includes('store') || l.href.includes('order') || l.href.includes('go.farm') || l.href.includes('product'))
                .slice(0, 10);
        }""")
        print(f"  Shop-related links: {len(links)}")
        for l in links:
            print(f"    {l['text']}: {l['href'][:80]}")

        print(f"  API responses: {len(api_data)}")
        for resp in api_data[:5]:
            print(f"    {resp['url'][:80]} size={resp['size']}")

        # Try go.farm.com.sa
        api_data.clear()
        print("\n  Loading go.farm.com.sa...")
        page.goto("https://go.farm.com.sa", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        print(f"  Title: {page.title()}")
        print(f"  URL: {page.url}")
        print(f"  API responses: {len(api_data)}")

        for resp in api_data[:10]:
            print(f"    {resp['url'][:80]} size={resp['size']}")
            if isinstance(resp["data"], dict):
                print(f"      Keys: {list(resp['data'].keys())[:10]}")

        html2 = page.content()
        print(f"  HTML: {len(html2)} bytes")

        # Scrape products from Farm SPA
        farm_products = page.evaluate("""() => {
            const products = [];
            const selectors = ['[class*="product"]', '[class*="Product"]', 'article', '.card', '[class*="item"]'];
            let elements = [];
            for (const sel of selectors) {
                elements = document.querySelectorAll(sel);
                if (elements.length > 2) break;
            }
            elements.forEach(el => {
                const nameEl = el.querySelector('h2, h3, h4, [class*="name"], [class*="title"], p');
                const priceEl = el.querySelector('[class*="price"], [class*="Price"]');
                if (nameEl && nameEl.textContent.trim().length > 2) {
                    products.push({
                        name: nameEl.textContent.trim(),
                        price: priceEl ? priceEl.textContent.trim() : '',
                    });
                }
            });
            return products;
        }""")
        print(f"  Farm DOM products: {len(farm_products)}")

    except Exception as e:
        print(f"  Farm ERR: {type(e).__name__}: {e}")
    finally:
        page.close()
        context.close()

    # ============================================================
    # 4. RAMEZ - Try website
    # ============================================================
    print("\n" + "=" * 60)
    print("4. RAMEZ")
    print("=" * 60)

    context = browser.new_context(
        locale="ar-SA",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

    api_data.clear()
    def ramez_intercept(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200 and "json" in ct:
            try:
                body = response.body()
                if len(body) > 50:
                    data = response.json()
                    api_data.append({"url": url, "data": data, "size": len(body)})
            except:
                pass

    page = context.new_page()
    page.on("response", ramez_intercept)

    try:
        ramez_urls = [
            "https://www.ramezonline.com",
            "https://ramezonline.com",
            "https://www.ramez.com.sa",
            "https://shop.ramez.com.sa",
        ]
        for url in ramez_urls:
            api_data.clear()
            try:
                print(f"  Trying {url}...")
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                print(f"    -> {page.url} title={page.title()[:50]}")
                print(f"    API responses: {len(api_data)}")
                for resp in api_data[:5]:
                    print(f"      {resp['url'][:80]}")

                html = page.content()
                if len(html) > 5000:
                    print(f"    HTML: {len(html)} bytes")
                    # Try scraping products
                    prods = page.evaluate("""() => {
                        const products = [];
                        document.querySelectorAll('[class*="product"], [class*="Product"], article, .card').forEach(el => {
                            const name = el.querySelector('h2, h3, h4, [class*="name"], [class*="title"]');
                            const price = el.querySelector('[class*="price"], [class*="Price"]');
                            if (name && name.textContent.trim().length > 2) {
                                products.push({name: name.textContent.trim(), price: price ? price.textContent.trim() : ''});
                            }
                        });
                        return products;
                    }""")
                    if prods:
                        print(f"    DOM products: {len(prods)}")
                    break
            except Exception as e:
                print(f"    ERR: {type(e).__name__}")

    except Exception as e:
        print(f"  Ramez ERR: {type(e).__name__}: {e}")
    finally:
        page.close()
        context.close()

    browser.close()

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("EXTRACTION SUMMARY")
print("=" * 60)
for store, products in all_store_products.items():
    print(f"  {store}: {len(products)} products")
if not all_store_products:
    print("  No new products extracted from remaining stores.")
print("\n=== DONE ===")
