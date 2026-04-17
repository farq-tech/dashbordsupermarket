#!/usr/bin/env python3
"""
Export full Lugtah dataset (restaurant_details.jsonl) into multiple CSVs with rich info.

Input:
  - data/lugtah/restaurant_details.jsonl

Outputs (under ./data with timestamp):
  - lugtah_restaurants_<ts>.csv
  - lugtah_listings_<ts>.csv
  - lugtah_menu_items_long_<ts>.csv          (item x platform row)
  - lugtah_menu_items_summary_<ts>.csv       (item-level min/max/saving + counts)
  - lugtah_full_flat_<ts>.csv                (ONE huge CSV: restaurant + listing + item + platform)
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DATA_DIR = Path("data")
LUGTAH_DIR = DATA_DIR / "lugtah"
INPUT_JSONL = Path(os.environ.get("LUGTAH_DETAILS_JSONL", str(LUGTAH_DIR / "restaurant_details.jsonl")))


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


def _safe_int(v: Any) -> Optional[int]:
    try:
        if v is None or v == "":
            return None
        return int(v)
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


def _items_from_detail(detail: dict) -> Iterable[Tuple[str, dict]]:
    for key in ("items_with_diffs", "items_same_price"):
        arr = detail.get(key)
        if isinstance(arr, list):
            for item in arr:
                if isinstance(item, dict) and isinstance(item.get("platforms"), list):
                    yield key, item


def main() -> int:
    if not INPUT_JSONL.exists():
        raise SystemExit(f"Missing input JSONL: {INPUT_JSONL}")

    ts = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    restaurants_csv = DATA_DIR / f"lugtah_restaurants_{ts}.csv"
    listings_csv = DATA_DIR / f"lugtah_listings_{ts}.csv"
    items_long_csv = DATA_DIR / f"lugtah_menu_items_long_{ts}.csv"
    items_summary_csv = DATA_DIR / f"lugtah_menu_items_summary_{ts}.csv"
    full_flat_csv = DATA_DIR / f"lugtah_full_flat_{ts}.csv"

    # Fieldnames
    restaurants_fields = [
        "restaurant_id",
        "name_en",
        "name_ar",
        "cuisine",
        "city",
        "image_url",
        "platforms",
        "total_items",
        "total_menu_items",
        "match_rate",
        "items_with_diffs_count",
        "items_same_price_count",
        "max_saving",
        "total_reviews",
        "max_rating",
    ]

    listings_fields = [
        "restaurant_id",
        "platform",
        "platform_id",
        "platform_url",
        "rating",
        "review_count",
        "delivery_fee",
        "is_open",
        "discount_pct",
        "link",
        "promotions_json",
    ]

    items_long_fields = [
        "restaurant_id",
        "restaurant_name_en",
        "restaurant_name_ar",
        "cuisine",
        "item_group",  # items_with_diffs | items_same_price
        "item_name_en",
        "item_name_ar",
        "item_image_url",
        "platform",
        "price",
        "original_price",
        "platform_image_url",
        "min_price",
        "max_price",
        "saving",
        "saving_pct",
    ]

    items_summary_fields = [
        "restaurant_id",
        "restaurant_name_en",
        "restaurant_name_ar",
        "cuisine",
        "item_group",
        "item_key",
        "item_name_en",
        "item_name_ar",
        "item_image_url",
        "stores_count",
        "min_price",
        "max_price",
        "saving",
        "saving_pct",
    ]

    full_flat_fields = [
        # Restaurant
        "restaurant_id",
        "restaurant_name_en",
        "restaurant_name_ar",
        "cuisine",
        "city",
        "restaurant_image_url",
        "restaurant_platforms",
        "restaurant_total_items",
        "restaurant_total_menu_items",
        "restaurant_match_rate",
        "restaurant_max_saving",
        "restaurant_total_reviews",
        "restaurant_max_rating",
        # Listing (per platform)
        "listing_platform",
        "listing_platform_id",
        "listing_platform_url",
        "listing_rating",
        "listing_review_count",
        "listing_delivery_fee",
        "listing_is_open",
        "listing_discount_pct",
        "listing_link",
        "listing_promotions_json",
        # Item (menu)
        "item_group",
        "item_name_en",
        "item_name_ar",
        "item_image_url",
        # Item x platform pricing
        "price_platform",
        "price",
        "original_price",
        "platform_image_url",
        "min_price",
        "max_price",
        "saving",
        "saving_pct",
    ]

    # Accumulate item summaries on the fly
    # key: (restaurant_id, item_group, normalized_name) -> summary
    summaries: Dict[Tuple[int, str, str], dict] = {}

    with restaurants_csv.open("w", newline="", encoding="utf-8") as f_rest, \
        listings_csv.open("w", newline="", encoding="utf-8") as f_list, \
        items_long_csv.open("w", newline="", encoding="utf-8") as f_long, \
        full_flat_csv.open("w", newline="", encoding="utf-8") as f_flat:

        w_rest = csv.DictWriter(f_rest, fieldnames=restaurants_fields)
        w_list = csv.DictWriter(f_list, fieldnames=listings_fields)
        w_long = csv.DictWriter(f_long, fieldnames=items_long_fields)
        w_flat = csv.DictWriter(f_flat, fieldnames=full_flat_fields)
        w_rest.writeheader()
        w_list.writeheader()
        w_long.writeheader()
        w_flat.writeheader()

        for row in _iter_jsonl(INPUT_JSONL):
            rest_id = row.get("restaurant_id")
            detail = row.get("detail") if isinstance(row.get("detail"), dict) else {}
            if not isinstance(rest_id, int) or not detail:
                continue

            name_en = str(detail.get("name") or "")
            name_ar = str(detail.get("name_ar") or "")
            cuisine = str(detail.get("cuisine") or "")
            city = str(detail.get("city") or "")
            image_url = str(detail.get("image_url") or "")
            platforms = detail.get("platforms") if isinstance(detail.get("platforms"), list) else []
            platforms_str = ",".join([str(p) for p in platforms])

            items_with_diffs = detail.get("items_with_diffs") if isinstance(detail.get("items_with_diffs"), list) else []
            items_same_price = detail.get("items_same_price") if isinstance(detail.get("items_same_price"), list) else []

            w_rest.writerow(
                {
                    "restaurant_id": rest_id,
                    "name_en": name_en,
                    "name_ar": name_ar,
                    "cuisine": cuisine,
                    "city": city,
                    "image_url": image_url,
                    "platforms": platforms_str,
                    "total_items": detail.get("total_items"),
                    "total_menu_items": detail.get("total_menu_items"),
                    "match_rate": detail.get("match_rate"),
                    "items_with_diffs_count": len(items_with_diffs),
                    "items_same_price_count": len(items_same_price),
                    "max_saving": detail.get("max_saving"),
                    "total_reviews": detail.get("total_reviews"),
                    "max_rating": detail.get("max_rating"),
                }
            )

            listings = detail.get("listings") if isinstance(detail.get("listings"), list) else []
            listings_by_platform: Dict[str, dict] = {}
            for l in listings:
                if not isinstance(l, dict):
                    continue
                plat = l.get("platform")
                if isinstance(plat, str):
                    listings_by_platform[plat] = l
                w_list.writerow(
                    {
                        "restaurant_id": rest_id,
                        "platform": l.get("platform"),
                        "platform_id": l.get("platform_id"),
                        "platform_url": l.get("platform_url"),
                        "rating": l.get("rating"),
                        "review_count": l.get("review_count"),
                        "delivery_fee": l.get("delivery_fee"),
                        "is_open": l.get("is_open"),
                        "discount_pct": l.get("discount_pct"),
                        "link": l.get("link"),
                        "promotions_json": json.dumps(l.get("promotions") or [], ensure_ascii=False),
                    }
                )

            for item_group, item in _items_from_detail(detail):
                item_name_en = str(item.get("name") or "")
                item_name_ar = str(item.get("name_ar") or "")
                item_image_url = str(item.get("image_url") or "")
                min_price = _safe_float(item.get("min_price"))
                max_price = _safe_float(item.get("max_price"))
                saving = _safe_float(item.get("saving"))
                saving_pct = _safe_float(item.get("saving_pct"))

                plats = item.get("platforms") if isinstance(item.get("platforms"), list) else []
                norm_key = _norm(item_name_en) or _norm(item_name_ar) or f"id:{rest_id}:{len(plats)}"
                sum_key = (rest_id, item_group, norm_key)
                s = summaries.get(sum_key)
                if not s:
                    s = {
                        "restaurant_id": rest_id,
                        "restaurant_name_en": name_en,
                        "restaurant_name_ar": name_ar,
                        "cuisine": cuisine,
                        "item_group": item_group,
                        "item_key": norm_key,
                        "item_name_en": item_name_en,
                        "item_name_ar": item_name_ar,
                        "item_image_url": item_image_url,
                        "stores_count": 0,
                        "min_price": None,
                        "max_price": None,
                        "saving": None,
                        "saving_pct": None,
                    }
                    summaries[sum_key] = s

                # Keep best-known fields
                s["stores_count"] = max(int(s["stores_count"]), len([p for p in plats if isinstance(p, dict) and p.get("platform")]))
                if min_price is not None:
                    s["min_price"] = min_price if s["min_price"] is None else min(s["min_price"], min_price)
                if max_price is not None:
                    s["max_price"] = max_price if s["max_price"] is None else max(s["max_price"], max_price)
                if saving is not None:
                    s["saving"] = saving if s["saving"] is None else max(s["saving"], saving)
                if saving_pct is not None:
                    s["saving_pct"] = saving_pct if s["saving_pct"] is None else max(s["saving_pct"], saving_pct)

                for p in plats:
                    if not isinstance(p, dict):
                        continue
                    price_platform = p.get("platform")
                    listing = listings_by_platform.get(price_platform) if isinstance(price_platform, str) else None
                    promotions_json = ""
                    if isinstance(listing, dict):
                        promotions_json = json.dumps(listing.get("promotions") or [], ensure_ascii=False)
                    w_long.writerow(
                        {
                            "restaurant_id": rest_id,
                            "restaurant_name_en": name_en,
                            "restaurant_name_ar": name_ar,
                            "cuisine": cuisine,
                            "item_group": item_group,
                            "item_name_en": item_name_en,
                            "item_name_ar": item_name_ar,
                            "item_image_url": item_image_url,
                            "platform": p.get("platform"),
                            "price": p.get("price"),
                            "original_price": p.get("original_price"),
                            "platform_image_url": p.get("image_url"),
                            "min_price": min_price,
                            "max_price": max_price,
                            "saving": saving,
                            "saving_pct": saving_pct,
                        }
                    )

                    # Full flat row (huge but complete)
                    w_flat.writerow(
                        {
                            "restaurant_id": rest_id,
                            "restaurant_name_en": name_en,
                            "restaurant_name_ar": name_ar,
                            "cuisine": cuisine,
                            "city": city,
                            "restaurant_image_url": image_url,
                            "restaurant_platforms": platforms_str,
                            "restaurant_total_items": detail.get("total_items"),
                            "restaurant_total_menu_items": detail.get("total_menu_items"),
                            "restaurant_match_rate": detail.get("match_rate"),
                            "restaurant_max_saving": detail.get("max_saving"),
                            "restaurant_total_reviews": detail.get("total_reviews"),
                            "restaurant_max_rating": detail.get("max_rating"),
                            "listing_platform": listing.get("platform") if isinstance(listing, dict) else "",
                            "listing_platform_id": listing.get("platform_id") if isinstance(listing, dict) else "",
                            "listing_platform_url": listing.get("platform_url") if isinstance(listing, dict) else "",
                            "listing_rating": listing.get("rating") if isinstance(listing, dict) else "",
                            "listing_review_count": listing.get("review_count") if isinstance(listing, dict) else "",
                            "listing_delivery_fee": listing.get("delivery_fee") if isinstance(listing, dict) else "",
                            "listing_is_open": listing.get("is_open") if isinstance(listing, dict) else "",
                            "listing_discount_pct": listing.get("discount_pct") if isinstance(listing, dict) else "",
                            "listing_link": listing.get("link") if isinstance(listing, dict) else "",
                            "listing_promotions_json": promotions_json,
                            "item_group": item_group,
                            "item_name_en": item_name_en,
                            "item_name_ar": item_name_ar,
                            "item_image_url": item_image_url,
                            "price_platform": price_platform,
                            "price": p.get("price"),
                            "original_price": p.get("original_price"),
                            "platform_image_url": p.get("image_url"),
                            "min_price": min_price,
                            "max_price": max_price,
                            "saving": saving,
                            "saving_pct": saving_pct,
                        }
                    )

    # Write item summary CSV
    with items_summary_csv.open("w", newline="", encoding="utf-8") as f_sum:
        w_sum = csv.DictWriter(f_sum, fieldnames=items_summary_fields)
        w_sum.writeheader()
        for _, s in summaries.items():
            w_sum.writerow(s)

    print("[ok] wrote:")
    print(f"- {restaurants_csv}")
    print(f"- {listings_csv}")
    print(f"- {items_long_csv}")
    print(f"- {items_summary_csv}")
    print(f"- {full_flat_csv}")
    print(f"[stats] restaurants={len(list(summaries.keys()))} item_summaries={len(summaries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

