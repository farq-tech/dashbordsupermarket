#!/usr/bin/env python3
"""Check what fields the product API returns."""
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

def compress(value):
    if not value: return ''
    d = {}; dtc = {}; w = ''; ei = 2; ds = 3; nb = 2; dv = 0; dp = 0; out = []
    def wb(bit):
        nonlocal dv, dp
        dv = (dv << 1) | bit
        if dp == 5: dp = 0; out.append(KEY_STR[dv]); dv = 0
        else: dp += 1
    def wbs(bv, width):
        for _ in range(width): wb(bv & 1); bv >>= 1
    def wc(chunk):
        nonlocal ei, nb
        if chunk in dtc:
            cc = ord(chunk[0])
            if cc < 256: wbs(0, nb); wbs(cc, 8)
            else: wbs(1, nb); wbs(cc, 16)
            ei -= 1
            if ei == 0: ei = 2**nb; nb += 1
            del dtc[chunk]
        else: wbs(d[chunk], nb)
        ei -= 1
        if ei == 0: ei = 2**nb; nb += 1
    for char in value:
        if char not in d: d[char] = ds; ds += 1; dtc[char] = True
        wc2 = w + char
        if wc2 in d: w = wc2; continue
        wc(w); d[wc2] = ds; ds += 1; w = char
    if w: wc(w)
    wbs(2, nb)
    while True:
        dv <<= 1
        if dp == 5: out.append(KEY_STR[dv]); break
        dp += 1
    return ''.join(out)

BASE = 'https://api.fustog.app/api/v1'
HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Fustog/1.4.2.1 CFNetwork/3860.300.31 Darwin/25.2.0',
    'Content-Type': 'text/plain; charset=utf-8',
}
STORES = '{"1":20,"2":9,"3":376,"4":4,"5":1,"6":1,"7":1,"8":5,"9":3755}'
UID = 462464

payload = compress(json.dumps({'query': 'حليب', 'stores': STORES, 'uid': UID}, ensure_ascii=False, separators=(',', ':')))
r = requests.post(f'{BASE}/product/search', headers=HEADERS, data=payload, timeout=30)
text = decompress(r.text)
data = json.loads(text) if text else []
if data:
    p = data[0]
    print('Product fields:', sorted(p.keys()))
    print()
    # Print non-price fields
    for k, v in sorted(p.items()):
        if k != 'Prices':
            print(f'  {k}: {repr(v)[:100]}')
