#!/usr/bin/env python3
"""Lulu: Use browser context to make API calls (bypass CORS/auth)"""
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
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        locale="en-SA",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

    page = context.new_page()

    print("=" * 60)
    print("LULU - Browser API calls")
    print("=" * 60)

    # First load the homepage to get cookies/session
    print("  Loading homepage to get session...")
    page.goto("https://gcc.luluhypermarket.com/en-sa", timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    print(f"  Title: {page.title()}")

    # Get cookies
    cookies = context.cookies()
    print(f"  Cookies: {len(cookies)}")
    for c in cookies[:5]:
        print(f"    {c['name']}: {c['value'][:30]}...")

    # Now make API calls from within the page context using fetch()
    print("\n  Making API calls from browser context...")

    api_endpoints = [
        "/api/client/categories/",
        "/api/client/widgets/mega-menu-sa/",
        "/api/client/widgets/home-page-sa/",
        "/api/client/widgets/categories-sa/",
        "/api/hot-food-config",
        "/api/client/products/?limit=20",
        "/api/client/products/?limit=20&category=HY00214301",
        "/api/client/search/?q=rice&limit=20",
        "/api/v1/categories/",
        "/api/v1/products/",
        "/api/v2/categories/",
        "/api/v2/products/",
        "/api/catalog/",
        "/api/products/",
        "/api/categories/",
    ]

    for ep in api_endpoints:
        try:
            result = page.evaluate(f"""async () => {{
                try {{
                    const r = await fetch('https://gcc.luluhypermarket.com{ep}', {{
                        credentials: 'include',
                        headers: {{'Accept': 'application/json'}},
                    }});
                    const text = await r.text();
                    return {{status: r.status, size: text.length, body: text.substring(0, 2000)}};
                }} catch(e) {{
                    return {{error: e.message}};
                }}
            }}""")

            status = result.get("status", "ERR")
            size = result.get("size", 0)
            if status == 200 and size > 100:
                print(f"  [{status}] {ep} size={size}")
                try:
                    d = json.loads(result["body"])
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        for k in ["products", "items", "data", "results", "categories", "widgets", "content"]:
                            if k in d:
                                val = d[k]
                                if isinstance(val, list):
                                    print(f"    .{k} = List[{len(val)}]")
                                    if val and isinstance(val[0], dict):
                                        print(f"    First keys: {list(val[0].keys())[:12]}")
                                elif isinstance(val, dict):
                                    print(f"    .{k} keys = {list(val.keys())[:8]}")
                        save(f"lulu_api_{ep.strip('/').replace('/', '_').split('?')[0]}.json", d)
                    elif isinstance(d, list):
                        print(f"    Array[{len(d)}]")
                except:
                    print(f"    Body: {result.get('body', '')[:200]}")
            elif status != 200:
                if size > 0 and size < 200:
                    print(f"  [{status}] {ep} size={size}")
            # Don't print 404s
        except Exception as e:
            print(f"  [ERR] {ep}: {type(e).__name__}")

    # Also try the Akinon API through the browser
    print("\n  Trying Akinon API patterns from browser...")
    akinon_endpoints = [
        "https://luluhypermarket.akinoncloud.com/api/v1/products/",
        "https://luluhypermarket.akinoncloud.com/api/v1/categories/",
        "https://sa.luluhypermarket.akinoncloud.com/api/v1/products/",
        "https://sa.luluhypermarket.akinoncloud.com/api/v1/categories/",
    ]

    for ep in akinon_endpoints:
        try:
            result = page.evaluate(f"""async () => {{
                try {{
                    const r = await fetch('{ep}', {{
                        headers: {{'Accept': 'application/json'}},
                    }});
                    const text = await r.text();
                    return {{status: r.status, size: text.length, body: text.substring(0, 2000)}};
                }} catch(e) {{
                    return {{error: e.message}};
                }}
            }}""")
            status = result.get("status", "ERR")
            error = result.get("error", "")
            if error:
                print(f"  [CORS] {ep.split('.com')[1][:40]}")
            elif status == 200:
                print(f"  [{status}] {ep.split('.com')[1][:40]} size={result.get('size', 0)}")
            else:
                print(f"  [{status}] {ep.split('.com')[1][:40]}")
        except:
            pass

    # Take a screenshot of a category page to see what renders
    print("\n  Taking screenshot of category page...")
    page.goto("https://gcc.luluhypermarket.com/en-sa/grocery/c/HY00214301", timeout=30000, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    # Check what's actually on the page
    page_info = page.evaluate("""() => {
        return {
            title: document.title,
            url: location.href,
            bodyText: document.body.innerText.substring(0, 1000),
            allLinks: Array.from(document.querySelectorAll('a[href]')).length,
            allImages: Array.from(document.querySelectorAll('img')).length,
            allDivs: document.querySelectorAll('div').length,
            scripts: Array.from(document.querySelectorAll('script[src]')).map(s => s.src).filter(s => !s.includes('google') && !s.includes('snap')).slice(0, 5),
        }
    }""")
    print(f"  Category page info:")
    print(f"    Title: {page_info['title']}")
    print(f"    Links: {page_info['allLinks']}, Images: {page_info['allImages']}, Divs: {page_info['allDivs']}")
    print(f"    Body text (first 300): {page_info['bodyText'][:300]}")
    print(f"    Scripts: {page_info['scripts']}")

    page.screenshot(path="data/lulu_category_screenshot.png")
    print("  Screenshot saved to data/lulu_category_screenshot.png")

    page.close()
    browser.close()

print("\n=== DONE ===")
