import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
import pandas as pd
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from tqdm import tqdm


_LZ_KEYSTR_BASE64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
_LZ_BASE_REVERSE_DICTIONARY: Dict[str, Dict[str, int]] = {}
_DEFAULT_MOBILE_USER_AGENT = "Fustog/1.4.2.1 CFNetwork/3860.300.31 Darwin/25.2.0"
_TARGET_ENDPOINTS = {
    "/product/ProductsByCategory",
    "/product/ItemsPrices",
}


def _lz_get_base_value(alphabet: str, character: str) -> int:
    if alphabet not in _LZ_BASE_REVERSE_DICTIONARY:
        _LZ_BASE_REVERSE_DICTIONARY[alphabet] = {c: i for i, c in enumerate(alphabet)}
    return _LZ_BASE_REVERSE_DICTIONARY[alphabet][character]


def lz_decompress_from_base64(input_str: str) -> str:
    if not input_str:
        return ""
    input_str = "".join(input_str.split())

    def get_next_value(index: int) -> int:
        return _lz_get_base_value(_LZ_KEYSTR_BASE64, input_str[index])

    return _lz_decompress(len(input_str), 32, get_next_value)


def _lz_decompress(length: int, reset_value: int, get_next_value) -> str:
    dictionary: Dict[int, str] = {}
    enlarge_in = 4
    dict_size = 4
    num_bits = 3
    entry = ""
    result: List[str] = []

    data_val = get_next_value(0)
    data_position = reset_value
    data_index = 1

    for i in range(3):
        dictionary[i] = chr(i)

    bits = 0
    maxpower = 2**2
    power = 1
    while power != maxpower:
        resb = data_val & data_position
        data_position >>= 1
        if data_position == 0:
            data_position = reset_value
            data_val = get_next_value(data_index)
            data_index += 1
        bits |= (1 if resb > 0 else 0) * power
        power <<= 1

    next_ = bits
    if next_ == 0:
        bits = 0
        maxpower = 2**8
        power = 1
        while power != maxpower:
            resb = data_val & data_position
            data_position >>= 1
            if data_position == 0:
                data_position = reset_value
                data_val = get_next_value(data_index)
                data_index += 1
            bits |= (1 if resb > 0 else 0) * power
            power <<= 1
        c = chr(bits)
    elif next_ == 1:
        bits = 0
        maxpower = 2**16
        power = 1
        while power != maxpower:
            resb = data_val & data_position
            data_position >>= 1
            if data_position == 0:
                data_position = reset_value
                data_val = get_next_value(data_index)
                data_index += 1
            bits |= (1 if resb > 0 else 0) * power
            power <<= 1
        c = chr(bits)
    elif next_ == 2:
        return ""
    else:
        return ""

    dictionary[3] = c
    w = c
    result.append(c)

    while True:
        if data_index > length:
            return "".join(result)

        bits = 0
        maxpower = 2**num_bits
        power = 1
        while power != maxpower:
            resb = data_val & data_position
            data_position >>= 1
            if data_position == 0:
                data_position = reset_value
                if data_index < length:
                    data_val = get_next_value(data_index)
                    data_index += 1
                else:
                    data_val = 0
            bits |= (1 if resb > 0 else 0) * power
            power <<= 1

        cc = bits
        if cc == 0:
            bits = 0
            maxpower = 2**8
            power = 1
            while power != maxpower:
                resb = data_val & data_position
                data_position >>= 1
                if data_position == 0:
                    data_position = reset_value
                    data_val = get_next_value(data_index)
                    data_index += 1
                bits |= (1 if resb > 0 else 0) * power
                power <<= 1
            dictionary[dict_size] = chr(bits)
            cc = dict_size
            dict_size += 1
            enlarge_in -= 1
        elif cc == 1:
            bits = 0
            maxpower = 2**16
            power = 1
            while power != maxpower:
                resb = data_val & data_position
                data_position >>= 1
                if data_position == 0:
                    data_position = reset_value
                    data_val = get_next_value(data_index)
                    data_index += 1
                bits |= (1 if resb > 0 else 0) * power
                power <<= 1
            dictionary[dict_size] = chr(bits)
            cc = dict_size
            dict_size += 1
            enlarge_in -= 1
        elif cc == 2:
            return "".join(result)

        if enlarge_in == 0:
            enlarge_in = 2**num_bits
            num_bits += 1

        if cc in dictionary:
            entry = dictionary[cc]
        elif cc == dict_size:
            entry = w + w[0]
        else:
            return ""

        result.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        enlarge_in -= 1
        w = entry

        if enlarge_in == 0:
            enlarge_in = 2**num_bits
            num_bits += 1


def lz_compress_to_base64(uncompressed: str) -> str:
    if not uncompressed:
        return ""
    return _lz_compress(uncompressed, 6, lambda value: _LZ_KEYSTR_BASE64[value])


def _lz_compress(uncompressed: str, bits_per_char: int, get_char_from_int) -> str:
    dictionary: Dict[str, int] = {}
    dictionary_to_create: Dict[str, bool] = {}
    w = ""
    enlarge_in = 2
    dict_size = 3
    num_bits = 2
    data_val = 0
    data_position = 0
    output: List[str] = []

    def write_bit(value: int) -> None:
        nonlocal data_val, data_position
        data_val = (data_val << 1) | value
        if data_position == bits_per_char - 1:
            data_position = 0
            output.append(get_char_from_int(data_val))
            data_val = 0
        else:
            data_position += 1

    def write_bits(value: int, count: int) -> None:
        for _ in range(count):
            write_bit(value & 1)
            value >>= 1

    def write_code(value: str) -> None:
        nonlocal enlarge_in, num_bits
        if value in dictionary_to_create:
            char_code = ord(value[0])
            if char_code < 256:
                write_bits(0, num_bits)
                write_bits(char_code, 8)
            else:
                write_bits(1, num_bits)
                write_bits(char_code, 16)
            enlarge_in -= 1
            if enlarge_in == 0:
                enlarge_in = 2**num_bits
                num_bits += 1
            del dictionary_to_create[value]
        else:
            write_bits(dictionary[value], num_bits)

        enlarge_in -= 1
        if enlarge_in == 0:
            enlarge_in = 2**num_bits
            num_bits += 1

    for char in uncompressed:
        if char not in dictionary:
            dictionary[char] = dict_size
            dict_size += 1
            dictionary_to_create[char] = True

        wc = w + char
        if wc in dictionary:
            w = wc
            continue

        write_code(w)
        dictionary[wc] = dict_size
        dict_size += 1
        w = char

    if w:
        write_code(w)

    write_bits(2, num_bits)
    while True:
        data_val <<= 1
        if data_position == bits_per_char - 1:
            output.append(get_char_from_int(data_val))
            break
        data_position += 1

    return "".join(output)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    return df


def _compact_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _sanitize_forward_headers(headers: Dict[str, str]) -> Dict[str, str]:
    blocked = {"host", "content-length", "connection", "accept-encoding"}
    return {k: v for k, v in headers.items() if k.lower() not in blocked}


def _normalize_endpoint_path(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path
    if "/api/v1/" in path:
        path = path[path.index("/api/v1/") + len("/api/v1") :]
    return path


def _try_decode_text_payload(payload: Optional[str]) -> Any:
    if not payload:
        return None
    try:
        return json.loads(payload)
    except Exception:
        pass
    try:
        decoded = lz_decompress_from_base64(payload)
        if decoded:
            return json.loads(decoded)
    except Exception:
        pass
    return None


def load_request_configs_from_har(har_path: str) -> Dict[str, Dict[str, Any]]:
    with open(har_path, "r", encoding="utf-8") as handle:
        har_data = json.load(handle)

    configs: Dict[str, Dict[str, Any]] = {}
    for entry in har_data.get("log", {}).get("entries", []):
        request = entry.get("request", {})
        url = request.get("url", "")
        endpoint = _normalize_endpoint_path(url)
        if endpoint not in _TARGET_ENDPOINTS:
            continue

        headers: Dict[str, str] = {}
        for header in request.get("headers", []):
            name = header.get("name")
            value = header.get("value")
            if name and value is not None:
                headers[name] = value

        raw_body = request.get("postData", {}).get("text")
        configs[endpoint] = {
            "method": request.get("method", "POST").upper(),
            "headers": _sanitize_forward_headers(headers),
            "raw_body": raw_body,
            "decoded_body": _try_decode_text_payload(raw_body),
            "source": f"HAR:{Path(har_path).name}",
        }

    return configs


def _inline_request_config(raw_body: Optional[str], body_json: Optional[str], mobile_user_agent: str) -> Optional[Dict[str, Any]]:
    if not raw_body and not body_json:
        return None

    decoded_body = None
    final_raw_body = raw_body
    if body_json:
        decoded_body = json.loads(body_json)
        final_raw_body = lz_compress_to_base64(_compact_json(decoded_body))
    elif raw_body:
        decoded_body = _try_decode_text_payload(raw_body)

    return {
        "method": "POST",
        "headers": {
            "Accept": "application/json",
            "Content-Type": "text/plain; charset=utf-8",
            "User-Agent": mobile_user_agent,
        },
        "raw_body": final_raw_body,
        "decoded_body": decoded_body,
        "source": "inline",
    }


def build_request_configs(args: argparse.Namespace) -> Dict[str, Dict[str, Any]]:
    configs: Dict[str, Dict[str, Any]] = {}

    if args.har:
        har_configs = load_request_configs_from_har(args.har)
        configs.update(har_configs)
        if har_configs:
            print(f"[INFO] Loaded request configs from HAR: {args.har}")

    products_config = _inline_request_config(
        raw_body=args.products_raw_body,
        body_json=args.products_body_json,
        mobile_user_agent=args.mobile_user_agent,
    )
    if products_config:
        configs["/product/ProductsByCategory"] = products_config

    prices_config = _inline_request_config(
        raw_body=args.prices_raw_body,
        body_json=args.prices_body_json,
        mobile_user_agent=args.mobile_user_agent,
    )
    if prices_config:
        configs["/product/ItemsPrices"] = prices_config

    return configs


def expand_categories(categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    expanded: List[Dict[str, Any]] = []

    def walk(item: Dict[str, Any], parent_id: Any = None, parent_name: Optional[str] = None) -> None:
        children = (
            item.get("SubItmes")
            or item.get("SubItems")
            or item.get("SubCategories")
            or item.get("subitmes")
            or item.get("subcategories")
            or []
        )
        row = dict(item)
        row["ParentCategoryId"] = parent_id
        row["ParentCategoryName"] = parent_name
        row["ChildrenCount"] = len(children) if isinstance(children, list) else 0
        row["IsLeaf"] = row["ChildrenCount"] == 0
        expanded.append(row)

        if not isinstance(children, list):
            return

        current_id = extract_category_id(item)
        current_name = extract_category_name(item)
        for child in children:
            if isinstance(child, dict):
                walk(child, current_id, current_name)

    for category in categories:
        if isinstance(category, dict):
            walk(category)

    return expanded


def extract_category_id(record: Dict[str, Any]) -> Optional[int]:
    for key in ("id", "Id", "CID", "cid", "categoryId", "CategoryId"):
        value = record.get(key)
        if value in (None, ""):
            continue
        try:
            return int(value)
        except Exception:
            continue
    return None


def extract_category_name(record: Dict[str, Any]) -> str:
    for key in ("NameAr", "TitleAR", "nameAr", "TitleEn", "Name", "title", "name"):
        value = record.get(key)
        if value:
            return str(value)
    return ""


def _first_existing(columns: List[str], candidates: List[str]) -> Optional[str]:
    column_set = set(columns)
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    return None


def _coerce_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


class ApiClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 20.0,
        api_key_env: str = "FUSTOG_API_KEY",
        request_configs: Optional[Dict[str, Dict[str, Any]]] = None,
        proxy: Optional[str] = None,
        mobile_user_agent: str = _DEFAULT_MOBILE_USER_AGENT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.request_configs = request_configs or {}

        load_dotenv()
        api_key = os.getenv(api_key_env)
        headers: Dict[str, str] = {
            "Accept": "application/json, */*;q=0.5",
            "Accept-Encoding": "identity",
            "User-Agent": mobile_user_agent,
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        client_kwargs: Dict[str, Any] = {
            "timeout": timeout,
            "headers": headers,
            "follow_redirects": True,
        }
        if proxy:
            client_kwargs["proxy"] = proxy

        self._client = httpx.Client(**client_kwargs)

    def has_request_config(self, endpoint: str) -> bool:
        return endpoint in self.request_configs

    def close(self) -> None:
        self._client.close()

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    def request_json(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        raw_body: Optional[str] = None,
        json_body: Any = None,
    ) -> Any:
        url = f"{self.base_url}{endpoint}"
        response = self._client.request(
            method.upper(),
            url,
            params=params,
            headers=headers,
            content=raw_body,
            json=json_body,
            timeout=30.0,
        )

        if response.status_code == 200 and len(response.content) == 0:
            print(f"[WARN] Empty response from {url}")
            return []

        response.raise_for_status()

        try:
            return response.json()
        except Exception:
            text = response.text or ""
            content_type = (response.headers.get("content-type") or "").lower()
            if text and (content_type.startswith("text/") or "text/plain" in content_type):
                try:
                    return json.loads(lz_decompress_from_base64(text))
                except Exception:
                    pass

            snippet = response.content[:200]
            print(f"[WARN] Non-JSON response from {url} ct={content_type} bytes={len(response.content)} snippet={snippet!r}")
            raise

    def get_json(self, endpoint: str, params: Optional[Dict[str, Any]] = None, method: str = "GET") -> Any:
        return self.request_json(endpoint=endpoint, method=method, params=params)

    def replay_request(self, endpoint: str, overrides: Optional[Dict[str, Any]] = None) -> Any:
        config = self.request_configs.get(endpoint)
        if not config:
            raise ValueError(f"No request config available for {endpoint}")

        method = config.get("method", "POST")
        headers = config.get("headers") or {}
        raw_body = config.get("raw_body")
        decoded_body = config.get("decoded_body")

        if overrides and isinstance(decoded_body, dict):
            merged_body = json.loads(json.dumps(decoded_body, ensure_ascii=False))
            merged_body.update(overrides)
            raw_body = lz_compress_to_base64(_compact_json(merged_body))
        elif overrides and raw_body:
            for key, value in overrides.items():
                raw_body = raw_body.replace(f"{{{{{key}}}}}", str(value))

        return self.request_json(
            endpoint=endpoint,
            method=method,
            headers=headers,
            raw_body=raw_body,
        )


def get_env_base_url() -> str:
    load_dotenv()
    base = os.getenv("VITE_API_BASE_URL") or os.getenv("API_BASE_URL")
    if base:
        return base
    return "https://api.fustog.app/api/v1"


def fetch_products_for_category(api: ApiClient, category_id: int) -> Any:
    endpoint = "/product/ProductsByCategory"
    if api.has_request_config(endpoint):
        config = api.request_configs.get(endpoint, {})
        decoded_body = config.get("decoded_body")
        raw_body = config.get("raw_body") or ""
        supports_override = False

        if isinstance(decoded_body, dict):
            supports_override = "categoryId" in decoded_body or "CategoryId" in decoded_body
            if not supports_override and "query" in decoded_body and "stores" in decoded_body:
                if not config.get("_warned_search_payload"):
                    print("[WARN] ProductsByCategory request body looks like a search payload, not a category payload; skipping HAR/mobile replay for products.")
                    config["_warned_search_payload"] = True
                return []
            if not supports_override:
                supports_override = True
        elif "{{categoryId}}" in raw_body:
            supports_override = True

        if not supports_override:
            if not config.get("_warned_opaque_payload"):
                print("[WARN] ProductsByCategory request body cannot be parameterized by categoryId; skipping HAR/mobile replay for products.")
                config["_warned_opaque_payload"] = True
            return []

        try:
            return api.replay_request(endpoint, overrides={"categoryId": category_id})
        except Exception as error:
            print(f"[WARN] HAR/mobile replay failed for category {category_id}: {error}")

    try:
        return api.get_json(endpoint, params={"categoryId": category_id}, method="GET")
    except Exception as get_error:
        try:
            return api.get_json(endpoint, params={"categoryId": category_id}, method="POST")
        except Exception as post_error:
            print(f"[WARN] Both GET and POST failed for category {category_id}")
            print(f"  GET error: {get_error}")
            print(f"  POST error: {post_error}")
            return []


def fetch_prices(api: ApiClient) -> Any:
    endpoint = "/product/ItemsPrices"
    if api.has_request_config(endpoint):
        try:
            return api.replay_request(endpoint)
        except Exception as error:
            print(f"[WARN] HAR/mobile replay failed for ItemsPrices: {error}")

    try:
        return api.get_json(endpoint, method="GET")
    except Exception:
        return api.get_json(endpoint, method="POST")


def derive_prices_from_products(products_df: pd.DataFrame) -> pd.DataFrame:
    if products_df.empty or "prices" not in products_df.columns:
        return pd.DataFrame()

    product_id_col = _first_existing(products_df.columns.tolist(), ["id", "fid", "productid", "pid"])
    if not product_id_col:
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []
    for _, row in products_df.iterrows():
        price_map = row.get("prices")
        if isinstance(price_map, str):
            try:
                price_map = json.loads(price_map)
            except Exception:
                continue
        if not isinstance(price_map, dict):
            continue

        product_id = row.get(product_id_col)
        for store_id, value in price_map.items():
            price_value = _coerce_float(value)
            if price_value is None:
                continue
            rows.append(
                {
                    "productid": product_id,
                    "storeid": store_id,
                    "price": price_value,
                }
            )

    if not rows:
        return pd.DataFrame()
    return _normalize_columns(pd.DataFrame(rows))


def fetch_all(api: ApiClient) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    categories = api.get_json("/category/Categories")
    if not isinstance(categories, list):
        categories = [categories] if categories else []

    expanded_categories = expand_categories(categories)
    cat_df = _normalize_columns(pd.DataFrame(expanded_categories))

    fetch_df = cat_df
    if not fetch_df.empty and "isleaf" in fetch_df.columns:
        leaf_df = fetch_df[fetch_df["isleaf"] == True]  # noqa: E712
        if not leaf_df.empty:
            fetch_df = leaf_df

    all_products: List[Dict[str, Any]] = []
    seen_category_ids: set[int] = set()

    for _, row in tqdm(fetch_df.iterrows(), total=len(fetch_df), desc="Fetching products by category"):
        category_id = extract_category_id(row.to_dict())
        if not category_id or category_id in seen_category_ids:
            continue

        seen_category_ids.add(category_id)
        products = fetch_products_for_category(api, category_id)
        if isinstance(products, list):
            for product in products:
                if isinstance(product, dict):
                    product.setdefault("_requestedCategoryId", category_id)
                    all_products.append(product)
        elif isinstance(products, dict):
            products.setdefault("_requestedCategoryId", category_id)
            all_products.append(products)

    prod_df = _normalize_columns(pd.DataFrame(all_products))

    try:
        prices = fetch_prices(api)
        if isinstance(prices, list):
            prices_df = _normalize_columns(pd.DataFrame(prices))
        elif isinstance(prices, dict):
            prices_df = _normalize_columns(pd.DataFrame([prices]))
        else:
            prices_df = pd.DataFrame()
    except Exception as error:
        print(f"[WARN] Failed to fetch prices: {error}")
        prices_df = pd.DataFrame()

    if prices_df.empty:
        derived_prices_df = derive_prices_from_products(prod_df)
        if not derived_prices_df.empty:
            print("[INFO] Derived price rows from embedded product prices")
            prices_df = derived_prices_df

    return cat_df, prod_df, prices_df


def compare_prices(products_df: pd.DataFrame, prices_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if products_df.empty or prices_df.empty:
        raise ValueError("Products and prices data are required for comparison")

    products = products_df.copy()
    prices = prices_df.copy()

    product_id_col = _first_existing(products.columns.tolist(), ["id", "fid", "productid", "pid"])
    product_name_col = _first_existing(products.columns.tolist(), ["name", "titlear", "fullname", "title", "titleen"])
    price_product_col = _first_existing(prices.columns.tolist(), ["productid", "fid", "id", "itemid"])
    price_value_col = _first_existing(prices.columns.tolist(), ["price", "saleprice", "itemprice", "value"])
    price_store_col = _first_existing(prices.columns.tolist(), ["storeid", "sid", "retailerid", "store"])

    if not all([product_id_col, product_name_col, price_product_col, price_value_col, price_store_col]):
        raise ValueError("Input dataframes missing required columns for merge/comparison")

    products = products.rename(columns={product_id_col: "id", product_name_col: "name"})
    prices = prices.rename(columns={price_product_col: "productid", price_value_col: "price", price_store_col: "storeid"})

    prices["price"] = pd.to_numeric(prices["price"], errors="coerce")
    prices = prices.dropna(subset=["productid", "storeid", "price"])

    merged = prices.merge(products, left_on="productid", right_on="id", how="left", suffixes=("_price", "_product"))
    merged = merged.rename(columns={"id": "product_id"})

    group = merged.groupby("product_id", as_index=False).agg(
        lowest_price=("price", "min"),
        highest_price=("price", "max"),
        stores_count=("storeid", "nunique"),
    )
    group["price_spread"] = group["highest_price"] - group["lowest_price"]

    name_map = products.set_index("id")["name"].to_dict()
    group["product_name"] = group["product_id"].map(name_map)
    group = group[["product_id", "product_name", "lowest_price", "highest_price", "price_spread", "stores_count"]]

    return merged, group


def export_outputs(
    categories_df: pd.DataFrame,
    products_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    merged_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> Dict[str, str]:
    os.makedirs("data", exist_ok=True)
    now = datetime.now().strftime("%Y_%m_%d_%H%M%S")

    files: Dict[str, str] = {}

    def save_csv(name: str, df: pd.DataFrame) -> None:
        path = os.path.join("data", f"{name}_{now}.csv")
        df.to_csv(path, index=False, encoding="utf-8")
        files[f"{name}_csv"] = path

    def save_xlsx(name: str, df: pd.DataFrame) -> None:
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
        save_csv(label, df)
        save_xlsx(label, df)

    index_path = os.path.join("data", f"index_{now}.csv")
    index_df = pd.DataFrame([{"name": key, "path": value} for key, value in files.items()])
    index_df.to_csv(index_path, index=False, encoding="utf-8")
    files["index_csv"] = index_path
    return files


def print_quick_stats(categories_df: pd.DataFrame, products_df: pd.DataFrame, prices_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    def null_pct(df: pd.DataFrame) -> float:
        if not df.size:
            return 0.0
        return float((df.isna().sum().sum() / (df.shape[0] * max(df.shape[1], 1))) * 100.0)

    print("\n=== Quick Stats ===")
    print(f"categories: count={len(categories_df)}")
    print(f"products:   count={len(products_df)} null%={null_pct(products_df):.2f}%")
    print(f"prices:     count={len(prices_df)} null%={null_pct(prices_df):.2f}%")
    if not summary_df.empty:
        print(
            "summary:    "
            f"unique_products={summary_df['product_id'].nunique()} "
            f"min_price={summary_df['lowest_price'].min()} "
            f"max_price={summary_df['highest_price'].max()}"
        )
    else:
        print("summary:    no comparison data")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Fustog categories, products, prices, and comparison outputs.")
    parser.add_argument("--har", help="HAR file with successful mobile requests for ProductsByCategory and/or ItemsPrices")
    parser.add_argument("--products-raw-body", help="Exact compressed text/plain body for /product/ProductsByCategory")
    parser.add_argument("--products-body-json", help="JSON body to LZ-compress before calling /product/ProductsByCategory")
    parser.add_argument("--prices-raw-body", help="Exact compressed text/plain body for /product/ItemsPrices")
    parser.add_argument("--prices-body-json", help="JSON body to LZ-compress before calling /product/ItemsPrices")
    parser.add_argument("--proxy", help="Optional HTTP proxy, for example http://localhost:9495")
    parser.add_argument("--mobile-user-agent", default=_DEFAULT_MOBILE_USER_AGENT, help="Mobile app user agent")
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    try:
        base_url = get_env_base_url()
        request_configs = build_request_configs(args)
        api = ApiClient(
            base_url=base_url,
            request_configs=request_configs,
            proxy=args.proxy,
            mobile_user_agent=args.mobile_user_agent,
        )

        try:
            categories_df, products_df, prices_df = fetch_all(api)
        finally:
            api.close()

        if not prices_df.empty and len(prices_df) > 0:
            merged_df, summary_df = compare_prices(products_df, prices_df)
        else:
            print("[INFO] Skipping price comparison because no price rows were fetched")
            merged_df = pd.DataFrame()
            summary_df = pd.DataFrame()

        paths = export_outputs(categories_df, products_df, prices_df, merged_df, summary_df)
        print_quick_stats(categories_df, products_df, prices_df, summary_df)

        print("\nOutputs:")
        for key, value in paths.items():
            print(f"- {key}: {value}")

        return 0
    except Exception as error:
        print(f"Error in main: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
