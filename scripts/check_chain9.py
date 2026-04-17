import csv
ts = "2026_04_16_135330"

with open(f'data/fustog_prices_enriched_long_{ts}.csv', encoding='utf-8') as f:
    rows_7 = [r for r in csv.DictReader(f) if r['StoreKey'] == '7']
    
print(f'Chain-9 (StoreKey=7): {len(rows_7)} price rows')
print(f'Sample store_name_en: {rows_7[0].get("store_name_en","") if rows_7 else "N/A"}')
print(f'Sample store_name_ar: {rows_7[0].get("store_name_ar","") if rows_7 else "N/A"}')
print(f'RID: {rows_7[0].get("rid","") if rows_7 else "N/A"}')

print('\nSample products in Chain-9:')
for r in rows_7[:15]:
    print(f'  FID={r["FID"]} | {r["TitleAr"]} | Price={r["Price"]}')
