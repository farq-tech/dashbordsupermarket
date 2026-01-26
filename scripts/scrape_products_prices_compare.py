import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple

import pandas as pd
from dotenv import load_dotenv
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tqdm import tqdm


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
	"""
	Normalize column names to snake_case and trimmed.
	دالة مساعدة لتوحيد أسماء الأعمدة
	"""
	df = df.copy()
	df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
	return df


class ApiClient:
	"""
	Simple API client with retries.
	عميل API بسيط مع إعادة المحاولة وتعيين المهلات
	Args:
		base_url: Base URL for API (from .env or default)
		timeout: request timeout seconds
		api_key_env: optional env var name for bearer token (default: FUSTOG_API_KEY)
	Returns:
		None
	"""

	def __init__(self, base_url: str, timeout: float = 20.0, api_key_env: str = "FUSTOG_API_KEY") -> None:
		self.base_url = base_url.rstrip("/")
		# حاول تحميل مفتاح API من البيئة لإرساله كترويسة Authorization (Bearer)
		load_dotenv()
		api_key = os.getenv(api_key_env)
		headers: Dict[str, str] = {
			"Accept": "application/json, */*;q=0.5",
			"Accept-Encoding": "identity",
		}
		if api_key:
			# ملاحظة: لو كانت الـ API تتطلب ترويسة مختلفة (مثل x-api-key) حدّث السطر التالي
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
		"""
		GET JSON with retries.
		يجلب JSON مع تكرار آلي عند الفشل المؤقت
		"""
		url = f"{self.base_url}{endpoint}"
		resp = self._client.get(url, params=params)
		resp.raise_for_status()
		ct = (resp.headers.get("content-type") or "").lower()
		try:
			return resp.json()
		except Exception:
			# طباعة معلومات تساعد على التشخيص ثم إعادة الخطأ
			snippet = resp.content[:200]
			print(f"[WARN] Non-JSON response from {url} ct={ct} bytes={len(resp.content)} snippet={snippet!r}")
			raise


def get_env_base_url() -> str:
	"""
	Load base URL from environment (.env) or fallback to dev.
	تحميل عنوان الأساس من .env أو استخدام التطوير افتراضيًا
	"""
	load_dotenv()
	base = os.getenv("VITE_API_BASE_URL") or os.getenv("API_BASE_URL")
	if base:
		return base
	# fallback dev
	return "https://devapi.fustog.app"


def fetch_all(api: ApiClient) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
	"""
	Fetch categories, products (by category), and item prices.
	جلب التصنيفات والمنتجات (لكل تصنيف) وأسعار العناصر
	Returns:
		(categories_df, products_df, prices_df)
	"""
	categories = api.get_json("/category/Categories")
	cat_df = _normalize_columns(pd.DataFrame(categories))

	all_products: List[Dict[str, Any]] = []
	for _, row in tqdm(cat_df.iterrows(), total=len(cat_df), desc="Fetching products by category"):
		category_id = int(row["id"])
		products = api.get_json("/product/ProductsByCategory", params={"categoryId": category_id})
		all_products.extend(products)
	prod_df = _normalize_columns(pd.DataFrame(all_products))

	prices = api.get_json("/product/ItemsPrices")
	prices_df = _normalize_columns(pd.DataFrame(prices))

	return cat_df, prod_df, prices_df


def compare_prices(products_df: pd.DataFrame, prices_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
	"""
	Join products with prices and compute per-product comparison metrics.
	دمج المنتجات مع الأسعار وحساب مؤشرات المقارنة لكل منتج
	Args:
		products_df: products dataframe
		prices_df: item prices dataframe
Returns:
		(merged_df, summary_df) where:
			- merged_df: all rows with product and each price row
			- summary_df: per product metrics (min, max, spread, stores_count)
	"""
	prod_cols = products_df.columns.tolist()
	price_cols = prices_df.columns.tolist()
	required_prod = {"id", "name", "categoryid"}
	required_price = {"productid", "price", "storeid"}
	if not required_prod.issubset(set(prod_cols)) or not required_price.issubset(set(price_cols)):
		raise ValueError("Input dataframes missing required columns for merge/comparison")

	merged = prices_df.merge(products_df, left_on="productid", right_on="id", how="left", suffixes=("_price", "_product"))
	merged = merged.rename(columns={"id": "product_id"})

	# Compute summary per product
	group = merged.groupby("product_id", as_index=False).agg(
		lowest_price=("price", "min"),
		highest_price=("price", "max"),
		stores_count=("storeid", "nunique"),
	)
	group["price_spread"] = group["highest_price"] - group["lowest_price"]

	# Attach product names for readability
	name_map = products_df.set_index("id")["name"].to_dict()
	group["product_name"] = group["product_id"].map(name_map)

	# Reorder columns
	group = group[["product_id", "product_name", "lowest_price", "highest_price", "price_spread", "stores_count"]]
	return merged, group


def export_outputs(
	categories_df: pd.DataFrame,
	products_df: pd.DataFrame,
	prices_df: pd.DataFrame,
	merged_df: pd.DataFrame,
	summary_df: pd.DataFrame,
) -> Dict[str, str]:
	"""
	Export CSV and XLSX files with timestamped names under /data.
	تصدير ملفات CSV و XLSX بأسماء موقّتة داخل مجلد data/
	Returns:
		Dictionary of generated file paths
	"""
	os.makedirs("data", exist_ok=True)
	now = datetime.now().strftime("%Y_%m_%d_%H%M%S")

	files: Dict[str, str] = {}
	def _save_csv(name: str, df: pd.DataFrame) -> None:
		path = os.path.join("data", f"{name}_{now}.csv")
		df.to_csv(path, index=False, encoding="utf-8")
		files[f"{name}_csv"] = path

	def _save_xlsx(name: str, df: pd.DataFrame) -> None:
		path = os.path.join("data", f"{name}_{now}.xlsx")
		df.to_excel(path, index=False, engine="openpyxl")
		files[f"{name}_xlsx"] = path

	for label, df in [
		("categories", categories_df),
		("products", products_df),
		("prices", prices_df),
		("merged", merged_df),
		("summary", summary_df),
	]:
		_save_csv(label, df)
		_save_xlsx(label, df)

	# index file to quickly browse outputs
	index_path = os.path.join("data", f"index_{now}.csv")
	index_df = pd.DataFrame([{"name": k, "path": v} for k, v in files.items()])
	index_df.to_csv(index_path, index=False, encoding="utf-8")
	files["index_csv"] = index_path
	return files


def print_quick_stats(products_df: pd.DataFrame, prices_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
	"""
	Print quick summary stats.
	عرض إحصائيات مختصرة لسلامة البيانات
	"""
	def null_pct(df: pd.DataFrame) -> float:
		return float((df.isna().sum().sum() / (df.shape[0] * max(df.shape[1], 1))) * 100.0) if df.size else 0.0

	print("\n=== Quick Stats ===")
	print(f"products: count={len(products_df)}  null%={null_pct(products_df):.2f}%")
	print(f"prices:   count={len(prices_df)}  null%={null_pct(prices_df):.2f}%")
	print(f"summary:  unique_products={summary_df['product_id'].nunique()} "
	      f"min_price={summary_df['lowest_price'].min() if not summary_df.empty else 'NA'} "
	      f"max_price={summary_df['highest_price'].max() if not summary_df.empty else 'NA'}")


def main() -> int:
	"""
	Run end-to-end scraping and comparison workflow.
	تشغيل عملية الجلب الشامل للمنتجات والأسعار مع المقارنة والتصدير
	Usage example:
		python scripts/scrape_products_prices_compare.py
	Sample Input/Output:
		- Input: API base via .env (VITE_API_BASE_URL)
		- Output: data/{products,prices,merged,summary}_YYYY_MM_DD_HHMMSS.{csv,xlsx}
	"""
	try:
		base_url = get_env_base_url()
		api = ApiClient(base_url=base_url)

		categories_df, products_df, prices_df = fetch_all(api)
		merged_df, summary_df = compare_prices(products_df, prices_df)
		paths = export_outputs(categories_df, products_df, prices_df, merged_df, summary_df)
		print_quick_stats(products_df, prices_df, summary_df)

		print("\nOutputs:")
		for k, v in paths.items():
			print(f"- {k}: {v}")

		return 0
	except Exception as e:
		# سجل الخطأ بشكل منظم
		print(f"Error in main: {e}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())



