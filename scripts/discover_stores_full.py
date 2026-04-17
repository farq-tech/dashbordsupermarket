#!/usr/bin/env python3
"""Discover ALL stores with full details from Fustog API across multiple locations."""
import sys, json, requests
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

KEY_STR = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
REV_DIC = {c: i for i, c in enumerate(KEY_STR)}

def decompress_from_base64(value):
    if not value: return ''
    def get_next_value(i): return REV_DIC.get(value[i], 0) if i < len(value) else 0
    return _decompress(len(value), 32, get_next_value)

def _decompress(length, reset_value, get_next_value):
    dictionary = {i: chr(i) for i in range(3)}
    enlarge_in, dict_size, num_bits = 4, 4, 3
    data_val = get_next_value(0)
    data_position, data_index = reset_value, 1
    def read_bits(max_bits):
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
    c = chr(read_bits(8)) if next_value == 0 else (chr(read_bits(16)) if next_value == 1 else '')
    if not c: return ''
    dictionary[3] = c; w = c; result = [c]
    while True:
        if data_index > length: return ''.join(result)
        cc = read_bits(num_bits)
        if cc == 0: dictionary[dict_size] = chr(read_bits(8)); cc = dict_size; dict_size += 1; enlarge_in -= 1
        elif cc == 1: dictionary[dict_size] = chr(read_bits(16)); cc = dict_size; dict_size += 1; enlarge_in -= 1
        elif cc == 2: return ''.join(result)
        if enlarge_in == 0: enlarge_in = 2**num_bits; num_bits += 1
        entry = dictionary.get(cc, w + w[0] if cc == dict_size else '')
        result.append(entry)
        dictionary[dict_size] = w + entry[0]; dict_size += 1; enlarge_in -= 1; w = entry
        if enlarge_in == 0: enlarge_in = 2**num_bits; num_bits += 1

def compress_to_base64(uncompressed):
    if not uncompressed: return ''
    return _compress(uncompressed, 6, lambda a: KEY_STR[a])

def _compress(value, bits_per_char, get_char):
    dictionary = {}; dictionary_to_create = {}; w = ''; enlarge_in = 2; dict_size = 3; num_bits = 2
    data_val = 0; data_position = 0; output = []
    def write_bit(bit):
        nonlocal data_val, data_position
        data_val = (data_val << 1) | bit
        if data_position == bits_per_char - 1:
            data_position = 0; output.append(get_char(data_val)); data_val = 0
        else: data_position += 1
    def write_bits(bv, width):
        for _ in range(width): write_bit(bv & 1); bv >>= 1
    def write_code(chunk):
        nonlocal enlarge_in, num_bits
        if chunk in dictionary_to_create:
            cc = ord(chunk[0])
            if cc < 256: write_bits(0, num_bits); write_bits(cc, 8)
            else: write_bits(1, num_bits); write_bits(cc, 16)
            enlarge_in -= 1
            if enlarge_in == 0: enlarge_in = 2**num_bits; num_bits += 1
            del dictionary_to_create[chunk]
        else: write_bits(dictionary[chunk], num_bits)
        enlarge_in -= 1
        if enlarge_in == 0: enlarge_in = 2**num_bits; num_bits += 1
    for char in value:
        if char not in dictionary: dictionary[char] = dict_size; dict_size += 1; dictionary_to_create[char] = True
        wc = w + char
        if wc in dictionary: w = wc; continue
        write_code(w); dictionary[wc] = dict_size; dict_size += 1; w = char
    if w: write_code(w)
    write_bits(2, num_bits)
    while True:
        data_val <<= 1
        if data_position == bits_per_char - 1: output.append(get_char(data_val)); break
        data_position += 1
    return ''.join(output)

def api_post(endpoint, body):
    BASE = 'https://api.fustog.app/api/v1'
    HEADERS = {
        'Accept': 'application/json',
        'User-Agent': 'Fustog/1.4.2.1 CFNetwork/3860.300.31 Darwin/25.2.0',
        'Content-Type': 'text/plain; charset=utf-8',
    }
    payload = compress_to_base64(json.dumps(body, ensure_ascii=False, separators=(',', ':')))
    r = requests.post(f'{BASE}/{endpoint}', headers=HEADERS, data=payload, timeout=30)
    if r.status_code != 200 or not r.text:
        return None
    text = decompress_from_base64(r.text)
    return json.loads(text) if text else None

uid = 462464
all_stores = {}  # RID -> {SID -> store_data}
coords = [
    ('riyadh_center', 24.690883, 46.6621698),
    ('riyadh_north', 24.810883, 46.6821698),
    ('riyadh_south', 24.570883, 46.7321698),
    ('riyadh_east', 24.700883, 46.8321698),
    ('riyadh_west', 24.700883, 46.4821698),
    ('jeddah_center', 21.543333, 39.172778),
    ('jeddah_north', 21.673333, 39.152778),
    ('dammam', 26.4207, 50.0888),
    ('mekkah', 21.3891, 39.8579),
    ('madina', 24.5247, 39.5692),
    ('khobar', 26.2172, 50.1971),
    ('taif', 21.2702, 40.4158),
]

for name, lat, lon in coords:
    data = api_post('stores/NearestStores', {'Latitude': lat, 'Longitude': lon, 'uid': uid})
    if isinstance(data, list):
        for store in data:
            rid = store.get('RID')
            sid = store.get('SID')
            if rid not in all_stores:
                all_stores[rid] = {}
            if sid not in all_stores[rid]:
                all_stores[rid][sid] = store
        print(f'  [{name}] {len(data)} stores: {[s.get("RID") for s in data]}')
    else:
        print(f'  [{name}] No data returned')

print()
print('=== ALL DISCOVERED STORES BY RID ===')
for rid in sorted(all_stores.keys()):
    stores = all_stores[rid]
    first = list(stores.values())[0]
    all_keys = list(first.keys())
    print(f'RID={rid} ({len(stores)} branches found) | all fields: {all_keys}')
    for sid, s in list(stores.items())[:4]:
        name_en = s.get('NameEn', s.get('nameEn', ''))
        name_ar = s.get('NameAr', s.get('nameAr', ''))
        # Look for brand/retailer info in all fields
        brand_fields = {k: v for k, v in s.items() if 'brand' in k.lower() or 'retailer' in k.lower() or 'chain' in k.lower()}
        print(f'  SID={sid} | EN={name_en} | AR={name_ar} | brand_fields={brand_fields}')

# Save
import os
os.makedirs('data', exist_ok=True)
with open('data/all_stores_discovery.json', 'w', encoding='utf-8') as f:
    json.dump({str(k): {str(sk): sv for sk, sv in v.items()} for k, v in all_stores.items()}, f, ensure_ascii=False, indent=2)
print()
print('Saved full data to data/all_stores_discovery.json')
print()

# Summary table for platform use
print('=== SUMMARY FOR PLATFORM ===')
for rid in sorted(all_stores.keys()):
    stores = all_stores[rid]
    sample_names_en = [s.get('NameEn','') for s in list(stores.values())[:5]]
    sample_names_ar = [s.get('NameAr','') for s in list(stores.values())[:5]]
    sids = list(stores.keys())[:5]
    print(f'RID={rid} | SIDs={sids} | EN names: {sample_names_en[:3]}')
