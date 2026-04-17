#!/usr/bin/env python3
"""
Farq Grocery API Server
Serves Fustog product data - 7 stores, 4,000+ products
Run: python server.py
"""

import csv
import json
import sys
import os
import re
import glob
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

PORT = int(os.environ.get("PORT", "8787"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# CORRECT store mapping (verified from Fustog NearestStores API probe)
# RID=1 Panda Express, RID=2 Panda, RID=3 Tamimi, RID=4 AlSadhan,
# RID=5 Othaim, RID=6 LuLu, RID=9 Carrefour
STORE_MAP = {
    "1": {"id": 1, "key": "panda_express", "name": "Panda Express", "nameAr": "بنده إكسبريس", "color": "#C53030"},
    "2": {"id": 2, "key": "panda",         "name": "Panda",          "nameAr": "بنده",          "color": "#E53E3E"},
    "3": {"id": 3, "key": "tamimi",        "name": "Tamimi",         "nameAr": "التميمي",        "color": "#D69E2E"},
    "4": {"id": 4, "key": "sadhan",        "name": "Al Sadhan",      "nameAr": "السدحان",        "color": "#2F855A"},
    "5": {"id": 5, "key": "othaim",        "name": "Othaim",         "nameAr": "العثيم",         "color": "#7B2D8E"},
    "6": {"id": 6, "key": "lulu",          "name": "LuLu",           "nameAr": "لولو",           "color": "#E31E24"},
    "7": {"id": 7, "key": "carrefour",     "name": "Carrefour",      "nameAr": "كارفور",         "color": "#2C5282"},
}

# Data
fustog_products = []   # list of product dicts with Prices field
categories = []
categories_map = {}


def find_latest_csv(pattern):
    """Find the most recently timestamped CSV matching pattern."""
    matches = sorted(glob.glob(os.path.join(DATA_DIR, pattern)), reverse=True)
    return matches[0] if matches else None


def load_data():
    global fustog_products, categories, categories_map

    print("Loading Fustog data from CSV files...")

    # Find newest enriched prices CSV
    prices_file = find_latest_csv("fustog_prices_enriched_long_*.csv")
    if not prices_file:
        print("  ERROR: No fustog_prices_enriched_long_*.csv found in data/")
        return

    print(f"  Using: {os.path.basename(prices_file)}")

    # Read prices into per-FID product dicts
    products_map = {}  # FID -> product dict

    with open(prices_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                fid = int(row.get("FID", 0))
                price = float(row.get("Price", 0) or 0)
                store_key = str(row.get("StoreKey", ""))
            except (ValueError, TypeError):
                continue

            if fid == 0 or price <= 0:
                continue

            if fid not in products_map:
                products_map[fid] = {
                    "FID": fid,
                    "TitleAr": row.get("TitleAr", ""),
                    "TitleEn": row.get("TitleEn", ""),
                    "BrandAR": row.get("BrandAR", ""),
                    "BrandEN": row.get("BrandEN", ""),
                    "CateguryAR": row.get("CateguryAR", ""),
                    "CateguryEN": row.get("CateguryEN", ""),
                    "AttrUnit": row.get("AttrUnit", ""),
                    "AttrVal": row.get("AttrVal", ""),
                    "ImageURL": row.get("ImageURL", ""),
                    "Prices": {},
                }
            products_map[fid]["Prices"][store_key] = price

    fustog_products = list(products_map.values())
    print(f"  Loaded {len(fustog_products)} products")

    # Build categories
    cat_set = defaultdict(lambda: {"count": 0, "nameEn": ""})
    for p in fustog_products:
        car = p.get("CateguryAR", "")
        cen = p.get("CateguryEN", "")
        if car:
            cat_set[car]["count"] += 1
            if cen:
                cat_set[car]["nameEn"] = cen

    categories = []
    for i, (name, info) in enumerate(sorted(cat_set.items(), key=lambda x: -x[1]["count"])):
        cat = {"id": i + 1, "nameAr": name, "name": info["nameEn"] or name, "count": info["count"]}
        categories.append(cat)
        categories_map[name] = cat

    print(f"  {len(categories)} categories")

    # Stats per store
    store_counts = defaultdict(int)
    for p in fustog_products:
        for sid, price in p.get("Prices", {}).items():
            if price and price > 0:
                store_counts[sid] += 1
    for sid, count in sorted(store_counts.items(), key=lambda x: int(x[0])):
        sname = STORE_MAP.get(sid, {}).get("nameAr", f"Store {sid}")
        print(f"  Store {sid} ({sname}): {count} products")


def search(query, category=None, limit=200):
    """Search products by Arabic/English name"""
    if not query:
        return fustog_products[:limit]

    query_lower = query.lower().strip()
    parts = query_lower.split()
    results = []

    for p in fustog_products:
        # Category filter
        if category and category != p.get("CateguryAR", ""):
            continue

        text = " ".join([
            p.get("TitleAr", ""),
            p.get("TitleEn", ""),
            p.get("BrandAR", ""),
            p.get("BrandEN", ""),
            p.get("CateguryAR", ""),
        ]).lower()

        if all(part in text for part in parts):
            # Relevance score
            score = 0
            tar = (p.get("TitleAr", "") or "").lower()
            ten = (p.get("TitleEn", "") or "").lower()
            for part in parts:
                if part in tar: score += 3
                if part in ten: score += 2
            results.append((score, p))

    results.sort(key=lambda x: -x[0])
    return [r[1] for r in results[:limit]]


def get_price_comparison(product):
    """Get price comparison across stores for a product"""
    prices = product.get("Prices", {})
    comparison = []
    for sid, price in prices.items():
        if price and price > 0:
            store = STORE_MAP.get(sid, {"name": f"Store {sid}", "nameAr": f"متجر {sid}", "color": "#666"})
            comparison.append({
                "storeId": sid,
                "storeName": store["name"],
                "storeNameAr": store["nameAr"],
                "storeColor": store["color"],
                "price": price,
            })
    comparison.sort(key=lambda x: x["price"])
    return comparison


def format_product(p):
    """Format a Fustog product for API response"""
    prices = get_price_comparison(p)
    lowest = prices[0]["price"] if prices else 0
    highest = prices[-1]["price"] if prices else 0
    savings = round(highest - lowest, 2) if len(prices) > 1 else 0

    return {
        "fid": p.get("FID"),
        "nameAr": p.get("TitleAr", ""),
        "nameEn": p.get("TitleEn", ""),
        "brandAr": p.get("BrandAR", ""),
        "brandEn": p.get("BrandEN", ""),
        "categoryAr": p.get("CateguryAR", ""),
        "categoryEn": p.get("CateguryEN", ""),
        "image": p.get("ImageURL", ""),
        "size": p.get("AttrVal", ""),
        "unit": p.get("AttrUnit", ""),
        "prices": prices,
        "lowestPrice": lowest,
        "highestPrice": highest,
        "savings": savings,
        "storeCount": len(prices),
    }


# ─── HTTP Server ───
class FarqHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # Serve static files
        if path == "/" or path == "/index.html":
            return self.serve_file("farq.html", "text/html")

        # API routes
        if path.startswith("/api/") or path == "/health":
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            return self.route_api(path, params)

        # 404
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not found")

    def route_api(self, path, params):
        if path == "/api/search":
            q = params.get("q", [""])[0]
            cat = params.get("category", [None])[0]
            limit = int(params.get("limit", ["100"])[0])
            results = search(q, cat, limit)
            formatted = [format_product(p) for p in results]
            self.write_json({"products": formatted, "total": len(formatted), "query": q})

        elif path == "/api/categories":
            self.write_json(categories)

        elif path == "/api/stores":
            self.write_json(list(STORE_MAP.values()))

        elif path == "/api/stats":
            self.write_json({
                "totalProducts": len(fustog_products),
                "totalCategories": len(categories),
                "stores": STORE_MAP,
            })

        elif path == "/api/product":
            fid = params.get("fid", [None])[0]
            if fid:
                fid = int(fid)
                for p in fustog_products:
                    if p.get("FID") == fid:
                        self.write_json(format_product(p))
                        return
            self.write_json({"error": "not found"})

        elif path == "/api/trending":
            # Products available in most stores with biggest price gaps
            multi = []
            for p in fustog_products:
                valid = [v for v in p.get("Prices", {}).values() if v and v > 0]
                if len(valid) >= 4:
                    multi.append((max(valid) - min(valid), p))
            multi.sort(key=lambda x: -x[0])
            formatted = [format_product(p) for p in (m[1] for m in multi[:30])]
            self.write_json({"products": formatted, "total": len(formatted)})

        elif path == "/health":
            self.write_json({"ok": True, "products": len(fustog_products)})

        else:
            self.write_json({"error": "unknown endpoint"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def serve_file(self, filename, content_type):
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            with open(filepath, "r", encoding="utf-8") as f:
                body = f.read().encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def write_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Silent


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    load_data()

    server = HTTPServer(("0.0.0.0", PORT), FarqHandler)
    print(f"\nFarq Grocery running at http://localhost:{PORT}")
    print(f"Open http://localhost:{PORT} in your browser\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()
