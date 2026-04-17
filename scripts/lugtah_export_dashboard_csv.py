#!/usr/bin/env python3
"""
Convert Lugtah restaurant_details.jsonl into the CSV files expected by the dashboard (platform/lib/dataCache.ts).

Outputs (under ./data with timestamp):
  - fustog_stores_lookup_<ts>.csv
  - fustog_prices_enriched_long_<ts>.csv
  - fustog_matching_summary_<ts>.csv

This lets the existing dashboard pages work without changing the UI.
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DATA_DIR = Path("data")
LUGTAH_DIR = DATA_DIR / "lugtah"
INPUT_JSONL = Path(os.environ.get("LUGTAH_DETAILS_JSONL", str(LUGTAH_DIR / "restaurant_details.jsonl")))


@dataclass(frozen=True)
class PlatformInfo:
  store_key: int
  name_en: str
  name_ar: str
  color: str
  logo_letter: str


PLATFORMS: Dict[str, PlatformInfo] = {
  "brand_app": PlatformInfo(1, "Official App", "التطبيق الرسمي", "#6A1B6A", "O"),
  "hungerstation": PlatformInfo(2, "HungerStation", "هنقرستيشن", "#E4002B", "H"),
  "jahez": PlatformInfo(3, "Jahez", "جاهز", "#6C3BAA", "J"),
  "chefz": PlatformInfo(4, "Chefz", "ذا شفز", "#B8860B", "C"),
  "keeta": PlatformInfo(5, "Keeta", "كيتا", "#FF6600", "K"),
  "toyou": PlatformInfo(6, "ToYou", "تويو", "#2563EB", "T"),
  "ninja": PlatformInfo(7, "Ninja", "نينجا", "#22C55E", "N"),
}


def _norm(s: str) -> str:
  s = (s or "").strip().lower()
  s = re.sub(r"\s+", " ", s)
  return s


def _safe_float(v: Any) -> Optional[float]:
  try:
    if v is None or v == "":
      return None
    return float(v)
  except Exception:
    return None


def _iter_jsonl(path: Path) -> Iterable[dict]:
  with path.open("r", encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if not line:
        continue
      try:
        obj = json.loads(line)
      except Exception:
        continue
      if isinstance(obj, dict):
        yield obj


def _items_from_detail(detail: dict) -> Iterable[dict]:
  # Both arrays have shape: {name,name_ar,image_url,platforms:[{platform,price,original_price,image_url}], ...}
  for key in ("items_with_diffs", "items_same_price"):
    arr = detail.get(key)
    if isinstance(arr, list):
      for item in arr:
        if isinstance(item, dict) and item.get("platforms"):
          yield item


def main() -> int:
  if not INPUT_JSONL.exists():
    raise SystemExit(f"Missing input JSONL: {INPUT_JSONL}")

  ts = datetime.now().strftime("%Y_%m_%d_%H%M%S")
  DATA_DIR.mkdir(parents=True, exist_ok=True)

  stores_path = DATA_DIR / f"fustog_stores_lookup_{ts}.csv"
  prices_path = DATA_DIR / f"fustog_prices_enriched_long_{ts}.csv"
  matching_path = DATA_DIR / f"fustog_matching_summary_{ts}.csv"

  # 1) stores lookup (platforms)
  store_rows: List[dict] = []
  for key, p in PLATFORMS.items():
    store_rows.append(
      {
        "store_key": p.store_key,
        "sid": p.store_key,
        "rid": p.store_key,
        "store_name_ar": p.name_ar,
        "store_name_en": p.name_en,
        "retailer_brand_ar": p.name_ar,
        "retailer_brand_en": p.name_en,
        "is_integration_ready": "True",
      }
    )

  with stores_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(store_rows[0].keys()))
    w.writeheader()
    w.writerows(store_rows)

  # 2) prices + matching
  # We create a stable per-restaurant item id by hashing (restaurant_id + normalized name_en)
  # and mapping to incrementing ints to keep FID small and readable.
  fid_map: Dict[Tuple[int, str], int] = {}
  next_fid = 1

  # Accumulators for matching
  match_acc: Dict[int, dict] = {}  # FID -> aggregated info + per-store prices

  price_fieldnames = [
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
    "Price",
    "retailer_brand_ar",
    "retailer_brand_en",
  ]

  with prices_path.open("w", newline="", encoding="utf-8") as f_prices:
    w_prices = csv.DictWriter(f_prices, fieldnames=price_fieldnames)
    w_prices.writeheader()

    for row in _iter_jsonl(INPUT_JSONL):
      rest_id = row.get("restaurant_id")
      rest = row.get("restaurant") if isinstance(row.get("restaurant"), dict) else {}
      detail = row.get("detail") if isinstance(row.get("detail"), dict) else {}
      if not isinstance(rest_id, int):
        continue

      brand_en = str(rest.get("name") or detail.get("name") or "")
      brand_ar = str(rest.get("name_ar") or detail.get("name_ar") or "")
      cuisine = str(rest.get("cuisine") or detail.get("cuisine") or "")
      category_en = cuisine
      category_ar = cuisine  # fallback

      for item in _items_from_detail(detail):
        title_en = str(item.get("name") or "")
        title_ar = str(item.get("name_ar") or "")
        image_url = str(item.get("image_url") or "")

        key = (rest_id, _norm(title_en) or _norm(title_ar))
        if key not in fid_map:
          fid_map[key] = next_fid
          next_fid += 1
        fid = fid_map[key]

        plats = item.get("platforms")
        if not isinstance(plats, list):
          continue

        for p in plats:
          if not isinstance(p, dict):
            continue
          plat_key = p.get("platform")
          if plat_key not in PLATFORMS:
            continue
          price = _safe_float(p.get("price"))
          if price is None or price <= 0:
            continue

          plat = PLATFORMS[str(plat_key)]
          w_prices.writerow(
            {
              "FID": fid,
              "TitleAr": title_ar,
              "TitleEn": title_en,
              "BrandAR": brand_ar,
              "BrandEN": brand_en,
              "CateguryAR": category_ar,
              "CateguryEN": category_en,
              "AttrUnit": "",
              "AttrVal": "",
              "ImageURL": image_url,
              "StoreKey": plat.store_key,
              "Price": price,
              "retailer_brand_ar": plat.name_ar,
              "retailer_brand_en": plat.name_en,
            }
          )

          acc = match_acc.get(fid)
          if not acc:
            acc = {
              "FID": fid,
              "TitleAr": title_ar,
              "TitleEn": title_en,
              "BrandAR": brand_ar,
              "BrandEN": brand_en,
              "CateguryAR": category_ar,
              "CateguryEN": category_en,
              "prices_by_store": {},  # store_key -> price
            }
            match_acc[fid] = acc
          acc["prices_by_store"][plat.store_key] = price

  # Build matching_summary
  matching_fieldnames = [
    "FID",
    "TitleAr",
    "TitleEn",
    "BrandAR",
    "BrandEN",
    "CateguryAR",
    "CateguryEN",
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

  with matching_path.open("w", newline="", encoding="utf-8") as f_match:
    w_match = csv.DictWriter(f_match, fieldnames=matching_fieldnames)
    w_match.writeheader()

    for fid, acc in match_acc.items():
      prices_map: Dict[int, float] = acc["prices_by_store"]
      if not prices_map:
        continue
      prices = list(prices_map.values())
      min_p = min(prices)
      max_p = max(prices)
      spread = max_p - min_p
      stores_count = len(prices_map)

      cheapest_store_key = min(prices_map.items(), key=lambda kv: kv[1])[0]
      cheapest = next((p for p in PLATFORMS.values() if p.store_key == cheapest_store_key), None)

      w_match.writerow(
        {
          "FID": fid,
          "TitleAr": acc.get("TitleAr", ""),
          "TitleEn": acc.get("TitleEn", ""),
          "BrandAR": acc.get("BrandAR", ""),
          "BrandEN": acc.get("BrandEN", ""),
          "CateguryAR": acc.get("CateguryAR", ""),
          "CateguryEN": acc.get("CateguryEN", ""),
          "min_price": round(min_p, 4),
          "max_price": round(max_p, 4),
          "price_spread": round(spread, 4),
          "stores_count": stores_count,
          "price_rows": stores_count,
          "cheapest_price": round(min_p, 4),
          "cheapest_store_key": cheapest_store_key,
          "cheapest_store_name_ar": cheapest.name_ar if cheapest else "",
          "cheapest_store_name_en": cheapest.name_en if cheapest else "",
          "cheapest_sid": cheapest_store_key,
          "cheapest_rid": cheapest_store_key,
        }
      )

  print("[ok] wrote:")
  print(f"- {stores_path}")
  print(f"- {prices_path}")
  print(f"- {matching_path}")
  print(f"[stats] items={len(match_acc)} price_rows written to {prices_path.name}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())

