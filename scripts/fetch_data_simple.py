#!/usr/bin/env python3
"""
سكربت بسيط وسريع لجلب البيانات
Simple and quick script to fetch data
"""

import os
import json
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

# الإعدادات
BASE_URL = os.getenv("VITE_API_BASE_URL") or os.getenv("API_BASE_URL") or "https://api.fustog.app/api/v1"
API_KEY = os.getenv("FUSTOG_API_KEY")
OUTPUT_DIR = "data"

def fetch_json(url: str, params: dict = None):
    """جلب JSON من URL"""
    headers = {
        "Accept": "application/json, */*;q=0.5",
        "Accept-Encoding": "identity"
    }
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    response = httpx.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    
    # Handle different response types
    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type:
        return response.json()
    else:
        # Try to parse as JSON anyway
        try:
            return response.json()
        except:
            return response.text

def main():
    print("Fetching data from Fustog API...\n")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    
    all_data = {}
    
    # 1. Fetch categories
    print("1. Fetching categories...")
    try:
        categories = fetch_json(f"{BASE_URL}/category/Categories")
        # Handle different response formats
        if isinstance(categories, str):
            # Try to decode if it's base64 or compressed
            print("   [WARN] Response is string, trying to parse...")
            categories = []
        elif isinstance(categories, list):
            all_data["categories"] = categories
        elif isinstance(categories, dict):
            all_data["categories"] = [categories]
        else:
            all_data["categories"] = []
        print(f"   [OK] {len(all_data['categories'])} categories\n")
    except Exception as e:
        print(f"   [ERROR] {e}\n")
        all_data["categories"] = []
    
    # 2. Fetch products
    print("2. Fetching products...")
    all_products = []
    for cat in all_data["categories"]:
        if isinstance(cat, dict):
            cat_id = cat.get("id") or cat.get("categoryId")
            if cat_id:
                try:
                    products = fetch_json(
                        f"{BASE_URL}/product/ProductsByCategory",
                        params={"categoryId": cat_id}
                    )
                    if isinstance(products, list):
                        all_products.extend(products)
                    elif isinstance(products, dict):
                        all_products.append(products)
                except Exception as e:
                    print(f"   [WARN] Error fetching products for category {cat_id}: {e}")
                    pass
    all_data["products"] = all_products
    print(f"   [OK] {len(all_products)} products\n")
    
    # 3. Fetch prices
    print("3. Fetching prices...")
    try:
        prices = fetch_json(f"{BASE_URL}/product/ItemsPrices")
        if isinstance(prices, list):
            all_data["prices"] = prices
        elif isinstance(prices, dict):
            all_data["prices"] = [prices]
        else:
            all_data["prices"] = []
        print(f"   [OK] {len(all_data['prices'])} prices\n")
    except Exception as e:
        print(f"   [ERROR] {e}\n")
        all_data["prices"] = []
    
    # Save data
    filename = f"{OUTPUT_DIR}/fustog_data_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Data saved to: {filename}")
    print(f"\nSummary:")
    print(f"  - Categories: {len(all_data['categories'])}")
    print(f"  - Products: {len(all_data['products'])}")
    print(f"  - Prices: {len(all_data['prices'])}")

if __name__ == "__main__":
    main()
