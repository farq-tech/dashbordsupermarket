#!/usr/bin/env python3
"""Decode the payload and call ItemsPrices endpoint."""
import sys, json, requests
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

KEY_STR = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
REV_DIC = {c: i for i, c in enumerate(KEY_STR)}

def decompress(value):
    if not value: return ''
    def gnv(i): return REV_DIC.get(value[i], 0) if i < len(value) else 0
    d = {i: chr(i) for i in range(3)}; ei, ds, nb = 4, 4, 3
    dv = gnv(0); dp, di = 32, 1
    def rb(mb):
        nonlocal dv, dp, di
        bits, p, mp = 0, 1, 2**mb
        while p != mp:
            r = dv & dp; dp >>= 1
            if dp == 0: dp = 32; dv = gnv(di); di += 1
            bits |= (1 if r > 0 else 0) * p; p <<= 1
        return bits
    nv = rb(2)
    c = chr(rb(8)) if nv == 0 else (chr(rb(16)) if nv == 1 else '')
    if not c: return ''
    d[3] = c; w = c; res = [c]
    while True:
        if di > len(value): return ''.join(res)
        cc = rb(nb)
        if cc == 0: d[ds] = chr(rb(8)); cc = ds; ds += 1; ei -= 1
        elif cc == 1: d[ds] = chr(rb(16)); cc = ds; ds += 1; ei -= 1
        elif cc == 2: return ''.join(res)
        if ei == 0: ei = 2**nb; nb += 1
        e = d.get(cc, w + w[0] if cc == ds else '')
        res.append(e); d[ds] = w + e[0]; ds += 1; ei -= 1; w = e
        if ei == 0: ei = 2**nb; nb += 1

# The payload from the curl command
PAYLOAD = 'N4IgZglgJgziBcBtATARgAwBo0HZsGZVsBWANm1OUwBYBOc1ADmq2VNT0Mcc32WqoscWFrWI1uPYulJ5iqfHL5ycjOYzSZ2xHpWT4tpWjgC6mEDAAuAewBOAUzjwQwADohU7+PgPvkX0nxyd3wvcXdqLzx3Yi8id1I4gF8QcwBXaARqSmzqJKA=='

# 1. Decode what's being sent
decoded = decompress(PAYLOAD)
print('=== DECODED PAYLOAD ===')
print(decoded)
try:
    payload_data = json.loads(decoded)
    print()
    print('=== PARSED JSON ===')
    print(json.dumps(payload_data, ensure_ascii=False, indent=2))
except Exception as e:
    print(f'Could not parse as JSON: {e}')

# 2. Call the endpoint with the same payload
print()
print('=== CALLING ItemsPrices ===')
HEADERS = {
    'Host': 'api.fustog.app',
    'Connection': 'keep-alive',
    'Accept': 'application/json',
    'User-Agent': 'Fustog/1.4.2.1 CFNetwork/3860.300.31 Darwin/25.2.0',
    'Accept-Language': 'en-US,en;q=0.9',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Content-Type': 'text/plain; charset=utf-8',
}

try:
    r = requests.post(
        'https://api.fustog.app/api/v1/product/ItemsPrices',
        headers=HEADERS,
        data=PAYLOAD,
        timeout=30,
    )
    print(f'Status: {r.status_code}')
    print(f'Response size: {len(r.content)} bytes')
    if r.status_code == 200 and r.text:
        text = decompress(r.text)
        if text:
            try:
                data = json.loads(text)
                print(f'Response type: {type(data).__name__}')
                if isinstance(data, list):
                    print(f'Items count: {len(data)}')
                    if data:
                        first = data[0]
                        print(f'First item keys: {list(first.keys()) if isinstance(first, dict) else type(first).__name__}')
                        print()
                        print('=== FIRST 3 ITEMS ===')
                        for item in data[:3]:
                            print(json.dumps(item, ensure_ascii=False))
                        print()
                        print('=== ANALYZING PRICES STRUCTURE ===')
                        # Check if items have Prices with store keys
                        for item in data[:5]:
                            if isinstance(item, dict):
                                prices = item.get('Prices', {})
                                if isinstance(prices, dict):
                                    print(f'FID={item.get("FID")} TitleAr={item.get("TitleAr","")[:30]} | Prices keys={list(prices.keys())}')
                elif isinstance(data, dict):
                    print(f'Dict keys: {list(data.keys())}')
                    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
            except Exception as e:
                print(f'JSON parse error: {e}')
                print(f'Raw text (first 500): {text[:500]}')
        else:
            print(f'Empty response after decompress')
            print(f'Raw (first 200): {r.content[:200]}')
    else:
        print(f'Error: {r.content[:500]}')
except Exception as e:
    print(f'Request error: {e}')
