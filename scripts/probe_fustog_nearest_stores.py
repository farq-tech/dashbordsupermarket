#!/usr/bin/env python3
"""
Probe Fustog `stores/NearestStores` for multiple coordinates, to discover
retailer brand names that may appear in store/branch labels.

This uses the same LZ-String base64 payload/response as other Fustog scripts.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import requests


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://api.fustog.app/api/v1"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Fustog/1.4.2.1 CFNetwork/3860.300.31 Darwin/25.2.0",
    "Content-Type": "text/plain; charset=utf-8",
}

KEY_STR = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
REV_DIC = {c: i for i, c in enumerate(KEY_STR)}


def decompress_from_base64(value: str) -> str:
    if not value:
        return ""

    def get_next_value(i: int) -> int:
        if i >= len(value):
            return 0
        return REV_DIC.get(value[i], 0)

    return _decompress(len(value), 32, get_next_value)


def _decompress(length: int, reset_value: int, get_next_value: Callable[[int], int]) -> str:
    dictionary: Dict[int, str] = {i: chr(i) for i in range(3)}
    enlarge_in = 4
    dict_size = 4
    num_bits = 3

    data_val = get_next_value(0)
    data_position = reset_value
    data_index = 1

    def read_bits(max_bits: int) -> int:
        nonlocal data_val, data_position, data_index
        bits = 0
        power = 1
        max_power = 2**max_bits
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
    result = [c]

    while True:
        if data_index > length:
            return "".join(result)

        cc = read_bits(num_bits)
        if cc == 0:
            dictionary[dict_size] = chr(read_bits(8))
            cc = dict_size
            dict_size += 1
            enlarge_in -= 1
        elif cc == 1:
            dictionary[dict_size] = chr(read_bits(16))
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
            return "".join(result)

        result.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        enlarge_in -= 1
        w = entry

        if enlarge_in == 0:
            enlarge_in = 2**num_bits
            num_bits += 1


def compress_to_base64(uncompressed: str) -> str:
    if not uncompressed:
        return ""
    return _compress(uncompressed, 6, lambda a: KEY_STR[a])


def _compress(value: str, bits_per_char: int, get_char: Callable[[int], str]) -> str:
    dictionary: Dict[str, int] = {}
    dictionary_to_create: Dict[str, bool] = {}
    w = ""
    enlarge_in = 2
    dict_size = 3
    num_bits = 2
    data_val = 0
    data_position = 0
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

    for ch in value:
        if ch not in dictionary:
            dictionary[ch] = dict_size
            dict_size += 1
            dictionary_to_create[ch] = True

        wc = w + ch
        if wc in dictionary:
            w = wc
        else:
            write_code(w)
            dictionary[wc] = dict_size
            dict_size += 1
            w = ch

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


def api_post(endpoint: str, body: Dict[str, Any]) -> Tuple[Optional[Any], int]:
    payload = compress_to_base64(json.dumps(body, ensure_ascii=False, separators=(",", ":")))
    r = requests.post(f"{BASE}/{endpoint}", headers=HEADERS, data=payload, timeout=30)
    if r.status_code != 200 or not r.text:
        return None, r.status_code
    text = decompress_from_base64(r.text)
    return (json.loads(text) if text else None), r.status_code


def main() -> int:
    uid = 462464
    coords = [
        ("riyadh", 24.790883230664154, 46.6621698799985),
        ("jeddah", 21.543333, 39.172778),
        ("dammam", 26.4207, 50.0888),
        ("mekkah", 21.3891, 39.8579),
        ("madina", 24.5247, 39.5692),
    ]

    rid_names_ar: Dict[int, Set[str]] = defaultdict(set)
    rid_names_en: Dict[int, Set[str]] = defaultdict(set)

    for name, lat, lon in coords:
        data, code = api_post("stores/NearestStores", {"Latitude": lat, "Longitude": lon, "uid": uid})
        if not isinstance(data, list):
            print(f"[{name}] status={code} data={type(data).__name__}")
            continue
        print(f"[{name}] status={code} stores={len(data)}")
        for e in data:
            try:
                rid = int(e.get("RID"))
            except Exception:
                continue
            rid_names_ar[rid].add(str(e.get("NameAr") or "").strip())
            rid_names_en[rid].add(str(e.get("NameEn") or "").strip())

    print("\n=== RID Name Samples ===")
    for rid in sorted(rid_names_ar.keys()):
        ar = [x for x in rid_names_ar[rid] if x][:4]
        en = [x for x in rid_names_en[rid] if x][:4]
        print(f"RID={rid} ar={ar} en={en}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

