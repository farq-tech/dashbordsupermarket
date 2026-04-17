#!/usr/bin/env python3
"""Lulu: Send OTP and try to get auth token"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os
import httpx

os.makedirs("data", exist_ok=True)

PHONE = "+966563333463"
PHONE_NO_PLUS = "966563333463"

client = httpx.Client(timeout=20.0, follow_redirects=True)

LULU = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"

h_json = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "accept-language": "ar;q=1.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
}

h_form = {
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "accept-language": "ar;q=1.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
}

# ============================================================
# 1. Send OTP to Lulu
# ============================================================
print("=" * 60)
print("LULU - Send OTP")
print("=" * 60)

# The retailer settings show: OTPURL = VerifyURL = /users/otp-login/
# This is likely both the send and verify endpoint

# Try sending OTP with form-urlencoded (as per retailer config MediaType)
bodies_form = [
    f"phone={PHONE}",
    f"phone={PHONE_NO_PLUS}",
    f"phone_number={PHONE}",
    f"mobile={PHONE}",
]

bodies_json = [
    {"phone": PHONE},
    {"phone": PHONE_NO_PLUS},
    {"phone_number": PHONE},
    {"mobile": PHONE},
    {"phone": PHONE, "sms_code": ""},
    {"phone": PHONE, "channel": "sms"},
]

endpoints = [
    "/users/otp-login/",
    "/users/send-otp/",
    "/users/otp/send/",
    "/users/phone-login/",
    "/users/login/",
    "/auth/otp/",
    "/auth/send-otp/",
]

print("\n  Form-urlencoded requests:")
for ep in endpoints:
    for body in bodies_form:
        try:
            r = client.post(f"{LULU}{ep}", content=body, headers=h_form, timeout=10)
            if r.status_code not in (404, 405) and len(r.content) > 5:
                try:
                    d = r.json()
                    text = json.dumps(d, ensure_ascii=False)[:400]
                    if "not found" not in text.lower():
                        print(f"  [{r.status_code}] POST {ep} body={body}")
                        print(f"    => {text}")
                        if r.status_code in (200, 201):
                            with open("data/lulu_otp_response.json", "w", encoding="utf-8") as f:
                                json.dump(d, f, ensure_ascii=False, indent=2)
                except:
                    if r.status_code == 200:
                        print(f"  [{r.status_code}] POST {ep}: non-JSON {r.text[:100]}")
        except:
            pass

print("\n  JSON requests:")
for ep in endpoints:
    for body in bodies_json:
        try:
            r = client.post(f"{LULU}{ep}", json=body, headers=h_json, timeout=10)
            if r.status_code not in (404, 405) and len(r.content) > 5:
                try:
                    d = r.json()
                    text = json.dumps(d, ensure_ascii=False)[:400]
                    if "not found" not in text.lower():
                        print(f"  [{r.status_code}] POST {ep} json={body}")
                        print(f"    => {text}")
                        if r.status_code in (200, 201):
                            with open("data/lulu_otp_response.json", "w", encoding="utf-8") as f:
                                json.dump(d, f, ensure_ascii=False, indent=2)
                except:
                    if r.status_code == 200:
                        print(f"  [{r.status_code}] POST {ep}: non-JSON {r.text[:100]}")
        except:
            pass

# ============================================================
# 2. Also try anonymous access to Lulu product endpoints
# ============================================================
print("\n" + "=" * 60)
print("LULU - Anonymous product access")
print("=" * 60)

anon_h = {
    "Accept": "application/json",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
}

anon_endpoints = [
    "/products/",
    "/products/?limit=10",
    "/categories/",
    "/categories/tree/",
    "/search/?q=milk",
    "/search/products/?q=milk",
    "/widgets/",
    "/widgets/home/",
    "/data-sources/",
    "/stores/",
    "/config/",
    "/settings/",
    "/channels/",
    "/baskets/",
    "/orders/",
    "/pages/",
    "/content/",
    "/catalogue/products/",
    "/catalogue/categories/",
    "/catalog/products/",
    "/catalog/categories/",
    "/v1/products/",
    "/v2/products/",
    "/api/products/",
    "/product/list/",
    "/product/search/?q=milk",
    "/flat-pages/",
]

for ep in anon_endpoints:
    try:
        r = client.get(f"{LULU}{ep}", headers=anon_h, timeout=10)
        if r.status_code not in (404, 405, 403) and len(r.content) > 50:
            try:
                d = r.json()
                text = json.dumps(d, ensure_ascii=False)[:300]
                if "not found" not in text.lower():
                    print(f"  [{r.status_code}] GET {ep}: {text[:200]}")

                    # If we got product data, save it
                    if isinstance(d, dict) and any(k in d for k in ["results", "products", "data", "items"]):
                        with open(f"data/lulu_anon_{ep.strip('/').replace('/','_')[:30]}.json", "w", encoding="utf-8") as f:
                            json.dump(d, f, ensure_ascii=False, indent=2)
                        print(f"    >>> Saved!")
                    elif isinstance(d, list) and len(d) > 0:
                        with open(f"data/lulu_anon_{ep.strip('/').replace('/','_')[:30]}.json", "w", encoding="utf-8") as f:
                            json.dump(d, f, ensure_ascii=False, indent=2)
                        print(f"    >>> Saved! Array[{len(d)}]")
            except:
                pass
        elif r.status_code == 200 and len(r.content) > 10:
            print(f"  [{r.status_code}] GET {ep}: {r.text[:100]}")
    except:
        pass

client.close()
print("\n=== DONE ===")
