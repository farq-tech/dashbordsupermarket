#!/usr/bin/env python3
"""Lulu: Try product listing URLs with category codes + full browser intercept"""
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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        locale="en-SA",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

    all_api = []
    all_urls_seen = set()

    def intercept(response):
        url = response.url
        if url in all_urls_seen:
            return
        ct = response.headers.get("content-type", "")
        if response.status == 200:
            try:
                if "json" in ct:
                    body = response.body()
                    if len(body) > 100:
                        data = response.json()
                        all_api.append({"url": url, "data": data, "size": len(body)})
                        all_urls_seen.add(url)
            except:
                pass

    page = context.new_page()
    page.on("response", intercept)

    print("=" * 60)
    print("LULU - Category code URLs")
    print("=" * 60)

    # Try category pages with codes (from the Lulu website structure)
    cat_urls = [
        # Main category codes
        ("Grocery", "https://gcc.luluhypermarket.com/en-sa/grocery/c/HY00214301"),
        ("Fresh Food", "https://gcc.luluhypermarket.com/en-sa/fresh-food/c/HY00214201"),
        ("Fruits", "https://gcc.luluhypermarket.com/en-sa/fresh-food/fruits/c/HY00214213"),
        ("Rice", "https://gcc.luluhypermarket.com/en-sa/grocery/rice-pasta-noodles/rice/c/HY00215501"),
        ("Dairy", "https://gcc.luluhypermarket.com/en-sa/dairy-eggs/c/HY00214601"),
        ("Beverages", "https://gcc.luluhypermarket.com/en-sa/grocery/beverages/c/HY00214401"),
        ("Snacks", "https://gcc.luluhypermarket.com/en-sa/grocery/snacks-confectionery/c/HY00215401"),
    ]

    lulu_products = []

    for cat_name, cat_url in cat_urls:
        all_api.clear()
        print(f"\n  {cat_name}: {cat_url.split('/')[-1]}")

        try:
            page.goto(cat_url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            # Scroll to trigger lazy loading
            for _ in range(5):
                page.evaluate("window.scrollBy(0, 800)")
                page.wait_for_timeout(500)

            print(f"    API responses: {len(all_api)}")
            for resp in all_api:
                print(f"      {resp['url'][:80]} size={resp['size']}")
                if isinstance(resp["data"], dict):
                    for k in ["products", "items", "data", "results", "content"]:
                        if k in resp["data"]:
                            val = resp["data"][k]
                            if isinstance(val, list) and val:
                                print(f"      .{k} = List[{len(val)}]")
                                if isinstance(val[0], dict):
                                    print(f"      First keys: {list(val[0].keys())[:12]}")
                                    lulu_products.extend(val)

            # Try scraping rendered DOM
            products = page.evaluate("""() => {
                const products = [];
                // Get all product cards using various possible selectors
                const allElements = document.querySelectorAll('*');
                const productElements = [];
                for (const el of allElements) {
                    const cls = el.className || '';
                    if (typeof cls === 'string' && (cls.includes('product') || cls.includes('Product'))) {
                        productElements.push(el);
                    }
                }

                // Also try data attributes
                const dataProducts = document.querySelectorAll('[data-sku], [data-product-id], [data-item-id]');

                const elements = productElements.length > dataProducts.length ? productElements : [...dataProducts];

                // Deduplicate by checking if elements contain each other
                const unique = elements.filter((el, i) => {
                    return !elements.some((other, j) => j !== i && el.contains(other) && el !== other);
                });

                unique.forEach(el => {
                    const text = el.textContent || '';
                    if (text.length > 5 && text.length < 2000) {
                        const priceMatch = text.match(/(?:SAR|ر\\.س|SR)\\s*([\\d,.]+)/);
                        products.push({
                            text: text.trim().substring(0, 200),
                            price: priceMatch ? priceMatch[1] : '',
                            sku: el.dataset.sku || el.dataset.productId || '',
                            tag: el.tagName,
                            class: (el.className || '').substring(0, 100),
                        });
                    }
                });

                return {products, totalElements: elements.length, uniqueElements: unique.length};
            }""")

            print(f"    DOM: {products.get('totalElements', 0)} product elements, {products.get('uniqueElements', 0)} unique")
            dom_prods = products.get("products", [])
            if dom_prods:
                for dp in dom_prods[:3]:
                    print(f"      {dp.get('text', '')[:80]}")
                lulu_products.extend(dom_prods)

            # Check page HTML for SSR data
            html = page.content()
            if "__NEXT_DATA__" in html:
                nd = page.evaluate("() => window.__NEXT_DATA__")
                if nd:
                    save(f"lulu_next_data_{cat_name.lower().replace(' ','_')}.json", nd)
                    pp = nd.get("props", {}).get("pageProps", {})
                    print(f"    __NEXT_DATA__ pageProps keys: {list(pp.keys())[:10]}")
                    for k in ["products", "items", "data", "initialProducts"]:
                        if k in pp:
                            val = pp[k]
                            if isinstance(val, list):
                                print(f"    pageProps.{k} = List[{len(val)}]")
                                lulu_products.extend(val)

        except Exception as e:
            print(f"    ERR: {type(e).__name__}: {e}")

    # Try search
    print("\n  Trying search...")
    all_api.clear()
    try:
        page.goto("https://gcc.luluhypermarket.com/en-sa/search/?q=rice&sort=relevance", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        for _ in range(3):
            page.evaluate("window.scrollBy(0, 800)")
            page.wait_for_timeout(500)

        print(f"    API responses: {len(all_api)}")
        for resp in all_api:
            print(f"      {resp['url'][:80]} size={resp['size']}")
            if isinstance(resp["data"], dict):
                for k in ["products", "items", "data", "results", "hits"]:
                    if k in resp["data"]:
                        val = resp["data"][k]
                        if isinstance(val, list) and val:
                            print(f"      .{k} = List[{len(val)}]")
                            lulu_products.extend(val)
    except Exception as e:
        print(f"    Search ERR: {type(e).__name__}: {e}")

    page.close()
    browser.close()

    print(f"\n  LULU TOTAL: {len(lulu_products)} items collected")
    if lulu_products:
        save(f"lulu_raw_{ts}.json", lulu_products)
        print(f"  Saved to data/lulu_raw_{ts}.json")
        if isinstance(lulu_products[0], dict):
            print(f"  Sample keys: {list(lulu_products[0].keys())[:12]}")
            print(f"  Sample: {json.dumps(lulu_products[0], ensure_ascii=False)[:300]}")

print("\n=== DONE ===")
