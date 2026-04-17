#!/usr/bin/env python3
"""Carrefour: Use Playwright with HTTP/1.1 to bypass HTTP2 error"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, time, re
from datetime import datetime
from playwright.sync_api import sync_playwright

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

with sync_playwright() as p:
    # Try Firefox instead of Chromium (different HTTP handling)
    print("=" * 60)
    print("CARREFOUR - Firefox browser")
    print("=" * 60)

    browser = p.firefox.launch(headless=True)
    context = browser.new_context(
        locale="ar-SA",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    )

    api_responses = []

    def handle_response(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200 and "json" in ct:
            try:
                body = response.body()
                if len(body) > 50:
                    data = response.json()
                    api_responses.append({"url": url, "data": data, "size": len(body)})
            except:
                pass

    page = context.new_page()
    page.on("response", handle_response)

    try:
        print("  Loading Carrefour homepage (Firefox)...")
        page.goto("https://www.carrefourksa.com/mafsau/ar/", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)
        print(f"  Title: {page.title()}")
        print(f"  URL: {page.url}")
        print(f"  Intercepted {len(api_responses)} JSON responses")

        for resp in api_responses[:10]:
            print(f"    {resp['url'][:100]} size={resp['size']}")
            if isinstance(resp["data"], dict):
                print(f"      Keys: {list(resp['data'].keys())[:10]}")

        # Check HTML for embedded data
        html = page.content()
        print(f"  HTML size: {len(html)}")

        # Look for __NEXT_DATA__
        if "__NEXT_DATA__" in html:
            print("  Found __NEXT_DATA__!")
            nd = page.evaluate("() => window.__NEXT_DATA__")
            save("carrefour_next_data.json", nd)

        # Check for other embedded data patterns
        for pattern in ["__INITIAL_STATE__", "__NUXT__", "__APP_STATE__", "__PRELOADED_STATE__"]:
            if pattern in html:
                print(f"  Found {pattern}!")

        # Look for script bundles
        scripts = re.findall(r'src="([^"]*\.js[^"]*)"', html)
        print(f"  JS bundles: {len(scripts)}")

        # Try navigating to search
        api_responses.clear()
        print("\n  Navigating to search...")
        page.goto("https://www.carrefourksa.com/mafsau/ar/v4/search?keyword=rice", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)
        print(f"  URL: {page.url}")
        print(f"  Intercepted {len(api_responses)} JSON responses")

        for resp in api_responses[:10]:
            print(f"    {resp['url'][:100]} size={resp['size']}")
            if isinstance(resp["data"], dict):
                print(f"      Keys: {list(resp['data'].keys())[:10]}")
                for k in ["products", "items", "hits", "data"]:
                    if k in resp["data"]:
                        val = resp["data"][k]
                        if isinstance(val, list):
                            print(f"      .{k} = List[{len(val)}]")
                            if val and isinstance(val[0], dict):
                                print(f"      First keys: {list(val[0].keys())[:12]}")
                                print(f"      Sample: {json.dumps(val[0], ensure_ascii=False)[:300]}")

        # Check search page HTML
        html2 = page.content()
        print(f"  Search HTML size: {len(html2)}")

        # Check for product cards in DOM
        product_elements = page.query_selector_all("[data-testid*='product'], .product-card, .product-item, [class*='product']")
        print(f"  Product elements in DOM: {len(product_elements)}")

        if product_elements:
            for el in product_elements[:3]:
                text = el.inner_text()[:200]
                print(f"    Product: {text}")

        # Extract __NEXT_DATA__ from search page
        if "__NEXT_DATA__" in html2:
            print("\n  Search page has __NEXT_DATA__!")
            nd = page.evaluate("() => window.__NEXT_DATA__")
            save("carrefour_search_next_data.json", nd)
            if isinstance(nd, dict):
                pp = nd.get("props", {}).get("pageProps", {})
                print(f"    pageProps keys: {list(pp.keys())[:15]}")

    except Exception as e:
        print(f"  ERR: {type(e).__name__}: {e}")
    finally:
        page.close()

    browser.close()

print("\n=== DONE ===")
