#!/usr/bin/env python3
"""
سكربت نهائي لجلب البيانات - يستخدم نفس المكتبات تماماً
Final script using exact same libraries as original
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple

# نفس المكتبات من السكربت الأصلي
import pandas as pd
from dotenv import load_dotenv
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """نفس الدالة من السكربت الأصلي"""
    df = df.copy()
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    return df


class ApiClient:
    """نفس ApiClient من السكربت الأصلي بالضبط"""
    
    def __init__(self, base_url: str, timeout: float = 20.0, api_key_env: str = "FUSTOG_API_KEY"):
        self.base_url = base_url.rstrip("/")
        load_dotenv()
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
    
    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    def get_json(self, endpoint: str, params: Dict[str, Any] | None = None) -> Any:
        """نفس الدالة من السكربت الأصلي"""
        url = f"{self.base_url}{endpoint}"
        resp = self._client.get(url, params=params)
        resp.raise_for_status()
        ct = (resp.headers.get("content-type") or "").lower()
        try:
            return resp.json()
        except Exception:
            snippet = resp.content[:200]
            print(f"[WARN] Non-JSON response from {url} ct={ct} bytes={len(resp.content)} snippet={snippet!r}")
            raise


def get_env_base_url() -> str:
    """نفس الدالة من السكربت الأصلي"""
    load_dotenv()
    base = os.getenv("VITE_API_BASE_URL") or os.getenv("API_BASE_URL")
    if base:
        return base
    # Use main API if dev doesn't work
    return "https://api.fustog.app/api/v1"


def fetch_all(api: ApiClient) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """نفس الدالة من السكربت الأصلي"""
    categories = api.get_json("/category/Categories")
    cat_df = _normalize_columns(pd.DataFrame(categories))
    
    all_products: List[Dict[str, Any]] = []
    for _, row in cat_df.iterrows():
        category_id = int(row["id"])
        products = api.get_json("/product/ProductsByCategory", params={"categoryId": category_id})
        all_products.extend(products)
    prod_df = _normalize_columns(pd.DataFrame(all_products))
    
    prices = api.get_json("/product/ItemsPrices")
    prices_df = _normalize_columns(pd.DataFrame(prices))
    
    return cat_df, prod_df, prices_df


def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("Fetching data from Fustog API")
    print("=" * 60)
    
    try:
        base_url = get_env_base_url()
        print(f"Base URL: {base_url}\n")
        
        api = ApiClient(base_url=base_url)
        
        print("Fetching all data...")
        categories_df, products_df, prices_df = fetch_all(api)
        
        # تحويل إلى JSON
        all_data = {
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "base_url": base_url
            },
            "categories": categories_df.to_dict('records'),
            "products": products_df.to_dict('records'),
            "prices": prices_df.to_dict('records')
        }
        
        # حفظ البيانات
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        filename = f"data/fustog_data_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
        
        print("\n" + "=" * 60)
        print(f"[OK] Data saved to: {filename}")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  - Categories: {len(categories_df)}")
        print(f"  - Products: {len(products_df)}")
        print(f"  - Prices: {len(prices_df)}")
        print("\nDone!")
        
        return 0
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
