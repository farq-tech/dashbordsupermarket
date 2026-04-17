#!/usr/bin/env python3
"""Query Fustog API properly with LZ-String compression (POST method)"""

import requests
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── LZ-String Base64 ───
keyStr = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
revDic = {c: i for i, c in enumerate(keyStr)}

def decompressFromBase64(s):
    if not s: return ''
    return _decompress(len(s), 32, lambda i: revDic.get(s[i], 0) if i < len(s) else 0)

def _decompress(length, resetValue, getNextValue):
    dictionary = {i: i for i in range(3)}
    enlargeIn, dictSize, numBits = 4, 4, 3
    result, w = [], ''
    data_val, data_position, data_index = getNextValue(0), resetValue, 1

    def readBits(maxBits):
        nonlocal data_val, data_position, data_index
        bits, power, maxpower = 0, 1, 2**maxBits
        while power != maxpower:
            resb = data_val & data_position
            data_position >>= 1
            if data_position == 0:
                data_position = resetValue
                data_val = getNextValue(data_index)
                data_index += 1
            bits |= (1 if resb > 0 else 0) * power
            power <<= 1
        return bits

    nv = readBits(2)
    if nv == 0: c = chr(readBits(8))
    elif nv == 1: c = chr(readBits(16))
    elif nv == 2: return ''
    dictionary[3] = c; w = c; result.append(c)

    while data_index <= length:
        cv = readBits(numBits)
        if cv == 0:
            dictionary[dictSize] = chr(readBits(8)); dictSize += 1; cv = dictSize - 1; enlargeIn -= 1
        elif cv == 1:
            dictionary[dictSize] = chr(readBits(16)); dictSize += 1; cv = dictSize - 1; enlargeIn -= 1
        elif cv == 2:
            return ''.join(result)
        if enlargeIn == 0: enlargeIn = 2**numBits; numBits += 1
        entry = dictionary.get(cv, w + w[0] if cv == dictSize else None)
        if entry is None: return ''.join(result)
        result.append(entry)
        dictionary[dictSize] = w + entry[0]; dictSize += 1; enlargeIn -= 1
        if enlargeIn == 0: enlargeIn = 2**numBits; numBits += 1
        w = entry
    return ''.join(result)

def compressToBase64(uncompressed):
    if not uncompressed: return ''
    return _compress(uncompressed, 6, lambda a: keyStr[a])

def _compress(u, bpc, getChar):
    d, dc = {}, {}
    w, ei, ds, nb = '', 2, 3, 2
    dv, dp = 0, 0
    out = []

    def writeBit(value):
        nonlocal dv, dp
        dv = (dv << 1) | value
        if dp == bpc - 1:
            dp = 0; out.append(getChar(dv)); dv = 0
        else:
            dp += 1

    def writeBits(value, numBits):
        for _ in range(numBits):
            writeBit(value & 1); value >>= 1

    def writeCode(w_str):
        nonlocal ei, nb
        if w_str in dc:
            ch = ord(w_str[0])
            if ch < 256:
                writeBits(0, nb); writeBits(ch, 8)
            else:
                writeBits(1, nb); writeBits(ch, 16)
            ei -= 1
            if ei == 0: ei = 2**nb; nb += 1
            del dc[w_str]
        else:
            writeBits(d[w_str], nb)
        ei -= 1
        if ei == 0: ei = 2**nb; nb += 1

    for c in u:
        if c not in d:
            d[c] = ds; ds += 1; dc[c] = True
        wc = w + c
        if wc in d:
            w = wc
        else:
            writeCode(w)
            d[wc] = ds; ds += 1
            w = c

    if w: writeCode(w)
    writeBits(2, nb)
    while True:
        dv = dv << 1
        if dp == bpc - 1:
            out.append(getChar(dv)); break
        else:
            dp += 1
    return ''.join(out)


# ─── Fustog API ───
BASE = 'https://api.fustog.app/api/v1'
HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Fustog/1.4.2.1 CFNetwork/3860.300.31 Darwin/25.2.0',
    'Content-Type': 'text/plain; charset=utf-8',
}

STORES = '{"1":20,"2":9,"3":64,"4":4,"5":1,"6":1}'
UID = 462464

def api_post(endpoint, body_dict):
    body_json = json.dumps(body_dict, ensure_ascii=False)
    compressed = compressToBase64(body_json)
    r = requests.post(f'{BASE}/{endpoint}', headers=HEADERS, data=compressed, timeout=20)
    if r.status_code != 200:
        return None
    return decompressFromBase64(r.text)

def api_get(endpoint):
    r = requests.get(f'{BASE}/{endpoint}', headers=HEADERS, timeout=20)
    if r.status_code != 200:
        return None
    return decompressFromBase64(r.text)


print("=" * 60)
print("FUSTOG API - Direct Query (POST + LZ-String)")
print("=" * 60)

# 1. Search for Afia corn oil
print("\n[1] Search: عافية ذرة (Afia Corn Oil)")
raw = api_post("product/search", {"query": "عافية ذرة", "stores": STORES, "uid": UID})
if raw:
    data = json.loads(raw)
    print(f"  Results: {len(data)}")
    for p in data:
        print(f"\n  FID:{p['FID']} {p['TitleAr']} ({p['BrandAR']})")
        print(f"    EN: {p.get('TitleEn','')}")
        print(f"    Size: {p.get('AttrVal','')} {p.get('AttrUnit','')}")
        prices = p.get('Prices', {})
        for sid, price in sorted(prices.items()):
            if price > 0:
                print(f"    Store {sid}: {price} SAR")

# 2. Abu Kas Rice
print("\n" + "=" * 60)
print("[2] Search: ابو كاس (Abu Kas Rice)")
raw = api_post("product/search", {"query": "ابو كاس", "stores": STORES, "uid": UID})
if raw:
    data = json.loads(raw)
    print(f"  Results: {len(data)}")
    for p in data[:5]:
        print(f"\n  FID:{p['FID']} {p['TitleAr']} ({p['BrandAR']})")
        prices = p.get('Prices', {})
        for sid, price in sorted(prices.items()):
            if price > 0:
                print(f"    Store {sid}: {price} SAR")

# 3. Nearest Stores
print("\n" + "=" * 60)
print("[3] Nearest Stores (Riyadh)")
raw = api_post("stores/NearestStores", {
    "Latitude": 24.790883230664154,
    "Longitude": 46.6621698799985,
    "uid": UID
})
if raw:
    stores = json.loads(raw)
    print(f"  Stores: {len(stores)}")
    for s in stores:
        print(f"  RID:{s['RID']} SID:{s['SID']} {s.get('NameAr','')} / {s.get('NameEn','')} (Integration: {s.get('IsIntegrationReady',False)})")

# 4. Build product database from Fustog
print("\n" + "=" * 60)
print("[4] Building Fustog product database...")

terms = [
    "حليب", "زيت", "رز", "سكر", "دجاج", "لحم", "خبز", "جبن", "ماء", "عصير",
    "شاي", "قهوة", "معكرونة", "طحين", "بيض", "زبدة", "تونة", "صلصة", "بسكويت",
    "شيبس", "شوكولاتة", "مكسرات", "عسل", "مربى", "كاتشب", "مايونيز", "فول",
    "طماطم", "خل", "ملح", "فلفل", "كمون", "كريمة", "زبادي", "آيس كريم",
    "عافية", "المراعي", "نادك", "السعودية", "ربيع", "كيلوقز", "نستله",
    "تايد", "فيري", "داوني", "كلوركس", "ديتول", "بامبرز", "مناديل",
    "صابون", "شامبو", "معجون", "فرشاة", "غسول", "كريم",
]

all_fustog = []
seen_fids = set()
for term in terms:
    raw = api_post("product/search", {"query": term, "stores": STORES, "uid": UID})
    if raw:
        try:
            items = json.loads(raw)
            new = 0
            for item in items:
                fid = item.get('FID')
                if fid and fid not in seen_fids:
                    seen_fids.add(fid)
                    all_fustog.append(item)
                    new += 1
            print(f"  '{term}': {len(items)} results, {new} new (total: {len(all_fustog)})")
        except:
            pass

# Save
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
out_path = os.path.join(data_dir, 'fustog_products.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'total': len(all_fustog),
            'source': 'api.fustog.app',
            'method': 'POST + LZ-String',
            'stores': STORES,
        },
        'products': all_fustog
    }, f, ensure_ascii=False, indent=2)
print(f"\nSaved {len(all_fustog)} Fustog products to {out_path}")

print("\n" + "=" * 60)
print("DONE!")
