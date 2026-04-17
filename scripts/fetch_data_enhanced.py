#!/usr/bin/env python3
"""
سكربت محسّن لجلب المنتجات والأسعار من Fustog API
يحاول طرق متعددة للتغلب على مشكلة الـ response الفارغ
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعدادات الـ API (من .env أو افتراضي)
BASE_URL = os.getenv("VITE_API_BASE_URL") or os.getenv("API_BASE_URL") or "https://api.fustog.app/api/v1"
CATEGORIES_ENDPOINT = "/category/Categories"
PRODUCTS_ENDPOINT = "/product/ProductsByCategory"
PRICES_ENDPOINT = "/product/ItemsPrices"

# Headers محسّنة (محاكاة المتصفح الحقيقي)
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://trends.fustog.app',
    'Referer': 'https://trends.fustog.app/',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

# Headers Android (محاكاة التطبيق الأصلي)
ANDROID_HEADERS = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 16)',
    'Accept': 'application/json, */*;q=0.5',
    'Accept-Encoding': 'identity',
    'Origin': 'https://trends.fustog.app',
    'Referer': 'https://trends.fustog.app/',
}

# إضافة coordinates (موقع الرياض)
LOCATION_DATA = {
    'latitude': 24.7136,
    'longitude': 46.6753,
    'cityId': '1',
    'city': 'Riyadh'
}

class FustogAPIClient:
    """عميل API محسّن مع طرق متعددة للوصول"""
    
    def __init__(self, use_android_headers: bool = False):
        self.session = requests.Session()
        if use_android_headers:
            self.session.headers.update(ANDROID_HEADERS)
        else:
            self.session.headers.update(BROWSER_HEADERS)
        self.base_url = BASE_URL
        
    def _try_get_request(self, url: str, params: Dict = None) -> Optional[Any]:
        """محاولة GET request"""
        try:
            print(f"[GET] محاولة GET: {url}")
            response = self.session.get(url, params=params, timeout=10)
            print(f"   Status: {response.status_code}, Content-Length: {len(response.content)}")
            
            if response.status_code == 200 and len(response.content) > 0:
                try:
                    return response.json()
                except:
                    # ربما LZ-String compressed
                    return response.text
            return None
        except Exception as e:
            print(f"   [ERROR] GET فشل: {e}")
            return None
    
    def _try_post_with_query_params(self, url: str, params: Dict = None) -> Optional[Any]:
        """محاولة POST مع query parameters"""
        try:
            print(f"🔄 محاولة POST (query params): {url}")
            response = self.session.post(url, params=params, timeout=10)
            print(f"   Status: {response.status_code}, Content-Length: {len(response.content)}")
            
            if response.status_code == 200 and len(response.content) > 0:
                try:
                    return response.json()
                except:
                    return response.text
            return None
        except Exception as e:
            print(f"   ❌ POST (query) فشل: {e}")
            return None
    
    def _try_post_with_json_body(self, url: str, data: Dict = None) -> Optional[Any]:
        """محاولة POST مع JSON body"""
        try:
            print(f"🔄 محاولة POST (JSON body): {url}")
            response = self.session.post(url, json=data, timeout=10)
            print(f"   Status: {response.status_code}, Content-Length: {len(response.content)}")
            
            if response.status_code == 200 and len(response.content) > 0:
                try:
                    return response.json()
                except:
                    return response.text
            return None
        except Exception as e:
            print(f"   ❌ POST (JSON) فشل: {e}")
            return None
    
    def _try_post_with_form_data(self, url: str, data: Dict = None) -> Optional[Any]:
        """محاولة POST مع form data"""
        try:
            print(f"🔄 محاولة POST (form data): {url}")
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            response = self.session.post(url, data=data, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}, Content-Length: {len(response.content)}")
            
            if response.status_code == 200 and len(response.content) > 0:
                try:
                    return response.json()
                except:
                    return response.text
            return None
        except Exception as e:
            print(f"   ❌ POST (form) فشل: {e}")
            return None
    
    def _try_post_with_location(self, url: str, params: Dict = None) -> Optional[Any]:
        """محاولة POST مع location data"""
        try:
            print(f"🔄 محاولة POST (مع Location): {url}")
            combined_params = {**(params or {}), **LOCATION_DATA}
            response = self.session.post(url, params=combined_params, timeout=10)
            print(f"   Status: {response.status_code}, Content-Length: {len(response.content)}")
            
            if response.status_code == 200 and len(response.content) > 0:
                try:
                    return response.json()
                except:
                    return response.text
            return None
        except Exception as e:
            print(f"   ❌ POST (location) فشل: {e}")
            return None
    
    def fetch_with_all_methods(self, url: str, params: Dict = None, data: Dict = None) -> Optional[Any]:
        """جرب جميع الطرق المتاحة"""
        print(f"\n{'='*60}")
        print(f"[FETCH] محاولة جلب البيانات من: {url}")
        print(f"{'='*60}")
        
        # الطريقة 1: GET
        result = self._try_get_request(url, params)
        if result:
            print("[SUCCESS] نجح GET!")
            return result
        
        # الطريقة 2: POST مع query params
        result = self._try_post_with_query_params(url, params)
        if result:
            print("[SUCCESS] نجح POST (query params)!")
            return result
        
        # الطريقة 3: POST مع JSON body
        if data:
            result = self._try_post_with_json_body(url, data)
            if result:
                print("[SUCCESS] نجح POST (JSON body)!")
                return result
        
        # الطريقة 4: POST مع form data
        if data:
            result = self._try_post_with_form_data(url, data)
            if result:
                print("[SUCCESS] نجح POST (form data)!")
                return result
        
        # الطريقة 5: POST مع location
        result = self._try_post_with_location(url, params)
        if result:
            print("[SUCCESS] نجح POST (مع location)!")
            return result
        
        print("[FAILED] فشلت جميع الطرق!")
        return None
    
    def get_categories(self) -> List[Dict]:
        """جلب التصنيفات"""
        url = f"{self.base_url}{CATEGORIES_ENDPOINT}"
        result = self.fetch_with_all_methods(url)
        
        # معالجة LZ-String إذا لزم
        if result and isinstance(result, str):
            try:
                import sys
                import os
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from scripts.scrape_products_prices_compare import lz_decompress_from_base64
                decompressed = lz_decompress_from_base64(result)
                result = json.loads(decompressed)
            except Exception as e:
                print(f"[WARN] فشل فك ضغط LZ-String: {e}")
                # جرب parse كـ JSON مباشرة
                try:
                    result = json.loads(result)
                except:
                    pass
        
        # تأكد أن النتيجة list
        if result and not isinstance(result, list):
            if isinstance(result, dict):
                result = [result]
            else:
                result = []
        
        return result if result else []
    
    def get_products_by_category(self, category_id: str) -> List[Dict]:
        """جلب المنتجات حسب التصنيف"""
        url = f"{self.base_url}{PRODUCTS_ENDPOINT}"
        params = {'categoryId': category_id}
        data = {'categoryId': category_id, **LOCATION_DATA}
        
        result = self.fetch_with_all_methods(url, params=params, data=data)
        return result if result else []
    
    def get_prices(self, product_ids: List[str] = None, store_ids: List[str] = None) -> List[Dict]:
        """جلب الأسعار"""
        url = f"{self.base_url}{PRICES_ENDPOINT}"
        params = {}
        data = {}
        
        if product_ids:
            params['productIds'] = ','.join(product_ids)
            data['productIds'] = product_ids
        
        if store_ids:
            params['storeIds'] = ','.join(store_ids)
            data['storeIds'] = store_ids
        
        # إضافة location
        data.update(LOCATION_DATA)
        
        result = self.fetch_with_all_methods(url, params=params, data=data)
        return result if result else []


def save_to_file(data: Any, filename: str):
    """حفظ البيانات إلى ملف JSON"""
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join("data", f"{filename}_{timestamp}.json")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[SAVED] تم حفظ البيانات في: {filepath}")
    return filepath


def main():
    """الدالة الرئيسية"""
    import sys
    import io
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("[START] بدء جلب البيانات من Fustog API")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print("="*60)
    
    # جرب مع Android headers أولاً
    print("\n[ANDROID] جرب مع Android Headers...")
    client = FustogAPIClient(use_android_headers=True)
    
    # 1. جلب التصنيفات
    print("\n[CATEGORIES] جلب التصنيفات...")
    categories = client.get_categories()
    
    # التأكد من أن categories هي list
    if not isinstance(categories, list):
        print(f"[ERROR] التصنيفات ليست list! النوع: {type(categories)}")
        categories = []
    
    print(f"[OK] تم جلب {len(categories)} تصنيف")
    
    if categories:
        save_to_file(categories, "categories_enhanced")
    
    # 2. جلب المنتجات لكل تصنيف
    all_products = []
    if categories and isinstance(categories, list) and len(categories) > 0:
        print(f"\n[PRODUCTS] جلب المنتجات من {len(categories)} تصنيف...")
        
        for i, category in enumerate(categories[:5], 1):  # جرب أول 5 تصنيفات
            # معالجة category - قد يكون dict أو string
            if isinstance(category, str):
                print(f"[WARN] التصنيف {i} هو string، تم تخطيه")
                continue
            
            if not isinstance(category, dict):
                print(f"[WARN] نوع غير متوقع للتصنيف: {type(category)}")
                continue
            
            category_id = str(category.get('id') or category.get('CID') or category.get('categoryId') or '')
            category_name = category.get('name') or category.get('nameAr') or category.get('TitleAR') or 'Unknown'
            
            if not category_id:
                print(f"[WARN] التصنيف {i} لا يحتوي على ID")
                continue
            
            print(f"\n[{i}/{min(5, len(categories))}] التصنيف: {category_name} (ID: {category_id})")
            
            products = client.get_products_by_category(category_id)
            
            if products:
                if isinstance(products, list):
                    print(f"   [OK] تم جلب {len(products)} منتج")
                    all_products.extend(products)
                else:
                    print(f"   [WARN] Response غير متوقع: {type(products)}")
            else:
                print(f"   [WARN] لا توجد منتجات")
            
            time.sleep(0.5)  # انتظر نصف ثانية بين الطلبات
        
        print(f"\n[OK] إجمالي المنتجات: {len(all_products)}")
        
        if all_products:
            save_to_file(all_products, "products_enhanced")
    
    # 3. جلب الأسعار
    print(f"\n[PRICES] جلب أسعار المنتجات...")
    
    prices = client.get_prices()
    
    if prices:
        if isinstance(prices, list):
            print(f"[OK] تم جلب {len(prices)} سعر")
            save_to_file(prices, "prices_enhanced")
        else:
            print(f"[WARN] Response غير متوقع: {type(prices)}")
    else:
        print("[WARN] لا توجد أسعار")
    
    # 4. عرض الملخص
    print("\n" + "="*60)
    print("[SUMMARY] ملخص النتائج:")
    print("="*60)
    print(f"[OK] التصنيفات: {len(categories)}")
    print(f"{'[OK]' if all_products else '[WARN]'} المنتجات: {len(all_products)}")
    print(f"{'[OK]' if prices and isinstance(prices, list) else '[WARN]'} الأسعار: {len(prices) if prices and isinstance(prices, list) else 0}")
    print("="*60)
    
    # 5. نصائح للمستخدم
    if not all_products:
        print("\n[TIPS] نصائح لحل المشكلة:")
        print("1. استخدم mitmproxy لالتقاط الطلبات الحقيقية:")
        print("   cd fustoog\\sandbox\\ingest")
        print("   .\\run_mitmproxy.ps1")
        print("2. تحقق من متطلبات Authentication للـ API")
        print("3. تحقق من أن الـ API يحتاج Location/Coordinates")
        print("4. راجع ملفات HAR من المتصفح (DevTools > Network > Export HAR)")
        print("5. استخدم البيانات الوهمية (Mock Data) مؤقتاً")
    
    # 6. جرب مع Browser headers إذا فشل
    if not all_products:
        print("\n[BROWSER] جرب مع Browser Headers...")
        browser_client = FustogAPIClient(use_android_headers=False)
        
        if categories and isinstance(categories, list):
            for category in categories[:2]:  # جرب أول تصنيفين فقط
                if not isinstance(category, dict):
                    continue
                category_id = str(category.get('id') or category.get('CID') or category.get('categoryId') or '')
                if category_id:
                    products = browser_client.get_products_by_category(category_id)
                    if products and isinstance(products, list) and len(products) > 0:
                        print(f"[OK] Browser headers نجحت! تم جلب {len(products)} منتج")
                        break


if __name__ == "__main__":
    main()
