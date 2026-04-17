#!/usr/bin/env python3
"""Quick test remaining stores + merge Panda + Tamimi into unified output"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import os
import csv
import time
from datetime import datetime
import httpx

os.makedirs("data", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

client = httpx.Client(timeout=15.0, follow_redirects=True)

# ============================================================
# Quick test remaining stores (5 sec timeout each)
# ============================================================
print("=" * 60)
print("QUICK TEST: Remaining stores")
print("=" * 60)

stores_status = {}

# CARREFOUR
print("\n--- Carrefour ---")
try:
    r = client.get("https://www.carrefourksa.com/mafsau/ar/", headers={
        "Accept": "text/html", "User-Agent": "Mozilla/5.0"}, timeout=8)
    print(f"  Web: {r.status_code}, size={len(r.content)}")
    stores_status["carrefour"] = "Web loads but no public product API found"
except Exception as e:
    stores_status["carrefour"] = f"Error: {type(e).__name__}"
    print(f"  Error: {type(e).__name__}")

# LULU
print("\n--- Lulu ---")
try:
    r = client.get("https://www.luluhypermarket.com/en-sa", headers={
        "Accept": "text/html", "User-Agent": "Mozilla/5.0"}, timeout=8)
    print(f"  Web: {r.status_code}, size={len(r.content)}")
    stores_status["lulu"] = "Web loads but Akinon API requires auth (405 on all endpoints)"
except Exception as e:
    stores_status["lulu"] = f"Error: {type(e).__name__}"
    print(f"  Error: {type(e).__name__}")

# FARM
print("\n--- Farm ---")
try:
    r = client.get("https://go.farm.com.sa/public/api/v1.0/stores", headers={
        "Accept": "application/json"}, timeout=8)
    print(f"  API: {r.status_code}, size={len(r.content)}")
    if r.status_code == 200:
        stores_status["farm"] = "API returns errors (Laravel route not found)"
    else:
        stores_status["farm"] = f"HTTP {r.status_code}"
except Exception as e:
    stores_status["farm"] = f"Error: {type(e).__name__}"
    print(f"  Error: {type(e).__name__}")

# RAMEZ
print("\n--- Ramez ---")
ramez_h = {
    "Accept": "application/json",
    "apikey": "^~>h2q=m[h=>3?bU/!M'X!m~?4GjKJP{Q@y;~fa3Vjs/M#`8FuB;x[LKwJ&>gNrxBt8!5PZ:9QLuHBUtu{TPc2s]k74]Br?PGe6+NcFUT-8",
    "User-Agent": "Ramez/8 CFNetwork/1404.0.5 Darwin/22.3.0",
}
try:
    r = client.get("https://risteh.com/SA/GroceryStoreApi/api/v9/Home", headers=ramez_h, timeout=8)
    print(f"  API: {r.status_code}, size={len(r.content)}")
    if r.status_code == 200 and len(r.content) > 50:
        stores_status["ramez"] = "API accessible but needs deeper exploration"
        try:
            d = r.json()
            print(f"  Keys: {list(d.keys())[:10]}")
            print(f"  Preview: {json.dumps(d, ensure_ascii=False)[:500]}")
            # Try products
            r2 = client.get("https://risteh.com/SA/GroceryStoreApi/api/v9/Products/list",
                headers=ramez_h, timeout=8)
            print(f"  Products: {r2.status_code}, size={len(r2.content)}")
            if r2.status_code == 200 and len(r2.content) > 50:
                d2 = r2.json()
                print(f"  Products Keys: {list(d2.keys())[:10]}")
                stores_status["ramez"] = "Products API may work!"
        except:
            pass
    else:
        stores_status["ramez"] = f"HTTP {r.status_code}"
except Exception as e:
    stores_status["ramez"] = f"Error: {type(e).__name__}"
    print(f"  Error: {type(e).__name__}")

# SADHAN
print("\n--- Sadhan ---")
try:
    r = client.get("https://sadhanmarketapi.witheldokan.com/api/home", headers={
        "Accept": "application/json", "User-Agent": "okhttp/5.0.0"}, timeout=8)
    print(f"  API: {r.status_code}, size={len(r.content)}")
    if r.status_code == 200 and len(r.content) > 50:
        stores_status["sadhan"] = "API accessible"
        d = r.json()
        print(f"  Preview: {json.dumps(d, ensure_ascii=False)[:500]}")
    else:
        stores_status["sadhan"] = f"HTTP {r.status_code}"
except Exception as e:
    stores_status["sadhan"] = f"Error: {type(e).__name__}"
    print(f"  Error: {type(e).__name__}")

# SPAR
print("\n--- Spar ---")
try:
    r = client.get("https://www.spar.sa/", headers={
        "Accept": "text/html", "User-Agent": "Mozilla/5.0"}, timeout=8)
    print(f"  Web: {r.status_code}, size={len(r.content)}")
    stores_status["spar"] = f"HTTP {r.status_code}" if r.status_code != 200 else "Web loads but no product API found"
except Exception as e:
    stores_status["spar"] = f"Error: {type(e).__name__}"
    print(f"  Error: {type(e).__name__}")

print("\n\nStore Status Summary:")
for store, status in stores_status.items():
    print(f"  {store}: {status}")

client.close()

# ============================================================
# MERGE: Panda + Tamimi into unified files
# ============================================================
print("\n" + "=" * 60)
print("MERGING: Panda + Tamimi into unified CSV/JSON")
print("=" * 60)

# Load Panda products
panda_csv = "data/all_products_full.csv"
tamimi_csv = "data/tamimi_products.csv"

all_rows = []
fieldnames = None

# Read Panda CSV
if os.path.exists(panda_csv):
    with open(panda_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        panda_rows = list(reader)
        if not fieldnames:
            fieldnames = reader.fieldnames
    print(f"  Panda: {len(panda_rows)} rows")
    all_rows.extend(panda_rows)
else:
    print(f"  WARNING: {panda_csv} not found!")
    panda_rows = []

# Read Tamimi CSV
if os.path.exists(tamimi_csv):
    with open(tamimi_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        tamimi_rows = list(reader)
        if not fieldnames:
            fieldnames = reader.fieldnames
    print(f"  Tamimi: {len(tamimi_rows)} rows")
    # Ensure tamimi rows have same fields
    for row in tamimi_rows:
        unified = {}
        for fn in fieldnames:
            unified[fn] = row.get(fn, "")
        all_rows.append(unified)
else:
    print(f"  WARNING: {tamimi_csv} not found!")

print(f"\n  TOTAL MERGED: {len(all_rows)} rows")

if all_rows and fieldnames:
    # Write merged CSV
    merged_csv = "data/all_stores_products.csv"
    with open(merged_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"  Merged CSV: {merged_csv}")

    # Write merged JSON
    merged_json = "data/all_stores_products.json"
    stores_summary = {}
    for row in all_rows:
        store = row.get("store", "unknown")
        if store not in stores_summary:
            stores_summary[store] = {"count": 0, "store_name": row.get("store_name", "")}
        stores_summary[store]["count"] += 1

    with open(merged_json, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "total_rows": len(all_rows),
                "stores": stores_summary,
                "other_stores_status": stores_status,
            },
            "products": all_rows,
        }, f, ensure_ascii=False, indent=2)
    print(f"  Merged JSON: {merged_json}")

    # Summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    for store, info in stores_summary.items():
        print(f"  {info['store_name']} ({store}): {info['count']} rows")
    print(f"  TOTAL: {len(all_rows)} rows across {len(stores_summary)} stores")

    prices = [float(r["price"]) for r in all_rows if r.get("price") and r["price"].replace(".", "").replace("-","").isdigit()]
    if prices:
        print(f"  Overall price range: {min(prices):.2f} - {max(prices):.2f} SAR")

    print(f"\nOutput files:")
    print(f"  data/all_stores_products.csv ({len(all_rows)} rows)")
    print(f"  data/all_stores_products.json")
    print(f"  data/all_products_full.csv (Panda only)")
    print(f"  data/tamimi_products.csv (Tamimi only)")

print("\n=== ALL DONE ===")
