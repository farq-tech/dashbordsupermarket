#!/usr/bin/env python3
"""Send OTP to phone for Farm and Lulu authentication"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os
import httpx

PHONE = "0563333463"
PHONE_INTL = "+966563333463"
PHONE_NO_ZERO = "563333463"

client = httpx.Client(timeout=20.0, follow_redirects=True)

# ============================================================
# 1. FARM - Send OTP
# ============================================================
print("=" * 60)
print("1. FARM - OTP Login")
print("=" * 60)

farm_h = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "FarmStores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
    "accept-language": "ar",
}

# Try different mobile field formats
farm_bodies = [
    {"mobile": PHONE_NO_ZERO, "mobile_intro": "+966"},
    {"mobile": PHONE, "mobile_intro": "+966"},
    {"mobile": PHONE_INTL},
    {"mobile": PHONE_NO_ZERO, "mobile_intro": "966"},
    {"mobile": PHONE, "mobile_intro": "966"},
    {"phone": PHONE_INTL},
    {"phone": PHONE_NO_ZERO, "country_code": "+966"},
]

farm_endpoints = [
    "/public/api/v1.0/user/login",
    "/public/api/v1.0/user/otp",
    "/public/api/v1.0/user/send-otp",
    "/public/api/v1.0/user/register",
    "/public/api/v1.0/auth/otp",
    "/public/api/v1.0/auth/send-otp",
]

for ep in farm_endpoints:
    for body in farm_bodies:
        try:
            r = client.post(f"https://go.farm.com.sa{ep}", json=body, headers=farm_h, timeout=10)
            if len(r.content) > 10:
                try:
                    d = r.json()
                    msg = d.get("message", d.get("status", {}).get("otherTxt", "")) if isinstance(d, dict) else ""
                    if isinstance(d.get("status"), dict):
                        msg = d["status"].get("otherTxt", "")
                    # Skip "route not found" errors
                    if "route" in str(msg).lower() and "not found" in str(msg).lower():
                        continue
                    print(f"  [{r.status_code}] POST {ep}")
                    print(f"    Body: {body}")
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:300]}")
                    # If success, break
                    if r.status_code == 200 and (d.get("status", {}).get("success", False) if isinstance(d.get("status"), dict) else d.get("success", False)):
                        print("  >>> OTP SENT! Check your phone <<<")
                        break
                except:
                    pass
        except:
            pass

# ============================================================
# 2. LULU - Send OTP
# ============================================================
print("\n" + "=" * 60)
print("2. LULU - OTP Login")
print("=" * 60)

lulu_h = {
    "Accept": "application/json",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
}

LULU = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"

# Try JSON body
lulu_bodies_json = [
    {"phone": PHONE_INTL},
    {"phone": PHONE},
    {"phone": PHONE_NO_ZERO, "country_code": "+966"},
    {"mobile": PHONE_INTL},
    {"phone_number": PHONE_INTL},
]

lulu_endpoints = [
    "/users/otp-login/",
    "/users/send-otp/",
    "/users/otp/",
    "/auth/otp/",
]

for ep in lulu_endpoints:
    for body in lulu_bodies_json:
        try:
            # Try JSON
            r = client.post(f"{LULU}{ep}", json=body, headers={**lulu_h, "Content-Type": "application/json"}, timeout=10)
            if r.status_code not in (404, 405) and len(r.content) > 10:
                try:
                    d = r.json()
                    print(f"  [{r.status_code}] POST {ep} (JSON)")
                    print(f"    Body: {body}")
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:300]}")
                    if r.status_code in (200, 201):
                        print("  >>> OTP SENT! Check your phone <<<")
                        break
                except:
                    pass
        except:
            pass

    # Try form-urlencoded
    for body in lulu_bodies_json:
        try:
            form_data = "&".join(f"{k}={v}" for k, v in body.items())
            r = client.post(f"{LULU}{ep}", content=form_data,
                headers={**lulu_h, "Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
            if r.status_code not in (404, 405) and len(r.content) > 10:
                try:
                    d = r.json()
                    print(f"  [{r.status_code}] POST {ep} (form)")
                    print(f"    Body: {form_data}")
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:300]}")
                    if r.status_code in (200, 201):
                        print("  >>> OTP SENT! Check your phone <<<")
                        break
                except:
                    pass
        except:
            pass

# ============================================================
# 3. RAMEZ - Try OTP
# ============================================================
print("\n" + "=" * 60)
print("3. RAMEZ - OTP Login")
print("=" * 60)

ramez_h = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "apikey": "^~>h2q=m[h=>3?bU/!M'X!m~?4GjKJP{Q@y;~fa3Vjs/M#`8FuB;x[LKwJ&>gNrxBt8!5PZ:9QLuHBUtu{TPc2s]k74]Br?PGe6+NcFUT-8",
    "User-Agent": "Ramez/8 CFNetwork/1404.0.5 Darwin/22.3.0",
    "accept-language": "ar",
    "device_type": "iOS",
    "app_version": "5.9.4",
}

ramez_bodies = [
    {"mobile": PHONE_INTL},
    {"mobile": PHONE},
    {"phone": PHONE_INTL},
    {"mobile": PHONE_NO_ZERO, "country_code": "+966"},
]

ramez_endpoints = [
    "https://risteh.com/SA/GroceryStoreApi/api/v9/Account/login",
    "https://risteh.com/SA/GroceryStoreApi/api/v9/Account/sendotp",
    "https://risteh.com/SA/GroceryStoreApi/api/v9/Account/register",
]

for url in ramez_endpoints:
    for body in ramez_bodies:
        try:
            r = client.post(url, json=body, headers=ramez_h, timeout=10)
            if r.status_code != 404 and len(r.content) > 10:
                try:
                    d = r.json()
                    print(f"  [{r.status_code}] POST {url.split('v9/')[1]}")
                    print(f"    Body: {body}")
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:300]}")
                    if r.status_code == 200:
                        print("  >>> OTP SENT! <<<")
                        break
                except:
                    pass
        except Exception as e:
            err = type(e).__name__
            if "connect" in err.lower() or "timeout" in err.lower():
                print(f"  [TIMEOUT] Ramez server unreachable")
                break

# ============================================================
# 4. SADHAN - Try OTP
# ============================================================
print("\n" + "=" * 60)
print("4. SADHAN - OTP Login")
print("=" * 60)

sadhan_h = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Alsadhan%20Stores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
    "Referer": "https://alsadhan.witheldokan.com/",
}

sadhan_bodies = [
    {"phone": PHONE_INTL},
    {"mobile": PHONE_INTL},
    {"phone": PHONE, "country_code": "+966"},
]

sadhan_endpoints = [
    "https://masterapi.witheldokan.com/api/customer/auth",
    "https://masterapi.witheldokan.com/api/customer/login",
    "https://masterapi.witheldokan.com/api/customer/otp",
    "https://masterapi.witheldokan.com/api/auth",
]

for url in sadhan_endpoints:
    for body in sadhan_bodies:
        try:
            r = client.post(url, json=body, headers=sadhan_h, timeout=10)
            if len(r.content) > 10:
                try:
                    d = r.json()
                    msg = d.get("message", "")
                    if "Store Not Found" in msg or "Referer" in msg:
                        continue
                    print(f"  [{r.status_code}] POST {url.split('.com')[1]}")
                    print(f"    Body: {body}")
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:300]}")
                    if r.status_code in (200, 201):
                        print("  >>> OTP SENT! <<<")
                        break
                except:
                    pass
        except Exception as e:
            err = type(e).__name__
            if "timeout" in err.lower():
                print(f"  [TIMEOUT] Sadhan unreachable")
                break

client.close()
print("\n=== DONE ===")
print("\nIf OTP was sent, reply with the code and I'll complete the login.")
