#!/usr/bin/env python3
"""Final merge: Panda + Tamimi into unified CSV/JSON with full report"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os, csv
from datetime import datetime

os.makedirs("data", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

# ============================================================
# Load existing data
# ============================================================
print("=" * 60)
print("FINAL MERGE - All Store Products")
print("=" * 60)

all_rows = []
fieldnames = None

# 1. PANDA
panda_csv = "data/all_products_full.csv"
if os.path.exists(panda_csv):
    with open(panda_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        panda_rows = list(reader)
        fieldnames = reader.fieldnames
    print(f"  Panda: {len(panda_rows)} rows")
    all_rows.extend(panda_rows)
else:
    print(f"  WARNING: {panda_csv} not found!")
    panda_rows = []

# 2. TAMIMI
tamimi_csv = "data/tamimi_products.csv"
if os.path.exists(tamimi_csv):
    with open(tamimi_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        tamimi_rows = list(reader)
        if not fieldnames:
            fieldnames = reader.fieldnames
    print(f"  Tamimi: {len(tamimi_rows)} rows")
    # Ensure tamimi rows match panda field names
    for row in tamimi_rows:
        unified = {}
        for fn in fieldnames:
            unified[fn] = row.get(fn, "")
        all_rows.append(unified)
else:
    print(f"  WARNING: {tamimi_csv} not found!")

print(f"\n  TOTAL: {len(all_rows)} rows")

# ============================================================
# Store status report
# ============================================================
store_status = {
    "panda": {
        "status": "DONE",
        "products": len(panda_rows) if 'panda_rows' in dir() else 0,
        "method": "Direct API (api.panda.sa/v3/products)",
        "notes": "Full product catalog with pagination"
    },
    "tamimi": {
        "status": "DONE",
        "products": len(tamimi_rows) if 'tamimi_rows' in dir() else 0,
        "method": "SSR scraping (__NEXT_DATA__ from shop.tamimimarkets.com)",
        "notes": "2,815 unique products across 165 categories, expanded to rows with variants"
    },
    "carrefour": {
        "status": "SKIPPED",
        "products": 0,
        "method": "N/A",
        "notes": "Skipped per user request. Akamai bot protection blocks all API/browser access."
    },
    "lulu": {
        "status": "BLOCKED",
        "products": 0,
        "method": "Tried: Akinon API, browser DOM scraping, Playwright intercept",
        "notes": "Cloudflare blocks category/product pages. Akinon API returns 405/401. App-only access."
    },
    "farm": {
        "status": "DEAD",
        "products": 0,
        "method": "Tried: go.farm.com.sa API, website scraping",
        "notes": "All API v1.0 routes removed (Laravel 'route not found'). Website is corporate only."
    },
    "ramez": {
        "status": "DEAD",
        "products": 0,
        "method": "Tried: risteh.com API with apikey",
        "notes": "Server unreachable. All connection attempts timeout/fail."
    },
    "sadhan": {
        "status": "DEAD",
        "products": 0,
        "method": "Tried: Eldokan API, browser intercept",
        "notes": "API server timeout. Admin panel only (requires auth). No public store."
    },
    "spar": {
        "status": "DEAD",
        "products": 0,
        "method": "Tried: website check",
        "notes": "Corporate website only, no e-commerce or product API."
    },
}

# ============================================================
# Export merged data
# ============================================================
if all_rows and fieldnames:
    # CSV
    merged_csv = "data/all_stores_products.csv"
    with open(merged_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\n  CSV: {merged_csv}")

    # JSON
    stores_summary = {}
    for row in all_rows:
        store = row.get("store", "unknown")
        if store not in stores_summary:
            stores_summary[store] = {"count": 0, "store_name": row.get("store_name", "")}
        stores_summary[store]["count"] += 1

    merged_json = "data/all_stores_products.json"
    with open(merged_json, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_products": len(all_rows),
                "stores_with_data": stores_summary,
                "all_stores_status": store_status,
                "fieldnames": fieldnames,
            },
            "products": all_rows,
        }, f, ensure_ascii=False, indent=2)
    print(f"  JSON: {merged_json}")

    # Summary by store
    print(f"\n  Products by store:")
    for store, info in sorted(stores_summary.items(), key=lambda x: -x[1]["count"]):
        print(f"    {info['store_name']} ({store}): {info['count']} rows")

    # Price analysis
    prices = []
    for r in all_rows:
        p = r.get("price", "")
        if p:
            try:
                prices.append(float(str(p).replace(",", "")))
            except:
                pass
    if prices:
        print(f"\n  Price range: {min(prices):.2f} - {max(prices):.2f} SAR")
        print(f"  Average price: {sum(prices)/len(prices):.2f} SAR")
        print(f"  Products with price: {len(prices)}/{len(all_rows)}")

# ============================================================
# Print final report
# ============================================================
print("\n" + "=" * 60)
print("STORE STATUS REPORT")
print("=" * 60)
for store, info in store_status.items():
    emoji = {"DONE": "+", "SKIPPED": "~", "BLOCKED": "!", "DEAD": "X"}[info["status"]]
    print(f"  [{emoji}] {store:12s} {info['status']:8s} {info['products']:6d} products")
    print(f"      Method: {info['method']}")
    print(f"      Notes: {info['notes']}")
    print()

total = sum(s["products"] for s in store_status.values())
print(f"  GRAND TOTAL: {total} product rows across {sum(1 for s in store_status.values() if s['products'] > 0)} stores")

print(f"\n  Output files:")
print(f"    data/all_stores_products.csv  ({len(all_rows)} rows)")
print(f"    data/all_stores_products.json")
print(f"    data/all_products_full.csv    (Panda only)")
print(f"    data/tamimi_products.csv      (Tamimi only)")

print("\n=== DONE ===")
