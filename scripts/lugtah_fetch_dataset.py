#!/usr/bin/env python3
"""
Fetch Lugtah public JSON endpoints and build a local JSONL dataset.

This relies on endpoints observed in lugtah.com homepage JS:
  - /api/stats.json
  - /api/restaurants.json
  - /api/deals.json
  - /api/cheapest.json
  - /api/price-drops.json
  - /api/restaurant/{id}.json  (requires auth cookie in the real app, but may work depending on current public access)
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("LUGTAH_BASE_URL", "https://lugtah.com").rstrip("/")
OUT_DIR = Path(os.environ.get("LUGTAH_OUT_DIR", r"data\lugtah"))
UA = os.environ.get(
    "LUGTAH_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
)
WORKERS = int(os.environ.get("LUGTAH_WORKERS", "5"))
REQUEST_SLEEP_S = float(os.environ.get("LUGTAH_REQUEST_SLEEP_S", "0.0"))


def http_get_json(path: str, headers: dict[str, str] | None = None) -> object:
    url = f"{BASE_URL}{path}"
    req = Request(url, method="GET")
    req.add_header("User-Agent", UA)
    req.add_header("Accept", "application/json,*/*")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)

    with urlopen(req, timeout=30) as resp:  # nosec - user-controlled URL via env for local usage
        raw = resp.read()
        return json.loads(raw.decode("utf-8"))


def http_get_text(path: str, headers: dict[str, str] | None = None) -> str:
    url = f"{BASE_URL}{path}"
    req = Request(url, method="GET")
    req.add_header("User-Agent", UA)
    req.add_header("Accept", "text/html,*/*")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urlopen(req, timeout=30) as resp:  # nosec - user-controlled URL via env for local usage
        raw = resp.read()
        return raw.decode("utf-8", errors="replace")


def build_decrypt_key_from_homepage(html: str) -> bytes | None:
    """
    Lugtah returns encrypted JSON as {"_e":"<base64>"} for some endpoints.
    Key derivation matches the site's JS:
      keySeed = data-v + css --_v + meta build-id + comment "Build <16hex>"
      keyBytes = hex-decode(keySeed) (64 hex chars => 32 bytes)
      decrypted = base64decode(_e) XOR keyBytes (repeating)
    """
    f1 = None
    m = re.search(r'data-v="([a-f0-9]{16})"', html)
    if m:
        f1 = m.group(1)

    f2 = None
    m = re.search(r'--_v:\s*"([a-f0-9]{16})"', html)
    if m:
        f2 = m.group(1)

    f3 = None
    m = re.search(r'<meta\s+name="build-id"\s+content="([a-f0-9]{16})"\s*>', html)
    if m:
        f3 = m.group(1)

    f4 = None
    m = re.search(r"Build\s+([a-f0-9]{16})", html)
    if m:
        f4 = m.group(1)

    if not (f1 and f2 and f3 and f4):
        print(
            f"[warn] Missing key parts: data-v={bool(f1)} --_v={bool(f2)} "
            f"build-id={bool(f3)} BuildComment={bool(f4)}"
        )
        return None

    key_seed = f1 + f2 + f3 + f4
    if len(key_seed) != 64:
        print(f"[warn] key_seed length != 64: {len(key_seed)}")
        return None

    try:
        return bytes.fromhex(key_seed)
    except ValueError as e:
        print(f"[warn] invalid hex key_seed: {e}")
        return None


def decrypt_payload(obj: object, key_bytes: bytes | None) -> object:
    if not isinstance(obj, dict) or "_e" not in obj:
        return obj
    if not key_bytes:
        return obj

    enc = obj.get("_e")
    if not isinstance(enc, str):
        return obj

    try:
        data = base64.b64decode(enc)
        out = bytearray(len(data))
        for i, b in enumerate(data):
            out[i] = b ^ key_bytes[i % len(key_bytes)]
        return json.loads(out.decode("utf-8"))
    except Exception as e:
        print(f"[warn] decrypt failed: {e}")
        return obj


def extract_restaurants_list(restaurants_obj: object) -> list[dict] | None:
    if isinstance(restaurants_obj, list):
        return [r for r in restaurants_obj if isinstance(r, dict)]
    if isinstance(restaurants_obj, dict):
        for k in ("restaurants", "data", "items", "results"):
            v = restaurants_obj.get(k)
            if isinstance(v, list):
                return [r for r in v if isinstance(r, dict)]
    return None


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _fetch_restaurant_detail(
    rid: int,
    restaurant: dict,
    key_bytes: bytes | None,
) -> dict:
    path = f"/api/restaurant/{rid}.json"
    detail = http_get_json(path)
    detail = decrypt_payload(detail, key_bytes)
    if REQUEST_SLEEP_S > 0:
        time.sleep(REQUEST_SLEEP_S)
    return {
        "type": "restaurant_detail",
        "restaurant_id": rid,
        "restaurant": restaurant,
        "detail": detail,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch homepage to derive decrypt key (needed for encrypted JSON endpoints)
    key_bytes: bytes | None = None
    try:
        homepage_html = http_get_text("/")
        (OUT_DIR / "homepage.html").write_text(homepage_html, encoding="utf-8")
        key_bytes = build_decrypt_key_from_homepage(homepage_html)
        if key_bytes:
            print("[ok] decrypt key derived from homepage")
    except Exception as e:
        print(f"[warn] failed to fetch homepage for key: {e}")

    # 1) Fetch public collections
    collections: dict[str, object] = {}
    for key, api_path in [
        ("stats", "/api/stats.json"),
        ("restaurants", "/api/restaurants.json"),
        ("deals", "/api/deals.json"),
        ("cheapest", "/api/cheapest.json"),
        ("price_drops", "/api/price-drops.json"),
    ]:
        try:
            data = http_get_json(api_path)
            data = decrypt_payload(data, key_bytes)
            collections[key] = data
            write_json(OUT_DIR / f"{key}.json", data)
            print(f"[ok] {api_path} -> {OUT_DIR / f'{key}.json'}")
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"[warn] Failed {api_path}: {e}")

    restaurants_obj = collections.get("restaurants")
    restaurants = extract_restaurants_list(restaurants_obj)
    if not restaurants:
        print("[warn] restaurants.json does not contain a restaurants list; skipping per-restaurant fetch")
        return 0

    # 2) Fetch per-restaurant details (may require auth on lugtah)
    detail_rows: list[dict] = []
    failed: list[dict] = []
    details_path = OUT_DIR / "restaurant_details.jsonl"
    failures_path = OUT_DIR / "restaurant_details_failures.json"
    # Start fresh each run
    if details_path.exists():
        details_path.unlink()
    if failures_path.exists():
        failures_path.unlink()

    # Build job list
    jobs: list[tuple[int, dict]] = []
    for r in restaurants:
        rid = r.get("id") if isinstance(r, dict) else None
        if isinstance(rid, int):
            jobs.append((rid, r))

    total = len(jobs)
    print(f"[info] fetching restaurant details: total={total} workers={WORKERS}")

    write_lock = Lock()
    done = 0

    def _record_success(row: dict) -> None:
        nonlocal done
        with write_lock:
            detail_rows.append(row)
            append_jsonl(details_path, row)
            done += 1
            if done % 25 == 0 or done == total:
                print(f"[ok] fetched {done}/{total} restaurant details")

    def _record_failure(rid: int, error: Exception) -> None:
        with write_lock:
            failed.append({"restaurant_id": rid, "error": str(error)})

    with ThreadPoolExecutor(max_workers=max(1, WORKERS)) as ex:
        future_map = {
            ex.submit(_fetch_restaurant_detail, rid, r, key_bytes): rid
            for (rid, r) in jobs
        }
        for fut in as_completed(future_map):
            rid = future_map[fut]
            try:
                row = fut.result()
                _record_success(row)
            except Exception as e:
                _record_failure(rid, e)

    write_json(failures_path, failed)
    print(f"[done] details ok={len(detail_rows)} failed={len(failed)}")
    print(f"[out] {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

