#!/usr/bin/env python3
"""
سكربت لجلب البيانات - يستخدم نفس طريقة السكربت الأصلي
Working script using the same method as the original
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List
import httpx
from dotenv import load_dotenv

load_dotenv()


class ApiClient:
    """نفس ApiClient من السكربت الأصلي"""
    
    def __init__(self, base_url: str, timeout: float = 20.0, api_key_env: str = "FUSTOG_API_KEY"):
        self.base_url = base_url.rstrip("/")
        api_key = os.getenv(api_key_env)
        headers: Dict[str, str] = {
            "Accept": "application/json, */*;q=0.5",
            "Accept-Encoding": "identity",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(
            timeout=timeout,
            headers=headers,
        )
    
    def get_json(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """جلب JSON - نفس الطريقة"""
        url = f"{self.base_url}{endpoint}"
        resp = self._client.get(url, params=params)
        resp.raise_for_status()
        ct = (resp.headers.get("content-type") or "").lower()
        
        # تحقق من content-type أولاً
        if "json" not in ct:
            # إذا لم يكن JSON، حاول فك التشفير
            snippet = resp.content[:200]
            print(f"[WARN] Non-JSON response from {url} ct={ct} bytes={len(resp.content)}")
            print(f"[WARN] First 200 bytes: {snippet!r}")
            
            # محاولة فك التشفير
            return self._decode_response(resp.content, ct)
        
        # محاولة JSON عادي
        try:
            return resp.json()
        except Exception:
            # إذا فشل، جرب فك التشفير
            return self._decode_response(resp.content, ct)
    
    def _decode_response(self, content: bytes, content_type: str) -> Any:
        """فك تشفير/ضغط الاستجابة"""
            
        """فك تشفير/ضغط الاستجابة"""
        import base64
        import gzip
        import zlib
        
        # جرب base64 decode أولاً
        try:
            # إذا كان النص يبدو base64
            text_content = content.decode('utf-8', errors='ignore').strip()
            
            # تحقق إذا كان base64
            if text_content and len(text_content) > 50:
                try:
                    # أضف padding إذا لزم
                    missing_padding = len(text_content) % 4
                    if missing_padding:
                        text_content += '=' * (4 - missing_padding)
                    
                    decoded_bytes = base64.b64decode(text_content, validate=True)
                    
                    # جرب gzip decompress
                    try:
                        decompressed = gzip.decompress(decoded_bytes)
                        json_data = json.loads(decompressed.decode('utf-8'))
                        print(f"[OK] Successfully decoded base64+gzip response")
                        return json_data
                    except Exception as e1:
                        # جرب zlib/deflate
                        try:
                            decompressed = zlib.decompress(decoded_bytes)
                            json_data = json.loads(decompressed.decode('utf-8'))
                            print(f"[OK] Successfully decoded base64+zlib response")
                            return json_data
                        except Exception as e2:
                            # جرب بدون decompress
                            try:
                                json_data = json.loads(decoded_bytes.decode('utf-8'))
                                print(f"[OK] Successfully decoded base64 response")
                                return json_data
                            except Exception as e3:
                                print(f"[DEBUG] All decode attempts failed: base64+gzip={e1}, base64+zlib={e2}, base64={e3}")
                                pass
                except Exception as e:
                    print(f"[DEBUG] Base64 decode failed: {e}")
                    pass
            
            # جرب decompress مباشرة بدون base64
            try:
                decompressed = gzip.decompress(content)
                json_data = json.loads(decompressed.decode('utf-8'))
                print(f"[OK] Successfully decoded gzip response")
                return json_data
            except:
                try:
                    decompressed = zlib.decompress(content)
                    json_data = json.loads(decompressed.decode('utf-8'))
                    print(f"[OK] Successfully decoded zlib response")
                    return json_data
                except:
                    pass
        except Exception as e:
            print(f"[ERROR] Failed to decode: {e}")
        
        # إذا فشل كل شيء، ارجع النص الأصلي
        raise ValueError(f"Could not decode response. Content type: {content_type}, Size: {len(content)}")


def get_env_base_url() -> str:
    """نفس الدالة من السكربت الأصلي"""
    load_dotenv()
    base = os.getenv("VITE_API_BASE_URL") or os.getenv("API_BASE_URL")
    if base:
        return base
    # Use the main API URL
    return "https://api.fustog.app/api/v1"


def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("Fetching data from Fustog API")
    print("=" * 60)
    
    base_url = get_env_base_url()
    print(f"Base URL: {base_url}\n")
    
    api = ApiClient(base_url=base_url)
    all_data = {
        "metadata": {
            "fetched_at": datetime.now().isoformat(),
            "base_url": base_url
        },
        "categories": [],
        "products": [],
        "prices": []
    }
    
    # 1. جلب التصنيفات
    print("1. Fetching categories...")
    try:
        categories = api.get_json("/category/Categories")
        if isinstance(categories, list):
            all_data["categories"] = categories
        elif isinstance(categories, dict):
            all_data["categories"] = [categories]
        print(f"   [OK] {len(all_data['categories'])} categories\n")
    except Exception as e:
        print(f"   [ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        return 1
    
    # 2. جلب المنتجات (من أول 5 تصنيفات للاختبار)
    print("2. Fetching products...")
    all_products = []
    categories_to_fetch = all_data["categories"][:5]  # أول 5 فقط للاختبار
    
    for i, cat in enumerate(categories_to_fetch):
        if isinstance(cat, dict):
            cat_id = cat.get("id") or cat.get("categoryId")
            if cat_id:
                try:
                    print(f"   Fetching category {cat_id} ({i+1}/{len(categories_to_fetch)})...")
                    products = api.get_json("/product/ProductsByCategory", params={"categoryId": cat_id})
                    if isinstance(products, list):
                        all_products.extend(products)
                    elif isinstance(products, dict):
                        all_products.append(products)
                    print(f"      [OK] {len(products) if isinstance(products, list) else 1} products")
                except Exception as e:
                    print(f"      [WARN] Error: {e}")
    
    all_data["products"] = all_products
    print(f"\n   [OK] Total: {len(all_products)} products\n")
    
    # 3. جلب الأسعار
    print("3. Fetching prices...")
    try:
        prices = api.get_json("/product/ItemsPrices")
        if isinstance(prices, list):
            all_data["prices"] = prices
        elif isinstance(prices, dict):
            all_data["prices"] = [prices]
        print(f"   [OK] {len(all_data['prices'])} prices\n")
    except Exception as e:
        print(f"   [ERROR] {e}\n")
        import traceback
        traceback.print_exc()
    
    # حفظ البيانات
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    filename = f"data/fustog_data_{timestamp}.json"
    
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
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
