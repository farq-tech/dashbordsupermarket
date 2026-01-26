# mitmproxy addon: send each HTTP flow to our relay webhook
# ملاحظة: هذا السكربت يرسل نسخة مبسطة لكل طلب/استجابة إلى /ingest لعرضها مباشرة في الواجهة

from mitmproxy import http, ctx
import json, requests, time

WEBHOOK = "http://localhost:8787/ingest"

def response(flow: http.HTTPFlow):
    try:
        entry = {
            "ts": int(time.time()*1000),
            "method": flow.request.method,
            "url": flow.request.url,
            "status": flow.response.status_code if flow.response else None,
            "reqHeaders": dict(flow.request.headers),
            "resHeaders": dict(flow.response.headers) if flow.response else {},
            "reqBody": flow.request.get_text() or "",
            "resBody": (flow.response.get_text() if flow.response else "") or ""
        }
        requests.post(WEBHOOK, json=entry, timeout=2)
    except Exception as e:
        ctx.log.warn(f"ingest error: {e}")


