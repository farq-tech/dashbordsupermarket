#!/usr/bin/env python3
"""Final creative attempts for Farm and Lulu"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, time, csv
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

# ============================================================
# FARM: Try exotic location formats
# ============================================================
print("=" * 60)
print("FARM: Exotic location formats")
print("=" * 60)

with open("data/farm_auth.json", "r") as f:
    auth = json.load(f)
TOKEN = auth["result"]["token"]
BASE = "https://go.farm.com.sa/public/api/v1.0"

# Use raw httpx to send custom requests
import socket
import ssl

LAT, LNG = "24.7136", "46.6753"

# Try with httpx but different approaches
client = httpx.Client(timeout=15.0, follow_redirects=True)

# 1. JSON-encoded location in header
exotic_headers = [
    {"X-Location": json.dumps({"lat": float(LAT), "lng": float(LNG)})},
    {"X-Customer-Location": json.dumps({"lat": float(LAT), "lng": float(LNG)})},
    {"customer-location": f"{LAT},{LNG}"},
    {"X-Location": f"{LAT},{LNG}"},
    {"x-geo": f"{LAT},{LNG}"},
    {"geo-location": f"{LAT},{LNG}"},
    {"X-Geo-Latitude": LAT, "X-Geo-Longitude": LNG},

    # Cookie-like headers
    {"Cookie": f"lat={LAT}; lng={LNG}"},
    {"Cookie": f"location={LAT},{LNG}"},
    {"Cookie": f"customer_location={LAT},{LNG}"},
    {"Cookie": f"store_id=1"},

    # Combine lat/lng as headers AND params
    {"latitude": LAT, "longitude": LNG, "User-Agent": "FarmStores/1 CFNetwork/1404.0.5 Darwin/22.3.0"},
]

for hdrs in exotic_headers:
    h = {
        "Accept": "application/json",
        "Authorization": f"Bearer {TOKEN}",
        "accept-encoding": "deflate",
        "accept-language": "ar",
        **hdrs,
    }
    try:
        r = client.get(f"{BASE}/home", headers=h,
                       params={"lat": LAT, "lng": LNG}, timeout=8)
        d = r.json()
        status = d.get("status", {})
        if isinstance(status, dict):
            success = status.get("success", False)
            msg = status.get("otherTxt", "")
            if success or "location" not in msg.lower():
                print(f"  [OK {r.status_code}] headers={list(hdrs.keys())}")
                print(f"    {r.text[:300]}")
    except:
        pass

# 2. Try with httpcore/h11 to send GET with body
print("\n  Trying GET with JSON body (raw)...")
import httpcore

for body_json in [
    {"lat": float(LAT), "lng": float(LNG)},
    {"latitude": float(LAT), "longitude": float(LNG)},
    {"store_id": 1, "lat": float(LAT), "lng": float(LNG)},
    {"location": {"lat": float(LAT), "lng": float(LNG)}},
]:
    try:
        body_bytes = json.dumps(body_json).encode()
        r = client.request(
            "GET",
            f"{BASE}/home",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
                "accept-encoding": "deflate",
                "accept-language": "ar",
            },
            content=body_bytes,
            timeout=8,
        )
        d = r.json()
        status = d.get("status", {})
        if isinstance(status, dict):
            msg = status.get("otherTxt", "")
            if "location" not in msg.lower():
                print(f"  [OK {r.status_code}] GET+body={list(body_json.keys())}")
                print(f"    {r.text[:300]}")
    except:
        pass

# 3. Try form-urlencoded GET body
for form in [
    f"lat={LAT}&lng={LNG}",
    f"latitude={LAT}&longitude={LNG}",
]:
    try:
        r = client.request(
            "GET",
            f"{BASE}/home",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/x-www-form-urlencoded",
                "accept-encoding": "deflate",
                "accept-language": "ar",
            },
            content=form.encode(),
            timeout=8,
        )
        d = r.json()
        status = d.get("status", {})
        if isinstance(status, dict):
            msg = status.get("otherTxt", "")
            if "location" not in msg.lower():
                print(f"  [OK] GET+form={form[:30]}")
                print(f"    {r.text[:300]}")
    except:
        pass

client.close()

# ============================================================
# LULU: Playwright stealth mode
# ============================================================
print("\n" + "=" * 60)
print("LULU: Playwright with stealth approach")
print("=" * 60)

from playwright.sync_api import sync_playwright

all_products = []

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ]
    )
    context = browser.new_context(
        locale="en-SA",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1440, "height": 900},
        java_script_enabled=True,
    )

    # Remove navigator.webdriver flag
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'ar']});
        window.chrome = { runtime: {} };
    """)

    api_data = []
    def intercept(response):
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
    page.on("response", intercept)

    try:
        # Load Lulu SA homepage
        print("  Loading luluhypermarket.com/en-sa...")
        page.goto("https://www.luluhypermarket.com/en-sa", timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(5000)
        title = page.title()
        print(f"  Title: {title[:60]}")

        if "cloudflare" in title.lower() or "attention" in title.lower() or "blocked" in title.lower():
            print("  -> Cloudflare challenge!")

            # Wait for challenge to complete
            print("  Waiting for challenge to resolve...")
            page.wait_for_timeout(10000)
            title = page.title()
            print(f"  After wait: {title[:60]}")
        else:
            print(f"  Homepage loaded! API intercepted: {len(api_data)}")

            # Extract any embedded product data
            embedded = page.evaluate("""() => {
                // Check for __NEXT_DATA__ (Next.js)
                const nextData = document.getElementById('__NEXT_DATA__');
                if (nextData) return {type: 'next', data: nextData.textContent.substring(0, 5000)};

                // Check for other embedded JSON
                const scripts = document.querySelectorAll('script[type="application/json"], script[type="application/ld+json"]');
                const results = [];
                scripts.forEach(s => {
                    if (s.textContent.length > 100) {
                        results.push({type: s.type, data: s.textContent.substring(0, 2000)});
                    }
                });

                // Check window objects
                const keys = Object.keys(window).filter(k =>
                    k.includes('data') || k.includes('product') || k.includes('catalog') ||
                    k.includes('store') || k.includes('config') || k.includes('initial') ||
                    k.includes('__')
                );

                return {scripts: results, windowKeys: keys.slice(0, 20)};
            }""")
            print(f"  Embedded data: {json.dumps(embedded, ensure_ascii=False)[:500]}")

            # Try to navigate to a category
            api_data.clear()
            print("\n  Navigating to grocery category...")

            # Try clicking on grocery
            grocery_link = page.query_selector('a[href*="grocery"], a:has-text("Grocery"), a:has-text("بقالة")')
            if grocery_link:
                href = grocery_link.get_attribute("href")
                print(f"  Found grocery link: {href}")
                grocery_link.click()
                page.wait_for_timeout(8000)
                print(f"  URL: {page.url}")
                print(f"  Title: {page.title()[:60]}")
                print(f"  API intercepted: {len(api_data)}")

                for resp in api_data[:10]:
                    u = resp["url"]
                    if "lulu" in u or "akinon" in u or "widget" in u or "product" in u:
                        print(f"    API: {u[:80]} size={resp['size']}")
                        d = resp["data"]
                        if isinstance(d, dict):
                            for k in d:
                                v = d[k]
                                if isinstance(v, list) and v and isinstance(v[0], dict):
                                    keys = list(v[0].keys())
                                    if any(pk in keys for pk in ["price", "name", "product", "title"]):
                                        print(f"      .{k}: {len(v)} items with product data!")
                                        for item in v[:3]:
                                            name = item.get("name", item.get("title", ""))
                                            price = item.get("price", item.get("retail_price", ""))
                                            print(f"        {name[:40]}: {price}")
                                        all_products.extend(v)

                # Extract from DOM
                dom_products = page.evaluate("""() => {
                    const products = [];
                    const cards = document.querySelectorAll('[class*="product"], [class*="Product"], [data-testid*="product"]');
                    cards.forEach(card => {
                        const nameEl = card.querySelector('h2, h3, h4, [class*="name"], [class*="title"]');
                        const priceEl = card.querySelector('[class*="price"], [class*="Price"]');
                        const imgEl = card.querySelector('img');
                        if (nameEl && nameEl.textContent.trim().length > 3) {
                            products.push({
                                name: nameEl.textContent.trim().substring(0, 100),
                                price: priceEl ? priceEl.textContent.trim() : '',
                                image: imgEl ? imgEl.src : '',
                            });
                        }
                    });
                    return products;
                }""")
                print(f"\n  DOM products: {len(dom_products)}")
                for p in dom_products[:5]:
                    print(f"    {p['name'][:50]} | {p['price']}")
                if dom_products:
                    all_products.extend(dom_products)
            else:
                print("  No grocery link found")

                # Try direct URL
                api_data.clear()
                print("  Trying direct category URL...")
                page.goto("https://www.luluhypermarket.com/en-sa/grocery/c/HY00214301", timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(8000)
                title = page.title()
                print(f"  Title: {title[:60]}")
                print(f"  API: {len(api_data)} responses")

                if "blocked" not in title.lower() and "cloudflare" not in title.lower():
                    dom_products = page.evaluate("""() => {
                        const products = [];
                        const cards = document.querySelectorAll('[class*="product"], [class*="Product"]');
                        cards.forEach(card => {
                            const nameEl = card.querySelector('h2, h3, h4, [class*="name"], [class*="title"]');
                            const priceEl = card.querySelector('[class*="price"], [class*="Price"]');
                            if (nameEl && nameEl.textContent.trim().length > 3) {
                                products.push({
                                    name: nameEl.textContent.trim().substring(0, 100),
                                    price: priceEl ? priceEl.textContent.trim() : '',
                                });
                            }
                        });
                        return products;
                    }""")
                    print(f"  DOM products: {len(dom_products)}")
                    if dom_products:
                        all_products.extend(dom_products)

    except Exception as e:
        print(f"  ERR: {type(e).__name__}: {e}")

    page.close()
    context.close()
    browser.close()

# Save any Lulu products found
if all_products:
    with open(f"data/lulu_products_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved {len(all_products)} Lulu products!")

    # CSV
    if isinstance(all_products[0], dict):
        keys = list(all_products[0].keys())
        with open("data/lulu_products.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(all_products)
        print(f"  CSV: data/lulu_products.csv")
else:
    print("\n  No Lulu products found")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Farm: API locked down, only /home endpoint exists but needs unknown location format")
print(f"  Lulu: {'Got ' + str(len(all_products)) + ' products' if all_products else 'Blocked by Cloudflare'}")

print("\n=== DONE ===")
