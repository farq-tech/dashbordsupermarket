#!/usr/bin/env python3
"""Lulu Hypermarket: Explore gcc.luluhypermarket.com API"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
client = httpx.Client(timeout=20.0, follow_redirects=True)

BASE = "https://gcc.luluhypermarket.com"

h = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Referer": "https://www.luluhypermarket.com/",
    "Origin": "https://www.luluhypermarket.com",
}

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 1. Explore the API endpoints we found
# ============================================================
print("=" * 60)
print("LULU API EXPLORATION")
print("=" * 60)

# Try various endpoint patterns
endpoints = [
    "/api/client/widgets/home-slider-sa/",
    "/api/client/widgets/delivery-mode/",
    "/api/hot-food-config",
    "/api/sentry",
    "/api/client/categories/",
    "/api/client/products/",
    "/api/client/search/",
    "/api/client/catalog/",
    "/api/client/menu/",
    "/api/client/navigation/",
    "/api/client/widgets/",
    "/api/v1/categories/",
    "/api/v1/products/",
    "/api/v2/categories/",
    "/api/v2/products/",
    "/api/categories/",
    "/api/products/",
    "/api/search/",
    "/api/catalog/",
    "/api/menu/",
    "/api/client/widgets/home-page-sa/",
    "/api/client/widgets/home-sa/",
    "/api/client/widgets/mega-menu-sa/",
    "/api/client/widgets/categories-sa/",
    "/api/client/widgets/menu-sa/",
    "/api/client/widgets/navigation-sa/",
]

for ep in endpoints:
    try:
        r = client.get(f"{BASE}{ep}", headers=h, timeout=8)
        if r.status_code != 404 and len(r.content) > 50:
            print(f"  [{r.status_code}] {ep} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        print(f"    Keys: {list(d.keys())[:10]}")
                        for k in ["products", "items", "data", "results", "categories", "widgets", "menu"]:
                            if k in d:
                                val = d[k]
                                if isinstance(val, list):
                                    print(f"    .{k} = List[{len(val)}]")
                                    if val and isinstance(val[0], dict):
                                        print(f"    First keys: {list(val[0].keys())[:12]}")
                                elif isinstance(val, dict):
                                    print(f"    .{k} keys = {list(val.keys())[:10]}")
                    elif isinstance(d, list):
                        print(f"    Array[{len(d)}]")
                        if d and isinstance(d[0], dict):
                            print(f"    First keys: {list(d[0].keys())[:12]}")
                    save(f"lulu_api_{ep.strip('/').replace('/', '_')}.json", d)
                except:
                    pass
    except Exception as e:
        if "timeout" not in str(e).lower():
            print(f"  [{type(e).__name__}] {ep}")

# ============================================================
# 2. Try Akinon API (Lulu uses Akinon platform)
# ============================================================
print("\n" + "=" * 60)
print("LULU AKINON API")
print("=" * 60)

akinon_base = "https://luluhypermarket.akinoncloud.com"
akinon_endpoints = [
    "/api/v1/products/",
    "/api/v1/categories/",
    "/api/v1/search/?q=rice",
    "/api/v2/products/",
    "/api/v2/categories/",
    "/api/catalogue/products/",
    "/api/catalogue/categories/",
]

for ep in akinon_endpoints:
    try:
        r = client.get(f"{akinon_base}{ep}", headers=h, timeout=8)
        if r.status_code != 404 and len(r.content) > 50:
            print(f"  [{r.status_code}] {ep} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    print(f"    Preview: {json.dumps(d, ensure_ascii=False)[:300]}")
                except:
                    pass
    except:
        pass

# ============================================================
# 3. Use Playwright to intercept Lulu product API calls
# ============================================================
print("\n" + "=" * 60)
print("LULU BROWSER INTERCEPT")
print("=" * 60)

client.close()

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        locale="en-SA",
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    )

    all_responses = []

    def handle_response(response):
        url = response.url
        if response.status == 200:
            ct = response.headers.get("content-type", "")
            if "json" in ct:
                try:
                    body = response.body()
                    if len(body) > 50:
                        data = response.json()
                        all_responses.append({"url": url, "data": data, "size": len(body)})
                except:
                    pass

    page = context.new_page()
    page.on("response", handle_response)

    # Load homepage and click on a category
    print("  Loading Lulu homepage...")
    page.goto("https://www.luluhypermarket.com/en-sa", timeout=60000, wait_until="networkidle")
    page.wait_for_timeout(3000)

    print(f"  Intercepted {len(all_responses)} responses")
    for r in all_responses:
        print(f"    {r['url'][:100]} size={r['size']}")

    # Try clicking on category links
    all_responses.clear()
    print("\n  Looking for category/product links on page...")

    # Get all links on the page
    links = page.evaluate("""() => {
        const links = Array.from(document.querySelectorAll('a[href]'));
        return links.map(a => ({href: a.href, text: a.textContent.trim().substring(0, 50)}))
            .filter(l => l.href.includes('/en-sa/') && (l.href.includes('/c/') || l.href.includes('grocery') || l.href.includes('food')))
            .slice(0, 20);
    }""")
    print(f"  Found {len(links)} category links")
    for l in links[:10]:
        print(f"    {l['text']}: {l['href'][:80]}")

    # Navigate to first category link
    if links:
        cat_url = links[0]["href"]
        print(f"\n  Navigating to: {cat_url}")
        all_responses.clear()
        page.goto(cat_url, timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)

        print(f"  Intercepted {len(all_responses)} responses")
        for r in all_responses:
            print(f"    {r['url'][:100]} size={r['size']}")
            if isinstance(r["data"], dict):
                keys = list(r["data"].keys())[:10]
                print(f"      Keys: {keys}")

        # Check for products in page HTML
        html = page.content()
        if "__NEXT_DATA__" in html:
            print("\n  Found __NEXT_DATA__!")
            nd = page.evaluate("() => window.__NEXT_DATA__")
            save("lulu_next_data.json", nd)
            if isinstance(nd, dict):
                pp = nd.get("props", {}).get("pageProps", {})
                print(f"    pageProps keys: {list(pp.keys())[:15]}")

    # Try scrolling to trigger lazy load
    all_responses.clear()
    print("\n  Scrolling page to trigger lazy loading...")
    for i in range(5):
        page.evaluate("window.scrollBy(0, 1000)")
        page.wait_for_timeout(1000)
    print(f"  After scrolling: {len(all_responses)} new responses")
    for r in all_responses:
        print(f"    {r['url'][:100]} size={r['size']}")

    page.close()
    browser.close()

print("\n=== DONE ===")
