#!/usr/bin/env python3
"""Farm: Check shop_online page + go.farm.com.sa SPA"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, re
from playwright.sync_api import sync_playwright

os.makedirs("data", exist_ok=True)

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        locale="ar-SA",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

    all_api = []
    def intercept(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if response.status == 200 and "json" in ct:
            try:
                body = response.body()
                if len(body) > 50:
                    data = response.json()
                    all_api.append({"url": url, "data": data, "size": len(body)})
            except:
                pass

    page = context.new_page()
    page.on("response", intercept)

    # 1. Check shop_online page
    print("=" * 60)
    print("FARM - Shop Online page")
    print("=" * 60)

    page.goto("https://www.farm.com.sa/ar/shop_online", timeout=30000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    print(f"  Title: {page.title()}")
    print(f"  URL: {page.url}")
    print(f"  API: {len(all_api)} responses")
    for r in all_api[:5]:
        print(f"    {r['url'][:80]} size={r['size']}")

    html = page.content()
    print(f"  HTML: {len(html)} bytes")

    # Check for app store links
    links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a[href]'))
            .map(a => ({href: a.href, text: a.textContent.trim().substring(0, 50)}))
            .slice(0, 20);
    }""")
    for l in links:
        if any(k in l["href"].lower() for k in ["app", "play.google", "apple", "store", "product", "shop"]):
            print(f"  Link: {l['text']}: {l['href'][:80]}")

    # 2. Try loading go.farm.com.sa with more patience
    print("\n" + "=" * 60)
    print("FARM - go.farm.com.sa SPA")
    print("=" * 60)

    all_api.clear()
    try:
        page.goto("https://go.farm.com.sa", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        print(f"  Title: {page.title()}")
        print(f"  URL: {page.url}")
        print(f"  API: {len(all_api)} responses")

        html2 = page.content()
        print(f"  HTML: {len(html2)} bytes")

        # Check body text
        body_text = page.evaluate("() => document.body.innerText.substring(0, 500)")
        print(f"  Body: {body_text[:200]}")

        # Check for any data
        if "__NEXT_DATA__" in html2:
            print("  Found __NEXT_DATA__!")

        # Extract any API URLs from the HTML
        api_urls = re.findall(r'https?://[^\s"\'>]+(?:api|product|categor)[^\s"\'>]*', html2)
        print(f"  API URLs in HTML: {len(api_urls)}")
        for a in api_urls[:10]:
            print(f"    {a}")

    except Exception as e:
        print(f"  ERR: {type(e).__name__}: {e}")

    page.close()
    browser.close()

print("\n=== DONE ===")
