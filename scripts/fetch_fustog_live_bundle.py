#!/usr/bin/env python3
"""Fetch currently reachable Fustog data and export normalized outputs."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


KEY_STR = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
REV_DIC = {c: i for i, c in enumerate(KEY_STR)}
BASE = "https://api.fustog.app/api/v1"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Fustog/1.4.2.1 CFNetwork/3860.300.31 Darwin/25.2.0",
    "Content-Type": "text/plain; charset=utf-8",
}
UID = 462464
STORES = '{"1":20,"2":9,"3":64,"4":4,"5":1,"6":1}'
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEARCH_TERMS = [
    "حليب", "زيت", "رز", "سكر", "دجاج", "لحم", "خبز", "جبن", "ماء", "عصير",
    "شاي", "قهوة", "معكرونة", "طحين", "بيض", "زبدة", "تونة", "صلصة", "بسكويت",
    "شيبس", "شوكولاتة", "مكسرات", "عسل", "مربى", "كاتشب", "مايونيز", "فول",
    "طماطم", "خل", "ملح", "فلفل", "كمون", "كريمة", "زبادي", "آيس كريم",
    "عافية", "المراعي", "نادك", "السعودية", "ربيع", "كيلوقز", "نستله",
    "تايد", "فيري", "داوني", "كلوركس", "ديتول", "بامبرز", "مناديل",
    "صابون", "شامبو", "معجون", "فرشاة", "غسول", "كريم",
]


def decompress_from_base64(value: str) -> str:
    if not value:
        return ""
    return _decompress(len(value), 32, lambda i: REV_DIC.get(value[i], 0) if i < len(value) else 0)


def _decompress(length: int, reset_value: int, get_next_value) -> str:
    dictionary = {i: i for i in range(3)}
    enlarge_in, dict_size, num_bits = 4, 4, 3
    result, w = [], ""
    data_val, data_position, data_index = get_next_value(0), reset_value, 1

    def read_bits(max_bits: int) -> int:
        nonlocal data_val, data_position, data_index
        bits, power, max_power = 0, 1, 2**max_bits
        while power != max_power:
            resb = data_val & data_position
            data_position >>= 1
            if data_position == 0:
                data_position = reset_value
                data_val = get_next_value(data_index)
                data_index += 1
            bits |= (1 if resb > 0 else 0) * power
            power <<= 1
        return bits

    next_value = read_bits(2)
    if next_value == 0:
        c = chr(read_bits(8))
    elif next_value == 1:
        c = chr(read_bits(16))
    elif next_value == 2:
        return ""
    else:
        return ""

    dictionary[3] = c
    w = c
    result.append(c)

    while data_index <= length:
        code = read_bits(num_bits)
        if code == 0:
            dictionary[dict_size] = chr(read_bits(8))
            dict_size += 1
            code = dict_size - 1
            enlarge_in -= 1
        elif code == 1:
            dictionary[dict_size] = chr(read_bits(16))
            dict_size += 1
            code = dict_size - 1
            enlarge_in -= 1
        elif code == 2:
            return "".join(result)

        if enlarge_in == 0:
            enlarge_in = 2**num_bits
            num_bits += 1

        entry = dictionary.get(code, w + w[0] if code == dict_size else None)
        if entry is None:
            return "".join(result)

        result.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        enlarge_in -= 1

        if enlarge_in == 0:
            enlarge_in = 2**num_bits
            num_bits += 1
        w = entry

    return "".join(result)


def compress_to_base64(uncompressed: str) -> str:
    if not uncompressed:
        return ""
    return _compress(uncompressed, 6, lambda a: KEY_STR[a])


def _compress(value: str, bits_per_char: int, get_char) -> str:
    dictionary: Dict[str, int] = {}
    dictionary_to_create: Dict[str, bool] = {}
    w, enlarge_in, dict_size, num_bits = "", 2, 3, 2
    data_val, data_position = 0, 0
    output: List[str] = []

    def write_bit(bit: int) -> None:
        nonlocal data_val, data_position
        data_val = (data_val << 1) | bit
        if data_position == bits_per_char - 1:
            data_position = 0
            output.append(get_char(data_val))
            data_val = 0
        else:
            data_position += 1

    def write_bits(bit_value: int, width: int) -> None:
        for _ in range(width):
            write_bit(bit_value & 1)
            bit_value >>= 1

    def write_code(chunk: str) -> None:
        nonlocal enlarge_in, num_bits
        if chunk in dictionary_to_create:
            char_code = ord(chunk[0])
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
            del dictionary_to_create[chunk]
        else:
            write_bits(dictionary[chunk], num_bits)
        enlarge_in -= 1
        if enlarge_in == 0:
            enlarge_in = 2**num_bits
            num_bits += 1

    for char in value:
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
            output.append(get_char(data_val))
            break
        data_position += 1

    return "".join(output)


def api_get(session: requests.Session, endpoint: str) -> Optional[Any]:
    response = session.get(f"{BASE}/{endpoint}", headers=HEADERS, timeout=30)
    if response.status_code != 200:
        return None
    text = decompress_from_base64(response.text)
    return json.loads(text) if text else None


def api_post(session: requests.Session, endpoint: str, body: Dict[str, Any]) -> Optional[Any]:
    payload = compress_to_base64(json.dumps(body, ensure_ascii=False, separators=(",", ":")))
    response = session.post(f"{BASE}/{endpoint}", headers=HEADERS, data=payload, timeout=30)
    if response.status_code != 200:
        return None
    text = decompress_from_base64(response.text)
    return json.loads(text) if text else None


def normalize_products(products: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for product in products:
        row = dict(product)
        if isinstance(row.get("Prices"), dict):
            row["StoresWithPrice"] = sum(1 for _, price in row["Prices"].items() if isinstance(price, (int, float)) and price > 0)
        else:
            row["StoresWithPrice"] = 0
        rows.append(row)
    return pd.DataFrame(rows)


def normalize_prices(products: List[Dict[str, Any]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for product in products:
        fid = product.get("FID")
        title_ar = product.get("TitleAr")
        brand_ar = product.get("BrandAR")
        prices = product.get("Prices") or {}
        if not isinstance(prices, dict):
            continue
        for store_key, price in prices.items():
            if not isinstance(price, (int, float)) or price <= 0:
                continue
            rows.append(
                {
                    "FID": fid,
                    "TitleAr": title_ar,
                    "BrandAR": brand_ar,
                    "StoreKey": store_key,
                    "Price": float(price),
                }
            )
    return pd.DataFrame(rows)


def normalize_store_summary(products: List[Dict[str, Any]]) -> pd.DataFrame:
    price_df = normalize_prices(products)
    if price_df.empty:
        return price_df
    return (
        price_df.groupby("StoreKey", as_index=False)
        .agg(ProductCount=("FID", "nunique"), PriceRows=("Price", "count"), MinPrice=("Price", "min"), MaxPrice=("Price", "max"))
        .sort_values(["ProductCount", "PriceRows"], ascending=[False, False])
    )


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

    with requests.Session() as session:
        categories = api_get(session, "category/Categories")
        retailer_settings = api_get(session, "retailer/Settings")
        cities = api_get(session, "cities/AllCities")
        nearest_stores = api_post(
            session,
            "stores/NearestStores",
            {"Latitude": 24.790883230664154, "Longitude": 46.6621698799985, "uid": UID},
        )

        all_products: List[Dict[str, Any]] = []
        seen_fids = set()
        term_stats: List[Dict[str, Any]] = []

        for term in SEARCH_TERMS:
            items = api_post(session, "product/search", {"query": term, "stores": STORES, "uid": UID}) or []
            new_count = 0
            for item in items:
                fid = item.get("FID")
                if fid and fid not in seen_fids:
                    seen_fids.add(fid)
                    all_products.append(item)
                    new_count += 1
            term_stats.append({"term": term, "results": len(items), "new": new_count, "total": len(all_products)})
            print(f"{term}: {len(items)} results, {new_count} new (total {len(all_products)})")

    products_df = normalize_products(all_products)
    prices_df = normalize_prices(all_products)
    stores_df = normalize_store_summary(all_products)

    metadata = {
        "fetched_at": datetime.now().isoformat(),
        "base": BASE,
        "uid": UID,
        "stores": STORES,
        "products_total": len(all_products),
        "prices_total": len(prices_df),
    }

    bundle = {
        "metadata": metadata,
        "categories": categories,
        "retailer_settings": retailer_settings,
        "cities": cities,
        "nearest_stores": nearest_stores,
        "term_stats": term_stats,
        "products": all_products,
    }

    json_path = DATA_DIR / f"fustog_live_bundle_{timestamp}.json"
    products_csv = DATA_DIR / f"fustog_live_products_{timestamp}.csv"
    prices_csv = DATA_DIR / f"fustog_live_prices_{timestamp}.csv"
    stores_csv = DATA_DIR / f"fustog_live_store_summary_{timestamp}.csv"
    terms_csv = DATA_DIR / f"fustog_live_term_stats_{timestamp}.csv"
    manifest_csv = DATA_DIR / f"fustog_live_files_{timestamp}.csv"

    json_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    products_df.to_csv(products_csv, index=False, encoding="utf-8")
    prices_df.to_csv(prices_csv, index=False, encoding="utf-8")
    stores_df.to_csv(stores_csv, index=False, encoding="utf-8")
    pd.DataFrame(term_stats).to_csv(terms_csv, index=False, encoding="utf-8")
    pd.DataFrame(
        [
            {"kind": "bundle_json", "file_name": json_path.name, "path": str(json_path), "rows": len(all_products)},
            {"kind": "products_csv", "file_name": products_csv.name, "path": str(products_csv), "rows": len(products_df)},
            {"kind": "prices_csv", "file_name": prices_csv.name, "path": str(prices_csv), "rows": len(prices_df)},
            {"kind": "stores_csv", "file_name": stores_csv.name, "path": str(stores_csv), "rows": len(stores_df)},
            {"kind": "terms_csv", "file_name": terms_csv.name, "path": str(terms_csv), "rows": len(term_stats)},
        ]
    ).to_csv(manifest_csv, index=False, encoding="utf-8")

    print("\nSaved:")
    print(json_path)
    print(products_csv)
    print(prices_csv)
    print(stores_csv)
    print(terms_csv)
    print(manifest_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
