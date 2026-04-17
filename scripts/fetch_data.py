#!/usr/bin/env python3
"""
سكربت بسيط لجلب البيانات من Fustog API
Simple script to fetch data from Fustog API
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional

# الإعدادات
BASE_URL = os.getenv("VITE_API_BASE_URL") or os.getenv("API_BASE_URL") or "https://api.fustog.app/api/v1"
API_KEY = os.getenv("FUSTOG_API_KEY")
OUTPUT_DIR = "data"

def fetch_json(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """جلب JSON من URL"""
    # إضافة المعاملات للـ URL
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    # إنشاء Request
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json, */*;q=0.5")
    req.add_header("Accept-Encoding", "identity")
    
    if API_KEY:
        req.add_header("Authorization", f"Bearer {API_KEY}")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8')
            return json.loads(content)
    except Exception as e:
        print(f"   [ERROR] {e}")
        raise

def main():
    print("Fetching data from Fustog API...\n")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    
    all_data = {
        "metadata": {
            "fetched_at": datetime.now().isoformat(),
            "base_url": BASE_URL
        },
        "categories": [],
        "products": [],
        "prices": []
    }
    
    # 1. جلب التصنيفات
    print("1. Fetching categories...")
    try:
        categories = fetch_json(f"{BASE_URL}/category/Categories")
        if isinstance(categories, list):
            all_data["categories"] = categories
        elif isinstance(categories, dict):
            all_data["categories"] = [categories]
        print(f"   [OK] {len(all_data['categories'])} categories\n")
    except Exception as e:
        print(f"   [ERROR] Failed to fetch categories: {e}\n")
    
    # 2. جلب المنتجات
    print("2. Fetching products...")
    all_products = []
    categories_to_fetch = all_data["categories"][:10]  # Limit to first 10 for testing
    
    for i, cat in enumerate(categories_to_fetch):
        if isinstance(cat, dict):
            cat_id = cat.get("id") or cat.get("categoryId")
            if cat_id:
                try:
                    print(f"   Fetching products for category {cat_id} ({i+1}/{len(categories_to_fetch)})...")
                    products = fetch_json(
                        f"{BASE_URL}/product/ProductsByCategory",
                        params={"categoryId": cat_id}
                    )
                    if isinstance(products, list):
                        all_products.extend(products)
                    elif isinstance(products, dict):
                        all_products.append(products)
                except Exception as e:
                    print(f"   [WARN] Error for category {cat_id}: {e}")
    
    all_data["products"] = all_products
    print(f"   [OK] {len(all_products)} products\n")
    
    # 3. جلب الأسعار
    print("3. Fetching prices...")
    try:
        prices = fetch_json(f"{BASE_URL}/product/ItemsPrices")
        if isinstance(prices, list):
            all_data["prices"] = prices
        elif isinstance(prices, dict):
            all_data["prices"] = [prices]
        print(f"   [OK] {len(all_data['prices'])} prices\n")
    except Exception as e:
        print(f"   [ERROR] Failed to fetch prices: {e}\n")
    
    # حفظ البيانات
    filename = f"{OUTPUT_DIR}/fustog_data_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print(f"[OK] Data saved to: {filename}")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Categories: {len(all_data['categories'])}")
    print(f"  - Products: {len(all_data['products'])}")
    print(f"  - Prices: {len(all_data['prices'])}")
    print("\nDone!")

if __name__ == "__main__":
    main()
