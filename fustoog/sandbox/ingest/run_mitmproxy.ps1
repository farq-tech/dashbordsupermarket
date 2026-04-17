Param(
  [string]$Webhook = "http://localhost:8787/ingest"
)
# شغّل mitmproxy مع الإضافة الخاصة بالإرسال للريلاي
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$addon = Join-Path $scriptDir "send_to_ingest.py"

Write-Host "Starting mitmproxy with addon: $addon"
Write-Host "Webhook: $Webhook"

# تمرير متغير البيئة داخل mitmproxy ليس مباشر؛ نعدل السطر مؤقتاً إن لزم.
mitmproxy -s $addon


