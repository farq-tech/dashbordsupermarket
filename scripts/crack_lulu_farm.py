#!/usr/bin/env python3
"""Lulu: Navigate naturally to bypass Cloudflare. Farm: Find web store."""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, time
from datetime import datetime
from playwright.sync_api import sync_playwright

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

with sync_playwright() as p:
    # ============================================================
    # 1. LULU - Natural navigation (click links, don't goto URLs)
    # ============================================================
    print("=" * 60)
    print("1. LULU - Natural click navigation")
    print("=" * 60)

    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        locale="en-SA",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
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

    try:
        # Step 1: Load homepage normally
        print("  Step 1: Loading homepage...")
        page.goto("https://www.luluhypermarket.com/en-sa", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(3000)
        print(f"  Homepage loaded: {page.title()[:50]}")
        print(f"  API intercepted: {len(api_data)}")

        # Step 2: Find and click on "Grocery" link
        api_data.clear()
        print("\n  Step 2: Clicking Grocery link...")

        # Try clicking the grocery link
        clicked = False
        for selector in [
            'a:has-text("Grocery")',
            'a:has-text("grocery")',
            'a[href*="grocery"]',
            'a[href*="Grocery"]',
            'nav a:first-child',
        ]:
            try:
                el = page.query_selector(selector)
                if el:
                    href = el.get_attribute("href")
                    print(f"  Found link: {href}")
                    el.click()
                    clicked = True
                    break
            except:
                pass

        if clicked:
            page.wait_for_timeout(5000)
            page.wait_for_load_state("networkidle", timeout=15000)
            print(f"  After click: {page.url}")
            print(f"  Title: {page.title()[:50]}")
            print(f"  API intercepted: {len(api_data)}")

            for resp in api_data:
                print(f"    {resp['url'][:80]} size={resp['size']}")

            # Check if we're on a product page
            html = page.content()
            if "cloudflare" in html.lower() or "blocked" in html.lower():
                print("  -> Still blocked by Cloudflare!")
            else:
                print(f"  HTML size: {len(html)}")

                # Try to extract products from DOM
                products = page.evaluate("""() => {
                    const products = [];
                    const elements = document.querySelectorAll('a[href*="/p/"], [class*="product"], [class*="Product"]');
                    elements.forEach(el => {
                        const name = el.querySelector('h2, h3, h4, [class*="name"], [class*="title"], p');
                        const price = el.querySelector('[class*="price"], [class*="Price"]');
                        if (name && name.textContent.trim().length > 3) {
                            products.push({
                                name: name.textContent.trim().substring(0, 100),
                                price: price ? price.textContent.trim() : '',
                                href: el.href || el.querySelector('a') ? (el.querySelector('a') || {}).href : '',
                            });
                        }
                    });
                    return products;
                }""")
                print(f"  DOM products: {len(products)}")
                for p in products[:5]:
                    print(f"    {p['name'][:60]} | {p['price']}")

        # Step 3: Try using the URL bar of already-loaded context
        # (cookies from homepage should be set)
        api_data.clear()
        print("\n  Step 3: Navigate to category with cookies...")
        cookies = context.cookies()
        print(f"  Cookies: {len(cookies)}")

        # Try navigating to gcc.luluhypermarket.com (the actual product site)
        page.goto("https://gcc.luluhypermarket.com/en-sa/grocery/c/HY00214301?sorter=-date_updated", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        title = page.title()
        print(f"  Category page title: {title[:60]}")
        if "cloudflare" in title.lower() or "attention" in title.lower():
            print("  -> Cloudflare block!")
            # Try with page.route to add cookies
        else:
            print(f"  API intercepted: {len(api_data)}")
            products2 = page.evaluate("""() => {
                const products = [];
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    const cls = el.className || '';
                    if (typeof cls === 'string' && cls.includes('product')) {
                        const text = el.innerText;
                        if (text.length > 5 && text.length < 500) {
                            products.push({text: text.substring(0, 200)});
                        }
                    }
                }
                return products;
            }""")
            print(f"  Product elements: {len(products2)}")

    except Exception as e:
        print(f"  ERR: {type(e).__name__}: {e}")
    finally:
        page.close()

    context.close()
    browser.close()

    # ============================================================
    # 2. FARM - Try the web store link
    # ============================================================
    print("\n" + "=" * 60)
    print("2. FARM - Web Store + Playwright API intercept")
    print("=" * 60)

    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        locale="ar-SA",
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        viewport={"width": 412, "height": 915},  # Mobile viewport
    )

    api_data.clear()
    def farm_intercept(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200:
            try:
                if "json" in ct:
                    body = response.body()
                    if len(body) > 50:
                        data = response.json()
                        api_data.append({"url": url, "data": data, "size": len(body)})
            except:
                pass

    page = context.new_page()
    page.on("response", farm_intercept)

    try:
        # Load Farm website shop online page
        print("  Loading Farm shop online page...")
        page.goto("https://www.farm.com.sa/ar/shop_online", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        print(f"  Title: {page.title()}")
        print(f"  API: {len(api_data)} responses")

        # Get all links
        links = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => ({href: a.href, text: a.textContent.trim().substring(0, 50)}))
                .filter(l => l.href.includes('farm'))
                .slice(0, 20);
        }""")
        print(f"  Links: {len(links)}")
        for l in links:
            if any(k in l["href"].lower() for k in ["app", "store", "play.google", "apple", "order", "product", "category", "go.farm"]):
                print(f"    {l['text']}: {l['href'][:80]}")

        # Check for app store links to find the app download
        app_links = [l for l in links if "play.google" in l["href"] or "apps.apple" in l["href"] or "go.farm" in l["href"]]
        if app_links:
            print(f"\n  App links found:")
            for l in app_links:
                print(f"    {l['href']}")

        # Try loading go.farm.com.sa as mobile
        api_data.clear()
        print("\n  Loading go.farm.com.sa (mobile)...")
        page.goto("https://go.farm.com.sa", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        print(f"  Title: {page.title()}")
        print(f"  URL: {page.url}")
        print(f"  API: {len(api_data)} responses")

        html = page.content()
        print(f"  HTML: {len(html)} bytes")

        # Check body text
        body_text = page.evaluate("() => document.body ? document.body.innerText.substring(0, 500) : ''")
        print(f"  Body: {body_text[:200]}")

        for resp in api_data[:5]:
            print(f"    {resp['url'][:80]} size={resp['size']}")

    except Exception as e:
        print(f"  Farm ERR: {type(e).__name__}: {e}")
    finally:
        page.close()

    context.close()
    browser.close()

    # ============================================================
    # 3. LULU - Try mobile app simulation via Playwright
    # ============================================================
    print("\n" + "=" * 60)
    print("3. LULU - Mobile app simulation")
    print("=" * 60)

    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        locale="ar-SA",
        user_agent="luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
        viewport={"width": 375, "height": 812},  # iPhone
        extra_http_headers={
            "x-app-type": "akinon-mobile",
            "x-project-name": "rn-env",
        },
    )

    api_data.clear()
    def lulu_mobile_intercept(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200:
            try:
                if "json" in ct:
                    body = response.body()
                    if len(body) > 50:
                        data = response.json()
                        api_data.append({"url": url, "data": data, "size": len(body)})
            except:
                pass

    page = context.new_page()
    page.on("response", lulu_mobile_intercept)

    try:
        # Try loading the Akinon mobile API directly
        print("  Loading Akinon mobile endpoint...")
        page.goto("https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com/products/", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        print(f"  URL: {page.url}")
        print(f"  API: {len(api_data)} responses")

        html = page.content()
        print(f"  Response: {html[:300]}")

        # Try categories
        api_data.clear()
        page.goto("https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com/categories/", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        html = page.content()
        print(f"  Categories: {html[:300]}")
        print(f"  API: {len(api_data)} responses")

    except Exception as e:
        print(f"  ERR: {type(e).__name__}: {e}")
    finally:
        page.close()

    context.close()
    browser.close()

print("\n=== DONE ===")
