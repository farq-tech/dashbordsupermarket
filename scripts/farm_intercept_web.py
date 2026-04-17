#!/usr/bin/env python3
"""Farm: Use Playwright to intercept actual API calls from Farm web/mobile app"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, time
import httpx
from playwright.sync_api import sync_playwright

os.makedirs("data", exist_ok=True)

# Also try different API versions and base paths directly
print("=" * 60)
print("PART 1: Try different API versions / base paths")
print("=" * 60)

with open("data/farm_auth.json", "r") as f:
    auth = json.load(f)
TOKEN = auth["result"]["token"]

client = httpx.Client(timeout=15.0, follow_redirects=True)
h = {
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}",
    "accept-encoding": "deflate",
    "accept-language": "ar",
    "User-Agent": "FarmStores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
}

LAT, LNG = "24.7136", "46.6753"

# Try different API versions
for ver in ["v1.0", "v1.1", "v1.2", "v2.0", "v2", "v3", "v1"]:
    url = f"https://go.farm.com.sa/public/api/{ver}/home"
    try:
        r = client.get(url, headers=h, params={"lat": LAT, "lng": LNG}, timeout=8)
        if "route" not in r.text.lower() or "not found" not in r.text.lower():
            print(f"  [{r.status_code}] {ver}/home: {r.text[:200]}")
    except:
        pass

# Try without /public prefix
for prefix in ["api/v1.0", "api/v1", "api/v2", "v1", "v2"]:
    url = f"https://go.farm.com.sa/{prefix}/home"
    try:
        r = client.get(url, headers=h, params={"lat": LAT, "lng": LNG}, timeout=8)
        text = r.text[:200]
        if len(r.content) > 50 and "not found" not in text.lower()[:50]:
            print(f"  [{r.status_code}] /{prefix}/home: {text}")
    except:
        pass

client.close()

# ============================================================
# PART 2: Playwright intercept on go.farm.com.sa
# ============================================================
print("\n" + "=" * 60)
print("PART 2: Playwright intercept on go.farm.com.sa")
print("=" * 60)

api_calls = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # Override geolocation to Riyadh
    context = browser.new_context(
        locale="ar-SA",
        geolocation={"latitude": 24.7136, "longitude": 46.6753},
        permissions=["geolocation"],
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
        viewport={"width": 375, "height": 812},
    )

    def intercept_all(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if "go.farm" in url or "farm.com" in url:
            try:
                status = response.status
                size = len(response.body()) if status < 400 else 0
                api_calls.append({
                    "url": url,
                    "status": status,
                    "ct": ct,
                    "size": size,
                })
                if "json" in ct and size > 50:
                    try:
                        data = response.json()
                        api_calls[-1]["data"] = data
                    except:
                        pass
            except:
                api_calls.append({"url": url, "status": response.status, "ct": ct, "size": 0})

    def intercept_request(request):
        url = request.url
        if "api" in url.lower() and "farm" in url.lower():
            headers = dict(request.headers)
            api_calls.append({
                "type": "REQUEST",
                "url": url,
                "method": request.method,
                "headers": {k: v for k, v in headers.items() if k.lower() not in ["cookie", "sec-"]},
                "post_data": request.post_data[:500] if request.post_data else None,
            })

    page = context.new_page()
    page.on("response", intercept_all)
    page.on("request", intercept_request)

    try:
        # Load the go.farm.com.sa mobile web
        print("  Loading go.farm.com.sa...")
        page.goto("https://go.farm.com.sa", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        print(f"  Title: {page.title()}")
        print(f"  URL: {page.url}")

        body = page.evaluate("() => document.body ? document.body.innerText.substring(0, 300) : ''")
        print(f"  Body: {body[:200]}")

        html = page.content()
        print(f"  HTML: {len(html)} bytes")

        # Check for any app-like redirects or deep links
        all_links = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href], link[href]'))
                .map(a => ({href: a.href || a.getAttribute('href'), rel: a.rel || '', text: (a.textContent || '').trim().substring(0, 40)}))
                .filter(l => l.href && l.href.length > 5)
                .slice(0, 30);
        }""")
        print(f"  Links: {len(all_links)}")
        for l in all_links:
            print(f"    {l['text']}: {l['href'][:80]}")

        # Check for any JavaScript that reveals API structure
        scripts = page.evaluate("""() => {
            const scripts = document.querySelectorAll('script');
            const texts = [];
            for (const s of scripts) {
                const src = s.src || '';
                const text = s.textContent || '';
                if (src) texts.push({type: 'src', value: src});
                if (text.length > 20 && text.length < 5000) texts.push({type: 'inline', value: text.substring(0, 500)});
            }
            return texts;
        }""")
        print(f"\n  Scripts: {len(scripts)}")
        for s in scripts:
            if "api" in s["value"].lower() or "lat" in s["value"].lower() or "location" in s["value"].lower():
                print(f"    [{s['type']}] {s['value'][:200]}")

    except Exception as e:
        print(f"  ERR: {e}")

    # Try Farm shop online
    api_calls.clear()
    try:
        print("\n  Loading farm.com.sa/ar/shop_online...")
        page.goto("https://www.farm.com.sa/ar/shop_online", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        print(f"  Title: {page.title()}")

        # Look for any go.farm links
        go_links = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href*="go.farm"], a[href*="farm.com.sa/app"], a[href*="farm.com.sa/store"]'))
                .map(a => ({href: a.href, text: a.textContent.trim().substring(0, 40)}));
        }""")
        print(f"  go.farm links: {len(go_links)}")
        for l in go_links:
            print(f"    {l['text']}: {l['href']}")

    except Exception as e:
        print(f"  ERR: {e}")

    page.close()
    context.close()
    browser.close()

print(f"\n  Total API calls intercepted: {len(api_calls)}")
for call in api_calls:
    if call.get("type") == "REQUEST":
        print(f"  >> {call['method']} {call['url'][:80]}")
        if call.get("headers"):
            for k, v in call["headers"].items():
                if k.lower() in ["latitude", "longitude", "x-lat", "x-lng", "location", "x-location"]:
                    print(f"     H: {k}: {v}")
        if call.get("post_data"):
            print(f"     Body: {call['post_data'][:200]}")
    else:
        print(f"  <- [{call.get('status')}] {call['url'][:80]} ct={call.get('ct','')[:30]} sz={call.get('size', 0)}")

# Save all intercepted data
if api_calls:
    with open("data/farm_api_intercept.json", "w", encoding="utf-8") as f:
        json.dump([c for c in api_calls if "data" not in c or c.get("size", 0) < 10000], f, ensure_ascii=False, indent=2, default=str)

print("\n=== DONE ===")
