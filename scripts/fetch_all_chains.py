#!/usr/bin/env python3
"""
Fetch ALL available supermarket chains from Fustog API.
Gets data for 9 chains available in Riyadh:
  RID=1  pos=1  SID=20  : Panda Express (neighborhood stores)
  RID=2  pos=2  SID=9   : Panda (hypermarket)
  RID=3  pos=3  SID=376 : Tamimi Markets
  RID=4  pos=4  SID=4   : Al Sadhan
  RID=5  pos=5  SID=1   : Othaim Markets
  RID=6  pos=6  SID=1   : LuLu Hypermarket (old)
  RID=9  pos=7  SID=1   : Carrefour (Riyadh)
  RID=25 pos=8  SID=5   : Farm Superstores (RUH-NAF001)
  RID=66 pos=9  SID=3755: LuLu Hypermarket (new)
"""

from __future__ import annotations
import json, sys
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
# Extended STORES: all 9 chains available in Riyadh
STORES = '{"1":20,"2":9,"3":376,"4":4,"5":1,"6":1,"7":1,"8":5,"9":3755}'
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SEARCH_TERMS = [
    "حليب", "زيت", "رز", "سكر", "دجاج", "لحم", "خبز", "جبن", "ماء", "عصير",
    "شاي", "قهوة", "معكرونة", "طحين", "بيض", "زبدة", "تونة", "صلصة", "بسكويت",
    "شيبس", "شوكولاتة", "مكسرات", "عسل", "مربى", "كاتشب", "مايونيز", "فول",
    "طماطم", "خل", "ملح", "فلفل", "كمون", "كريمة", "زبادي", "آيس كريم",
    "عافية", "المراعي", "نادك", "السعودية", "ربيع", "نستله",
    "تايد", "فيري", "داوني", "كلوركس", "ديتول", "بامبرز", "مناديل",
    "صابون", "شامبو", "معجون", "فرشاة", "غسول", "كريم",
    "تمر", "زعفران", "هيل", "قهوة سعودية", "لبن",
    "كورن فليكس", "عصير برتقال", "نودلز", "سمك", "روبيان",
]


def decompress_from_base64(value: str) -> str:
    if not value:
        return ""
    return _decompress(len(value), 32, lambda i: REV_DIC.get(value[i], 0) if i < len(value) else 0)


def _decompress(length: int, reset_value: int, get_next_value) -> str:
    dictionary: dict = {i: chr(i) for i in range(3)}
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


# RID → brand mapping (discovered via probe)
RETAILER_BRANDS = {
    1: {"ar": "بنده إكسبريس", "en": "Panda Express"},
    2: {"ar": "بنده", "en": "Panda"},
    3: {"ar": "أسواق التميمي", "en": "Tamimi Markets"},
    4: {"ar": "أسواق السدحان", "en": "Al Sadhan"},
    5: {"ar": "أسواق العثيم", "en": "Othaim Markets"},
    6: {"ar": "لولو هايبر ماركت", "en": "LuLu"},
    9: {"ar": "كارفور", "en": "Carrefour"},
    25: {"ar": "فارم سوبرستورز", "en": "Farm Superstores"},
    66: {"ar": "لولو هايبر ماركت (جديد)", "en": "LuLu (New)"},
}


def build_enriched_prices(products: List[Dict[str, Any]], store_lookup: Dict[str, Dict]) -> pd.DataFrame:
    """Build enriched prices CSV with all columns the platform needs."""
    rows: List[Dict[str, Any]] = []
    for product in products:
        fid = product.get("FID")
        prices = product.get("Prices") or {}
        if not isinstance(prices, dict):
            continue
        for store_key, price in prices.items():
            if not isinstance(price, (int, float)) or price <= 0:
                continue
            si = store_lookup.get(str(store_key), {})
            rows.append({
                "FID": fid,
                "TitleAr": product.get("TitleAr", ""),
                "TitleEn": product.get("TitleEn", ""),
                "BrandAR": product.get("BrandAR", ""),
                "BrandEN": product.get("BrandEN", ""),
                "CateguryAR": product.get("CateguryAR", ""),
                "CateguryEN": product.get("CateguryEN", ""),
                "AttrUnit": product.get("AttrUnit", ""),
                "AttrVal": product.get("AttrVal", ""),
                "ImageURL": product.get("ImageURL", ""),
                "StoreKey": store_key,
                "Price": float(price),
                "retailer_brand_ar": si.get("retailer_brand_ar", ""),
                "retailer_brand_en": si.get("retailer_brand_en", ""),
                "store_name_ar": si.get("store_name_ar", ""),
                "store_name_en": si.get("store_name_en", ""),
                "rid": si.get("rid", ""),
                "sid": si.get("sid", ""),
            })
    return pd.DataFrame(rows)


def build_matching_summary(products: List[Dict[str, Any]], store_lookup: Dict[str, Dict]) -> pd.DataFrame:
    """Build matching summary CSV with columns expected by platform dataCache."""
    rows: List[Dict[str, Any]] = []
    for product in products:
        fid = product.get("FID")
        prices = {str(k): float(v) for k, v in (product.get("Prices") or {}).items()
                  if isinstance(v, (int, float)) and float(v) > 0}
        if not prices:
            continue
        min_p = min(prices.values())
        max_p = max(prices.values())
        price_rows = len(prices)
        cheapest_key = min(prices, key=prices.get)
        cheapest_si = store_lookup.get(cheapest_key, {})
        rows.append({
            "FID": fid,
            "TitleAr": product.get("TitleAr", ""),
            "TitleEn": product.get("TitleEn", ""),
            "BrandAR": product.get("BrandAR", ""),
            "BrandEN": product.get("BrandEN", ""),
            "CateguryAR": product.get("CateguryAR", ""),
            "CateguryEN": product.get("CateguryEN", ""),
            "min_price": round(min_p, 2),
            "max_price": round(max_p, 2),
            "price_spread": round(max_p - min_p, 2),
            "stores_count": price_rows,
            "price_rows": price_rows,
            "cheapest_price": round(min_p, 2),
            "cheapest_store_key": cheapest_key,
            "cheapest_store_name_ar": cheapest_si.get("store_name_ar", ""),
            "cheapest_store_name_en": cheapest_si.get("store_name_en", ""),
            "cheapest_sid": cheapest_si.get("sid", ""),
            "cheapest_rid": cheapest_si.get("rid", ""),
        })
    return pd.DataFrame(rows)


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

    stores_dict = json.loads(STORES)  # {"1":20, "2":9, ...}

    with requests.Session() as session:
        print("Fetching NearestStores...")
        nearest = api_post(session, "stores/NearestStores", {
            "Latitude": 24.790883230664154,
            "Longitude": 46.6621698799985,
            "uid": UID,
        }) or []

        store_info: Dict[str, Dict] = {}
        for i, s in enumerate(nearest):
            pos = str(i + 1)
            if pos in stores_dict:
                rid = s.get("RID")
                sid = stores_dict[pos]
                brand = RETAILER_BRANDS.get(rid, {"ar": "", "en": ""})
                store_info[pos] = {
                    "store_key": int(pos),
                    "sid": sid,
                    "rid": rid,
                    "store_name_ar": s.get("NameAr", ""),
                    "store_name_en": s.get("NameEn", ""),
                    "retailer_brand_ar": brand["ar"],
                    "retailer_brand_en": brand["en"],
                    "is_integration_ready": s.get("IsIntegrationReady", False),
                }
                print(f"  StoreKey={pos} RID={rid} SID={sid} Brand={brand['en']} | {s.get('NameEn')}")

        print(f"\nFetching products for {len(stores_dict)} stores with {len(SEARCH_TERMS)} search terms...")
        all_products: List[Dict[str, Any]] = []
        seen_fids: set = set()
        term_stats = []

        for i, term in enumerate(SEARCH_TERMS):
            items = api_post(session, "product/search", {
                "query": term, "stores": STORES, "uid": UID
            }) or []
            new_count = 0
            for item in items:
                fid = item.get("FID")
                if fid and fid not in seen_fids:
                    seen_fids.add(fid)
                    all_products.append(item)
                    new_count += 1
            term_stats.append({"term": term, "results": len(items), "new": new_count, "total": len(all_products)})
            print(f"  [{i+1}/{len(SEARCH_TERMS)}] '{term}': {len(items)} results, {new_count} new (total {len(all_products)})")

    print(f"\nTotal products: {len(all_products)}")

    stores_rows = list(store_info.values())

    # 1. Stores lookup CSV
    stores_df = pd.DataFrame(stores_rows)
    stores_csv = DATA_DIR / f"fustog_stores_lookup_{timestamp}.csv"
    stores_df.to_csv(stores_csv, index=False, encoding="utf-8")
    print(f"Saved stores lookup: {stores_csv}")

    # 2. Enriched prices CSV (with all fields platform needs)
    prices_df = build_enriched_prices(all_products, store_info)
    prices_csv = DATA_DIR / f"fustog_prices_enriched_long_{timestamp}.csv"
    prices_df.to_csv(prices_csv, index=False, encoding="utf-8")
    print(f"Saved prices enriched: {prices_csv} ({len(prices_df)} rows)")

    # 3. Matching summary CSV (with exact columns platform needs)
    matching_df = build_matching_summary(all_products, store_info)
    matching_csv = DATA_DIR / f"fustog_matching_summary_{timestamp}.csv"
    matching_df.to_csv(matching_csv, index=False, encoding="utf-8")
    print(f"Saved matching summary: {matching_csv} ({len(matching_df)} rows)")

    # 4. Metadata
    meta = {
        "fetched_at": datetime.now().isoformat(),
        "stores": STORES,
        "uid": UID,
        "total_products": len(all_products),
        "total_price_rows": len(prices_df),
        "store_count": len(stores_rows),
        "timestamp": timestamp,
        "store_map": store_info,
    }
    (DATA_DIR / f"fustog_fetch_meta_{timestamp}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n{'='*60}")
    print("FETCH COMPLETE!")
    print(f"Timestamp: {timestamp}")
    print(f"Stores: {len(stores_rows)}")
    print(f"Products: {len(all_products)}")
    print(f"Price rows: {len(prices_df)}")
    print(f"Matching rows: {len(matching_df)}")
    print(f"{'='*60}")
    print(f"\nCSV files ready in: {DATA_DIR}")
    print(f"  Stores:   {stores_csv.name}")
    print(f"  Prices:   {prices_csv.name}")
    print(f"  Matching: {matching_csv.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
