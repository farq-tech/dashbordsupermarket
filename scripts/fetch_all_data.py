#!/usr/bin/env python3
"""
سكربت شامل لجلب جميع البيانات من Fustog API
Script to fetch all data from Fustog API
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


class FustogDataFetcher:
    """جلب جميع البيانات من Fustog API"""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.getenv("VITE_API_BASE_URL") or os.getenv("API_BASE_URL") or "https://api.fustog.app/api/v1"
        self.base_url = self.base_url.rstrip("/")
        self.api_key = api_key or os.getenv("FUSTOG_API_KEY")
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "Fustog-Data-Fetcher/1.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.Client(
            headers=headers,
            timeout=30.0,
            follow_redirects=True
        )
    
    def fetch_categories(self) -> List[Dict[str, Any]]:
        """جلب جميع التصنيفات"""
        print("جلب التصنيفات...")
        try:
            response = self.client.get(f"{self.base_url}/category/Categories")
            response.raise_for_status()
            data = response.json()
            print(f"  [OK] تم جلب {len(data)} تصنيف")
            return data if isinstance(data, list) else [data]
        except Exception as e:
            print(f"  [ERROR] خطأ في جلب التصنيفات: {e}")
            return []
    
    def fetch_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """جلب المنتجات حسب التصنيف"""
        try:
            response = self.client.get(
                f"{self.base_url}/product/ProductsByCategory",
                params={"categoryId": category_id}
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else [data]
        except Exception as e:
            print(f"  [WARN] خطأ في جلب منتجات التصنيف {category_id}: {e}")
            return []
    
    def fetch_all_products(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """جلب جميع المنتجات من جميع التصنيفات"""
        print("جلب المنتجات...")
        all_products = []
        
        for cat in tqdm(categories, desc="  جلب المنتجات"):
            cat_id = cat.get("id") or cat.get("categoryId")
            if not cat_id:
                continue
            
            products = self.fetch_products_by_category(int(cat_id))
            all_products.extend(products)
        
        print(f"  [OK] تم جلب {len(all_products)} منتج")
        return all_products
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """جلب جميع الأسعار"""
        print("جلب الأسعار...")
        try:
            response = self.client.get(f"{self.base_url}/product/ItemsPrices")
            response.raise_for_status()
            data = response.json()
            prices = data if isinstance(data, list) else [data]
            print(f"  [OK] تم جلب {len(prices)} سعر")
            return prices
        except Exception as e:
            print(f"  [ERROR] خطأ في جلب الأسعار: {e}")
            return []
    
    def fetch_cities(self) -> List[Dict[str, Any]]:
        """جلب جميع المدن"""
        print("جلب المدن...")
        try:
            # جرب endpoints مختلفة للمدن
            endpoints = [
                "/city/Cities",
                "/cities",
                "/location/Cities",
                "/location/cities"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.client.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        data = response.json()
                        cities = data if isinstance(data, list) else [data]
                        print(f"  [OK] تم جلب {len(cities)} مدينة من {endpoint}")
                        return cities
                except:
                    continue
            
            print("  [WARN] لم يتم العثور على endpoint للمدن")
            return []
        except Exception as e:
            print(f"  [ERROR] خطأ في جلب المدن: {e}")
            return []
    
    def fetch_stores(self, latitude: Optional[float] = None, longitude: Optional[float] = None) -> List[Dict[str, Any]]:
        """جلب المتاجر (يمكن تمرير الموقع للحصول على أقرب المتاجر)"""
        print("جلب المتاجر...")
        try:
            params = {}
            if latitude and longitude:
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius": 10,  # 10 km
                    "limit": 50
                }
            
            endpoints = [
                "/store/Stores",
                "/store/NearestStores",
                "/stores"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.client.get(
                        f"{self.base_url}{endpoint}",
                        params=params if params else None
                    )
                    if response.status_code == 200:
                        data = response.json()
                        stores = data if isinstance(data, list) else [data]
                        print(f"  [OK] تم جلب {len(stores)} متجر من {endpoint}")
                        return stores
                except:
                    continue
            
            print("  [WARN] لم يتم العثور على endpoint للمتاجر")
            return []
        except Exception as e:
            print(f"  [ERROR] خطأ في جلب المتاجر: {e}")
            return []
    
    def fetch_retailer_settings(self) -> Dict[str, Any]:
        """جلب إعدادات التاجر"""
        print("جلب إعدادات التاجر...")
        try:
            endpoints = [
                "/retailer/Settings",
                "/settings",
                "/retailer/settings"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.client.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"  [OK] تم جلب الإعدادات من {endpoint}")
                        return data if isinstance(data, dict) else {}
                except:
                    continue
            
            print("  [WARN] لم يتم العثور على endpoint للإعدادات")
            return {}
        except Exception as e:
            print(f"  [ERROR] خطأ في جلب الإعدادات: {e}")
            return {}
    
    def fetch_all(self, include_stores: bool = True, include_cities: bool = True) -> Dict[str, Any]:
        """جلب جميع البيانات المتاحة"""
        print("=" * 60)
        print("بدء جلب البيانات من Fustog API")
        print("=" * 60)
        print(f"Base URL: {self.base_url}\n")
        
        all_data = {
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "base_url": self.base_url,
                "api_key_provided": bool(self.api_key)
            },
            "categories": [],
            "products": [],
            "prices": [],
            "cities": [],
            "stores": [],
            "retailer_settings": {}
        }
        
        # جلب التصنيفات
        categories = self.fetch_categories()
        all_data["categories"] = categories
        
        # جلب المنتجات
        if categories:
            products = self.fetch_all_products(categories)
            all_data["products"] = products
        
        # جلب الأسعار
        prices = self.fetch_prices()
        all_data["prices"] = prices
        
        # جلب المدن (اختياري)
        if include_cities:
            cities = self.fetch_cities()
            all_data["cities"] = cities
        
        # جلب المتاجر (اختياري)
        if include_stores:
            stores = self.fetch_stores()
            all_data["stores"] = stores
        
        # جلب الإعدادات
        settings = self.fetch_retailer_settings()
        all_data["retailer_settings"] = settings
        
        # إحصائيات
        print("\n" + "=" * 60)
        print("ملخص البيانات المجلوبة:")
        print("=" * 60)
        print(f"التصنيفات: {len(all_data['categories'])}")
        print(f"المنتجات: {len(all_data['products'])}")
        print(f"الأسعار: {len(all_data['prices'])}")
        print(f"المدن: {len(all_data['cities'])}")
        print(f"المتاجر: {len(all_data['stores'])}")
        print(f"الإعدادات: {'نعم' if all_data['retailer_settings'] else 'لا'}")
        print("=" * 60)
        
        return all_data
    
    def save_to_json(self, data: Dict[str, Any], output_dir: str = "data") -> str:
        """حفظ البيانات في ملف JSON"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        filename = f"fustog_data_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] تم حفظ البيانات في: {filepath}")
        return filepath
    
    def save_individual_files(self, data: Dict[str, Any], output_dir: str = "data") -> Dict[str, str]:
        """حفظ كل نوع بيانات في ملف منفصل"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        files = {}
        
        for key in ["categories", "products", "prices", "cities", "stores"]:
            if data.get(key):
                filename = f"{key}_{timestamp}.json"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data[key], f, ensure_ascii=False, indent=2)
                files[key] = filepath
                print(f"  [OK] {key}: {filepath}")
        
        if data.get("retailer_settings"):
            filename = f"retailer_settings_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data["retailer_settings"], f, ensure_ascii=False, indent=2)
            files["retailer_settings"] = filepath
            print(f"  [OK] retailer_settings: {filepath}")
        
        return files


def main():
    """الدالة الرئيسية"""
    import argparse
    
    parser = argparse.ArgumentParser(description="جلب جميع البيانات من Fustog API")
    parser.add_argument("--base-url", help="Base URL للـ API")
    parser.add_argument("--api-key", help="API Key (أو استخدم .env)")
    parser.add_argument("--output-dir", default="data", help="مجلد الحفظ")
    parser.add_argument("--no-stores", action="store_true", help="عدم جلب المتاجر")
    parser.add_argument("--no-cities", action="store_true", help="عدم جلب المدن")
    parser.add_argument("--individual", action="store_true", help="حفظ كل نوع في ملف منفصل")
    
    args = parser.parse_args()
    
    # إنشاء Fetcher
    fetcher = FustogDataFetcher(
        base_url=args.base_url,
        api_key=args.api_key
    )
    
    # جلب البيانات
    all_data = fetcher.fetch_all(
        include_stores=not args.no_stores,
        include_cities=not args.no_cities
    )
    
    # حفظ البيانات
    if args.individual:
        fetcher.save_individual_files(all_data, args.output_dir)
    else:
        fetcher.save_to_json(all_data, args.output_dir)
    
    print("\n[OK] اكتمل جلب البيانات بنجاح!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
