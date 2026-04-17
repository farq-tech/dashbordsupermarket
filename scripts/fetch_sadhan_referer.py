#!/usr/bin/env python3
"""Sadhan: Eldokan API with correct Referer header"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv, time
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
client = httpx.Client(timeout=20.0, follow_redirects=True)

BASE = "https://masterapi.witheldokan.com"

h = {
    "Accept": "application/json",
    "User-Agent": "okhttp/5.0.0",
    "Referer": "https://alsadhan.witheldokan.com/",
    "Origin": "https://alsadhan.witheldokan.com",
    "x-platform": "android",
}

def save(name, data):
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 1. Try various API endpoints with Referer
# ============================================================
print("=" * 60)
print("SADHAN - Eldokan API with Referer")
print("=" * 60)

endpoints = [
    f"{BASE}/api/home",
    f"{BASE}/api/admin/home",
    f"{BASE}/api/store/alsadhan/home",
    f"{BASE}/api/store/alsadhan/categories",
    f"{BASE}/api/store/alsadhan/products",
    f"{BASE}/api/admin/categories",
    f"{BASE}/api/admin/products",
    f"{BASE}/api/admin/profile",
    f"{BASE}/api/admin/configurations",
    f"{BASE}/api/v1/home",
    f"{BASE}/api/v1/categories",
    f"{BASE}/api/v1/products",
    f"{BASE}/api/v2/home",
    f"{BASE}/api/v2/categories",
    f"{BASE}/api/v2/products",
    f"{BASE}/api/client/home",
    f"{BASE}/api/client/categories",
    f"{BASE}/api/client/products",
    # Common Eldokan patterns
    f"{BASE}/api/stores",
    f"{BASE}/api/vendors",
    f"{BASE}/api/catalog",
    f"{BASE}/api/menu",
]

for url in endpoints:
    try:
        r = client.get(url, headers=h, timeout=8)
        if len(r.content) > 50:
            print(f"  [{r.status_code}] {url.replace(BASE, '')} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        # Skip error responses
                        if "errors" in d and d.get("code") in [401, 403, 422]:
                            print(f"    Error: {d.get('message', '')[:100]}")
                            continue
                        print(f"    Keys: {list(d.keys())[:10]}")
                        for k in d:
                            val = d[k]
                            if isinstance(val, list) and len(val) > 0:
                                print(f"    .{k} = List[{len(val)}]")
                                if isinstance(val[0], dict):
                                    print(f"    First keys: {list(val[0].keys())[:12]}")
                            elif isinstance(val, dict) and len(val) > 0:
                                print(f"    .{k} = Dict keys: {list(val.keys())[:8]}")
                        save(f"sadhan_api_{url.split('/')[-1]}.json", d)
                except:
                    pass
    except Exception as e:
        if "timeout" not in str(e).lower():
            print(f"  [ERR] {url.replace(BASE, '')}: {type(e).__name__}")

# ============================================================
# 2. Try the sadhanmarketapi subdomain with Referer
# ============================================================
print("\n" + "=" * 60)
print("SADHAN - sadhanmarketapi with Referer")
print("=" * 60)

BASE2 = "https://sadhanmarketapi.witheldokan.com"
h2 = {**h, "Referer": "https://alsadhan.witheldokan.com/", "Origin": "https://alsadhan.witheldokan.com"}

endpoints2 = [
    f"{BASE2}/api/home",
    f"{BASE2}/api/categories",
    f"{BASE2}/api/products",
    f"{BASE2}/api/catalog",
    f"{BASE2}/api/menu",
    f"{BASE2}/api/store",
    f"{BASE2}/api/v1/home",
    f"{BASE2}/api/v1/categories",
    f"{BASE2}/api/v1/products",
]

for url in endpoints2:
    try:
        r = client.get(url, headers=h2, timeout=10)
        if len(r.content) > 50:
            print(f"  [{r.status_code}] {url.replace(BASE2, '')} size={len(r.content)}")
            if r.status_code == 200:
                try:
                    d = r.json()
                    if isinstance(d, dict):
                        if "errors" in d and d.get("code") in [401, 403, 422]:
                            print(f"    Error: {d.get('message', '')[:100]}")
                            continue
                        print(f"    Keys: {list(d.keys())[:10]}")
                        for k in d:
                            val = d[k]
                            if isinstance(val, list) and len(val) > 0:
                                print(f"    .{k} = List[{len(val)}]")
                                if isinstance(val[0], dict):
                                    print(f"    First keys: {list(val[0].keys())[:12]}")
                                    print(f"    Sample: {json.dumps(val[0], ensure_ascii=False)[:300]}")
                            elif isinstance(val, dict) and len(val) > 0:
                                print(f"    .{k} = Dict keys: {list(val.keys())[:8]}")
                        save(f"sadhan_api2_{url.split('/')[-1]}.json", d)
                except:
                    pass
    except Exception as e:
        if "timeout" not in str(e).lower():
            print(f"  [ERR] {url.replace(BASE2, '')}: {type(e).__name__}")
        else:
            print(f"  [TIMEOUT] {url.replace(BASE2, '')}")

# ============================================================
# 3. Use Playwright to load the admin panel and intercept API
# ============================================================
print("\n" + "=" * 60)
print("SADHAN - Browser intercept (admin panel)")
print("=" * 60)

client.close()

from playwright.sync_api import sync_playwright

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

    # Load the admin panel - it might make public API calls on load
    page.goto("https://alsadhan.witheldokan.com", timeout=30000, wait_until="networkidle")
    page.wait_for_timeout(5000)

    print(f"  Intercepted {len(all_api)} JSON responses")
    for resp in all_api:
        url = resp["url"]
        data = resp["data"]
        print(f"  {url[:80]} size={resp['size']}")
        if isinstance(data, dict):
            keys = list(data.keys())[:10]
            print(f"    Keys: {keys}")
            # Check if it's product/category data
            for k in ["products", "items", "data", "categories", "home"]:
                if k in data:
                    val = data[k]
                    if isinstance(val, list) and val:
                        print(f"    .{k} = List[{len(val)}]")
                        if isinstance(val[0], dict):
                            print(f"    First keys: {list(val[0].keys())[:12]}")
                            print(f"    Sample: {json.dumps(val[0], ensure_ascii=False)[:200]}")
            save(f"sadhan_browser_{all_api.index(resp)}.json", data)

    page.close()
    browser.close()

print("\n=== DONE ===")
