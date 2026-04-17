#!/usr/bin/env python3
"""
Build exports from previously captured Fustog live bundle + CSVs.

Inputs (defaults align with current workspace live capture):
- data/fustog_live_bundle_YYYY_MM_DD_HHMMSS.json
- data/fustog_live_products_YYYY_MM_DD_HHMMSS.csv
- data/fustog_live_prices_YYYY_MM_DD_HHMMSS.csv

Outputs (timestamped) under data/:
- fustog_stores_lookup_<ts>.csv
- fustog_prices_enriched_long_<ts>.csv
- fustog_matching_summary_<ts>.csv
- fustog_exports_index_<ts>.csv
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


@dataclass(frozen=True)
class StoreLookupRow:
    store_key: int
    sid: int
    rid: Optional[int]
    store_name_ar: Optional[str]
    store_name_en: Optional[str]
    retailer_brand_ar: Optional[str]
    retailer_brand_en: Optional[str]
    is_integration_ready: Optional[bool]


def _now_tag() -> str:
    return datetime.now().strftime("%Y_%m_%d_%H%M%S")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_metadata_stores(meta_stores: Any) -> Dict[int, int]:
    """
    metadata.stores is usually a JSON string like:
      "{\"1\":20,\"2\":9,\"3\":64,\"4\":4,\"5\":1,\"6\":1}"
    Returns: {store_key:int -> sid:int}
    """
    if meta_stores is None:
        return {}

    if isinstance(meta_stores, str):
        try:
            parsed = json.loads(meta_stores)
        except Exception:
            return {}
    elif isinstance(meta_stores, dict):
        parsed = meta_stores
    else:
        return {}

    out: Dict[int, int] = {}
    for k, v in parsed.items():
        try:
            out[int(k)] = int(v)
        except Exception:
            continue
    return out


def _parse_jsonish(value: Any) -> Any:
    """
    Some columns are stored as stringified Python literals or JSON-ish strings.
    We try JSON first, then fall back to a very small safe normalization.
    """
    if value is None:
        return None
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    if not isinstance(value, str):
        return None

    s = value.strip()
    if not s or s in ("[]", "{}", "null", "None"):
        return [] if s == "[]" else ({} if s == "{}" else None)

    # Try strict JSON
    try:
        return json.loads(s)
    except Exception:
        pass

    # Try converting single quotes to double quotes (common in captures)
    if ("'" in s) and (s.startswith("[") or s.startswith("{")):
        try:
            return json.loads(s.replace("'", '"'))
        except Exception:
            return None
    return None


def infer_storekey_to_rid_from_products(products_df: pd.DataFrame) -> Dict[int, int]:
    """
    Infer StoreKey -> RID by correlating OnlinePrices (RID,Price) with Prices dict (StoreKey->price).
    This resolves ambiguous SIDs (e.g., StoreKey 5 and 6 both mapping to SID=1).
    """
    if products_df.empty:
        return {}
    if "OnlinePrices" not in products_df.columns or "Prices" not in products_df.columns:
        return {}

    votes: Dict[Tuple[int, int], int] = {}
    for _, row in products_df.iterrows():
        online = _parse_jsonish(row.get("OnlinePrices"))
        prices_map = _parse_jsonish(row.get("Prices"))
        if not isinstance(online, list) or not isinstance(prices_map, dict):
            continue

        # Normalize price map values to float
        norm_prices: Dict[int, float] = {}
        for sk, pv in prices_map.items():
            try:
                sk_i = int(sk)
                pv_f = float(pv)
                if pv_f > 0:
                    norm_prices[sk_i] = pv_f
            except Exception:
                continue
        if not norm_prices:
            continue

        for op in online:
            if not isinstance(op, dict):
                continue
            rid = op.get("RID")
            price = op.get("Price")
            try:
                rid_i = int(rid)
                price_f = float(price)
            except Exception:
                continue

            # Find StoreKeys with exact same price (typical for OnlinePrices)
            matches = [sk for sk, pv in norm_prices.items() if pv == price_f]
            if len(matches) == 1:
                sk = matches[0]
                votes[(sk, rid_i)] = votes.get((sk, rid_i), 0) + 1

    # Choose best RID per StoreKey
    best: Dict[int, Tuple[int, int]] = {}  # store_key -> (rid, votes)
    for (sk, rid), cnt in votes.items():
        cur = best.get(sk)
        if cur is None or cnt > cur[1]:
            best[sk] = (rid, cnt)

    return {sk: rid for sk, (rid, _cnt) in best.items()}


def build_store_lookup(bundle: Dict[str, Any], products_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    meta = bundle.get("metadata") or {}
    store_key_to_sid = _parse_metadata_stores(meta.get("stores"))

    nearest: List[Dict[str, Any]] = bundle.get("nearest_stores") or []
    sid_to_nearest: Dict[int, Dict[str, Any]] = {}
    rid_to_nearest: Dict[int, Dict[str, Any]] = {}
    for entry in nearest:
        try:
            rid = int(entry.get("RID"))
            if rid not in rid_to_nearest:
                rid_to_nearest[rid] = entry
        except Exception:
            pass
        try:
            sid = int(entry.get("SID"))
        except Exception:
            continue
        # Keep first occurrence per SID (good enough for lookup)
        if sid not in sid_to_nearest:
            sid_to_nearest[sid] = entry

    storekey_to_rid: Dict[int, int] = {}
    if products_df is not None and not products_df.empty:
        storekey_to_rid = infer_storekey_to_rid_from_products(products_df)

    rows: List[StoreLookupRow] = []
    for store_key, sid in sorted(store_key_to_sid.items(), key=lambda x: x[0]):
        sk_int = int(store_key)
        n: Dict[str, Any] = {}

        # Primary rule (observed in live exports): StoreKey matches RID (retailer id).
        if sk_int in rid_to_nearest:
            n = rid_to_nearest.get(sk_int) or {}
        else:
            # Fallback 1: inferred RID from products' OnlinePrices (best-effort)
            rid_hint = storekey_to_rid.get(sk_int)
            if rid_hint is not None and int(rid_hint) in rid_to_nearest:
                n = rid_to_nearest.get(int(rid_hint)) or {}
            else:
                # Fallback 2: match by SID from metadata.stores
                n = sid_to_nearest.get(int(sid)) or {}

        rid = n.get("RID")
        try:
            rid_int = int(rid) if rid is not None else None
        except Exception:
            rid_int = None

        name_ar = (n.get("NameAr") or None)
        name_en = (n.get("NameEn") or None)

        brand_ar, brand_en = infer_retailer_brand(rid=rid_int, name_ar=name_ar, name_en=name_en)

        rows.append(
            StoreLookupRow(
                store_key=int(store_key),
                sid=int(sid),
                rid=rid_int,
                store_name_ar=name_ar,
                store_name_en=name_en,
                retailer_brand_ar=brand_ar,
                retailer_brand_en=brand_en,
                is_integration_ready=(n.get("IsIntegrationReady") if "IsIntegrationReady" in n else None),
            )
        )

    df = pd.DataFrame([r.__dict__ for r in rows])
    if df.empty:
        return df

    return df.sort_values(["store_key"]).reset_index(drop=True)


def infer_retailer_brand(*, rid: Optional[int], name_ar: Optional[str], name_en: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Best-effort brand extraction from branch labels returned by Fustog.
    Some names include explicit brand tokens (e.g., 'أسواق العثيم', 'لولو', 'Panda').
    If not found, returns (None, None).
    """
    ar = (name_ar or "").strip()
    en = (name_en or "").strip()

    # Known RID->brand mappings discovered by probing Fustog NearestStores across cities
    # (kept minimal & conservative).
    rid_brand_hints: Dict[int, Tuple[str, str]] = {
        2: ("بنده", "Panda"),
        5: ("أسواق العثيم", "Othaim Markets"),
        6: ("لولو", "LuLu"),
    }
    if rid is not None and int(rid) in rid_brand_hints:
        return rid_brand_hints[int(rid)]

    # Arabic signals
    if "أسواق العثيم" in ar or "العثيم" in ar:
        return "أسواق العثيم", "Othaim Markets"
    if "لولو" in ar:
        return "لولو", "LuLu"
    # English signals
    if "Panda" in en or "PANDA" in en:
        return "بنده", "Panda"

    return None, None


def _safe_read_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(str(path))
    # Many Arabic texts; always force UTF-8.
    return pd.read_csv(path, encoding="utf-8", **kwargs)


def build_enriched_long(
    products_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    stores_df: pd.DataFrame,
) -> pd.DataFrame:
    # Normalize column casing for joins
    products = products_df.copy()
    prices = prices_df.copy()
    stores = stores_df.copy()

    # Ensure types
    if "FID" in products.columns:
        products["FID"] = pd.to_numeric(products["FID"], errors="coerce").astype("Int64")
    if "FID" in prices.columns:
        prices["FID"] = pd.to_numeric(prices["FID"], errors="coerce").astype("Int64")
    if "StoreKey" in prices.columns:
        prices["StoreKey"] = pd.to_numeric(prices["StoreKey"], errors="coerce").astype("Int64")
    if "store_key" in stores.columns:
        stores["store_key"] = pd.to_numeric(stores["store_key"], errors="coerce").astype("Int64")

    # Join prices -> products
    enriched = prices.merge(
        products,
        how="left",
        on="FID",
        suffixes=("", "_product"),
    )

    # Join store lookup
    if not stores.empty:
        enriched = enriched.merge(
            stores,
            how="left",
            left_on="StoreKey",
            right_on="store_key",
            suffixes=("", "_store"),
        )

    # Column selection (keep useful product info + store info)
    preferred_cols = [
        "FID",
        "TitleAr",
        "TitleEn",
        "BrandAR",
        "BrandEN",
        "CateguryAR",
        "CateguryEN",
        "AttrUnit",
        "AttrVal",
        "ImageURL",
        "StoreKey",
        "sid",
        "rid",
        "store_name_ar",
        "store_name_en",
        "is_integration_ready",
        "Price",
    ]
    existing = [c for c in preferred_cols if c in enriched.columns]
    # Keep any remaining columns at the end (for debugging/traceability)
    remaining = [c for c in enriched.columns if c not in existing]
    enriched = enriched[existing + remaining]

    return enriched


def build_matching_summary(enriched_long: pd.DataFrame) -> pd.DataFrame:
    if enriched_long.empty:
        return pd.DataFrame()

    df = enriched_long.copy()
    df["Price"] = pd.to_numeric(df.get("Price"), errors="coerce")
    df = df.dropna(subset=["FID", "Price"])

    group = df.groupby("FID", as_index=False).agg(
        min_price=("Price", "min"),
        max_price=("Price", "max"),
        stores_count=("StoreKey", "nunique"),
        price_rows=("Price", "count"),
    )
    group["price_spread"] = group["max_price"] - group["min_price"]

    # Cheapest store for each FID (tie: first by StoreKey)
    cheapest = (
        df.sort_values(["FID", "Price", "StoreKey"], ascending=[True, True, True])
        .drop_duplicates(subset=["FID"], keep="first")
        .rename(
            columns={
                "StoreKey": "cheapest_store_key",
                "sid": "cheapest_sid",
                "rid": "cheapest_rid",
                "store_name_ar": "cheapest_store_name_ar",
                "store_name_en": "cheapest_store_name_en",
                "Price": "cheapest_price",
            }
        )[
            [
                "FID",
                "cheapest_price",
                "cheapest_store_key",
                "cheapest_sid",
                "cheapest_rid",
                "cheapest_store_name_ar",
                "cheapest_store_name_en",
            ]
            if all(
                c in df.columns
                for c in [
                    "FID",
                    "StoreKey",
                    "sid",
                    "rid",
                    "store_name_ar",
                    "store_name_en",
                    "Price",
                ]
            )
            else ["FID", "cheapest_price", "cheapest_store_key"]
        ]
    )

    # Attach product names once
    prod_cols = [c for c in ["TitleAr", "TitleEn", "BrandAR", "BrandEN", "CateguryAR", "CateguryEN"] if c in df.columns]
    if prod_cols:
        prod_info = df.drop_duplicates(subset=["FID"], keep="first")[["FID"] + prod_cols]
        out = group.merge(prod_info, on="FID", how="left").merge(cheapest, on="FID", how="left")
    else:
        out = group.merge(cheapest, on="FID", how="left")

    # Reorder to keep identifiers first
    front = ["FID"] + prod_cols + [
        "min_price",
        "max_price",
        "price_spread",
        "stores_count",
        "price_rows",
        "cheapest_price",
        "cheapest_store_key",
        "cheapest_store_name_ar",
        "cheapest_store_name_en",
        "cheapest_sid",
        "cheapest_rid",
    ]
    existing_front = [c for c in front if c in out.columns]
    remaining = [c for c in out.columns if c not in existing_front]
    out = out[existing_front + remaining]
    return out


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build exports from captured Fustog live bundle.")
    parser.add_argument(
        "--bundle",
        default="f:/fustog/data/fustog_live_bundle_2026_04_15_143229.json",
        help="Path to bundle JSON",
    )
    parser.add_argument(
        "--products",
        default="f:/fustog/data/fustog_live_products_2026_04_15_143229.csv",
        help="Path to products CSV",
    )
    parser.add_argument(
        "--prices",
        default="f:/fustog/data/fustog_live_prices_2026_04_15_143229.csv",
        help="Path to prices CSV (long: FID,StoreKey,Price)",
    )
    parser.add_argument(
        "--out-dir",
        default="f:/fustog/data",
        help="Output directory",
    )
    args = parser.parse_args()

    bundle_path = Path(args.bundle)
    products_path = Path(args.products)
    prices_path = Path(args.prices)
    out_dir = Path(args.out_dir)

    bundle = _read_json(bundle_path)

    products_df = _safe_read_csv(products_path)
    prices_df = _safe_read_csv(prices_path)

    stores_lookup = build_store_lookup(bundle, products_df=products_df)

    enriched = build_enriched_long(products_df, prices_df, stores_lookup)
    summary = build_matching_summary(enriched)

    tag = _now_tag()
    stores_path = out_dir / f"fustog_stores_lookup_{tag}.csv"
    enriched_path = out_dir / f"fustog_prices_enriched_long_{tag}.csv"
    summary_path = out_dir / f"fustog_matching_summary_{tag}.csv"
    index_path = out_dir / f"fustog_exports_index_{tag}.csv"

    _write_csv(stores_lookup, stores_path)
    _write_csv(enriched, enriched_path)
    _write_csv(summary, summary_path)

    index_df = pd.DataFrame(
        [
            {"kind": "stores_lookup_csv", "path": str(stores_path), "rows": int(len(stores_lookup))},
            {"kind": "enriched_long_csv", "path": str(enriched_path), "rows": int(len(enriched))},
            {"kind": "matching_summary_csv", "path": str(summary_path), "rows": int(len(summary))},
            {"kind": "source_bundle", "path": str(bundle_path), "rows": None},
            {"kind": "source_products_csv", "path": str(products_path), "rows": int(len(products_df))},
            {"kind": "source_prices_csv", "path": str(prices_path), "rows": int(len(prices_df))},
        ]
    )
    _write_csv(index_df, index_path)

    meta = bundle.get("metadata") or {}
    print("=== Done ===")
    print(f"bundle:   {bundle_path}")
    print(f"products: {products_path} rows={len(products_df)} meta_products_total={meta.get('products_total')}")
    print(f"prices:   {prices_path} rows={len(prices_df)} meta_prices_total={meta.get('prices_total')}")
    print("")
    print("Outputs:")
    print(f"- stores_lookup: {stores_path}")
    print(f"- enriched_long: {enriched_path}")
    print(f"- summary:       {summary_path}")
    print(f"- index:         {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

