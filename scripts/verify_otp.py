#!/usr/bin/env python3
"""Verify OTP code 4953 with all store APIs"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json, os
import httpx

OTP = "4953"
PHONE = "0563333463"
PHONE_INTL = "+966563333463"
PHONE_NO_ZERO = "563333463"

client = httpx.Client(timeout=20.0, follow_redirects=True)

def save(name, data):
    os.makedirs("data", exist_ok=True)
    with open(f"data/{name}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 1. FARM - Verify OTP
# ============================================================
print("=" * 60)
print("1. FARM - Verify OTP")
print("=" * 60)

farm_h = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "FarmStores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
    "accept-language": "ar",
}

farm_verify_bodies = [
    {"mobile": PHONE_NO_ZERO, "mobile_intro": "+966", "otp": OTP},
    {"mobile": PHONE_NO_ZERO, "mobile_intro": "+966", "code": OTP},
    {"mobile": PHONE_NO_ZERO, "mobile_intro": "+966", "verification_code": OTP},
    {"mobile": PHONE, "mobile_intro": "+966", "otp": OTP},
    {"phone": PHONE_INTL, "otp": OTP},
    {"mobile": PHONE_INTL, "otp": OTP},
    {"mobile": PHONE_NO_ZERO, "mobile_intro": "966", "otp": OTP},
]

farm_verify_endpoints = [
    "/public/api/v1.0/user/login",
    "/public/api/v1.0/user/verify",
    "/public/api/v1.0/user/verify-otp",
    "/public/api/v1.0/user/otp/verify",
    "/public/api/v1.0/auth/verify",
]

for ep in farm_verify_endpoints:
    for body in farm_verify_bodies:
        try:
            r = client.post(f"https://go.farm.com.sa{ep}", json=body, headers=farm_h, timeout=10)
            if len(r.content) > 10:
                try:
                    d = r.json()
                    msg = str(d)
                    if "route" in msg.lower() and "not found" in msg.lower():
                        continue
                    print(f"  [{r.status_code}] POST {ep}")
                    print(f"    Body: {body}")
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:400]}")

                    # Check for token
                    if isinstance(d, dict):
                        for tk in ["token", "access_token", "api_token", "bearer", "data"]:
                            if tk in d:
                                val = d[tk]
                                if isinstance(val, str) and len(val) > 10:
                                    print(f"    >>> TOKEN: {val[:60]}... <<<")
                                    save("farm_token.json", d)
                                elif isinstance(val, dict):
                                    for tk2 in ["token", "access_token"]:
                                        if tk2 in val:
                                            print(f"    >>> TOKEN: {val[tk2][:60]}... <<<")
                                            save("farm_token.json", d)
                        if d.get("status", {}).get("success", False) if isinstance(d.get("status"), dict) else d.get("success", False):
                            print("    >>> SUCCESS <<<")
                            save("farm_auth.json", d)
                except:
                    pass
        except:
            pass

# ============================================================
# 2. LULU - Verify OTP
# ============================================================
print("\n" + "=" * 60)
print("2. LULU - Verify OTP")
print("=" * 60)

lulu_h = {
    "Accept": "application/json",
    "User-Agent": "luluakinon/1 CFNetwork/3826.500.131 Darwin/24.5.0",
    "x-app-type": "akinon-mobile",
    "x-project-name": "rn-env",
}

LULU = "https://5082fcfb6f824fd085925566005cee41.lb.akinoncloud.com"

lulu_verify_bodies = [
    {"phone": PHONE_INTL, "otp": OTP},
    {"phone": PHONE_INTL, "code": OTP},
    {"phone": PHONE_INTL, "password": OTP},
    {"phone": PHONE, "otp": OTP},
    {"phone_number": PHONE_INTL, "otp": OTP},
    {"mobile": PHONE_INTL, "otp": OTP},
]

lulu_verify_endpoints = [
    "/users/otp-login/",
    "/users/verify-otp/",
    "/users/otp/verify/",
    "/auth/verify/",
]

for ep in lulu_verify_endpoints:
    for body in lulu_verify_bodies:
        # JSON
        try:
            r = client.post(f"{LULU}{ep}", json=body,
                headers={**lulu_h, "Content-Type": "application/json"}, timeout=10)
            if r.status_code not in (404, 405) and len(r.content) > 10:
                try:
                    d = r.json()
                    print(f"  [{r.status_code}] POST {ep} (JSON)")
                    print(f"    Body: {body}")
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:400]}")
                    if isinstance(d, dict):
                        for tk in ["token", "access_token", "key", "auth_token", "Token"]:
                            if tk in d:
                                print(f"    >>> TOKEN: {d[tk][:60] if isinstance(d[tk], str) else d[tk]}... <<<")
                                save("lulu_token.json", d)
                except:
                    pass
        except:
            pass

        # Form-urlencoded
        try:
            form = "&".join(f"{k}={v}" for k, v in body.items())
            r = client.post(f"{LULU}{ep}", content=form,
                headers={**lulu_h, "Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
            if r.status_code not in (404, 405) and len(r.content) > 10:
                try:
                    d = r.json()
                    print(f"  [{r.status_code}] POST {ep} (form)")
                    print(f"    Body: {form}")
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:400]}")
                    if isinstance(d, dict):
                        for tk in ["token", "access_token", "key", "auth_token", "Token"]:
                            if tk in d:
                                print(f"    >>> TOKEN: {d[tk][:60] if isinstance(d[tk], str) else d[tk]}... <<<")
                                save("lulu_token.json", d)
                except:
                    pass
        except:
            pass

# ============================================================
# 3. SADHAN - Verify OTP
# ============================================================
print("\n" + "=" * 60)
print("3. SADHAN - Verify OTP")
print("=" * 60)

sadhan_h = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Alsadhan%20Stores/1 CFNetwork/1404.0.5 Darwin/22.3.0",
    "Referer": "https://alsadhan.witheldokan.com/",
}

sadhan_bodies = [
    {"phone": PHONE_INTL, "otp": OTP},
    {"phone": PHONE_INTL, "code": OTP},
    {"mobile": PHONE_INTL, "otp": OTP},
]

sadhan_endpoints = [
    "https://masterapi.witheldokan.com/api/customer/auth",
    "https://masterapi.witheldokan.com/api/customer/verify",
    "https://masterapi.witheldokan.com/api/customer/otp/verify",
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
                    print(f"    Response: {json.dumps(d, ensure_ascii=False)[:400]}")
                    if isinstance(d, dict) and "token" in d:
                        print(f"    >>> TOKEN: {d['token'][:60]}... <<<")
                        save("sadhan_token.json", d)
                except:
                    pass
        except Exception as e:
            if "timeout" in type(e).__name__.lower():
                print(f"  [TIMEOUT] Sadhan unreachable")
                break

client.close()
print("\n=== DONE ===")
