# سكربت تشغيل mitmproxy لالتقاط طلبات Fustog من iPhone
# Fustog API Capture Tool for iPhone

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Fustog API Capture - iPhone  " -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# التحقق من تثبيت mitmproxy
Write-Host "[1/5] التحقق من mitmproxy..." -ForegroundColor Yellow

try {
    $mitmwebPath = Get-Command mitmweb -ErrorAction Stop
    Write-Host "  ✓ mitmproxy مثبت" -ForegroundColor Green
} catch {
    Write-Host "  ✗ mitmproxy غير مثبت!" -ForegroundColor Red
    Write-Host ""
    Write-Host "لتثبيت mitmproxy، شغّل:" -ForegroundColor Yellow
    Write-Host "  pip install mitmproxy" -ForegroundColor White
    Write-Host ""
    Read-Host "اضغط Enter للخروج"
    exit
}

Write-Host ""

# الحصول على IP الكمبيوتر
Write-Host "[2/5] الحصول على IP الكمبيوتر..." -ForegroundColor Yellow

$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | 
              Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.PrefixOrigin -eq "Dhcp"} | 
              Select-Object -First 1).IPAddress

if (-not $ipAddress) {
    # محاولة بطريقة بديلة
    $ipAddress = (Get-NetIPConfiguration | 
                  Where-Object {$_.IPv4DefaultGateway -ne $null} | 
                  Select-Object -First 1).IPv4Address.IPAddress
}

if ($ipAddress) {
    Write-Host "  ✓ IP Address: $ipAddress" -ForegroundColor Green
} else {
    Write-Host "  ⚠ لم نتمكن من تحديد IP تلقائياً" -ForegroundColor Yellow
    Write-Host "  يمكنك معرفة IP بتشغيل: ipconfig" -ForegroundColor White
    $ipAddress = "192.168.x.x"
}

Write-Host ""

# إنشاء مجلد للحفظ
Write-Host "[3/5] إنشاء مجلد للبيانات..." -ForegroundColor Yellow

$captureDir = ".\captured_data"
if (-not (Test-Path $captureDir)) {
    New-Item -ItemType Directory -Path $captureDir | Out-Null
    Write-Host "  ✓ تم إنشاء مجلد: $captureDir" -ForegroundColor Green
} else {
    Write-Host "  ✓ المجلد موجود: $captureDir" -ForegroundColor Green
}

Write-Host ""

# عرض التعليمات
Write-Host "[4/5] التعليمات:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  على iPhone:" -ForegroundColor Cyan
Write-Host "  -----------" -ForegroundColor Cyan
Write-Host "  1. Settings > WiFi > (i) > HTTP Proxy > Manual" -ForegroundColor White
Write-Host "  2. Server: $ipAddress" -ForegroundColor White
Write-Host "  3. Port: 8080" -ForegroundColor White
Write-Host "  4. Safari > http://mitm.it > Install Certificate" -ForegroundColor White
Write-Host "  5. Settings > General > About > Certificate Trust" -ForegroundColor White
Write-Host "  6. فعّل mitmproxy ✓" -ForegroundColor White
Write-Host ""
Write-Host "  ثم استخدم تطبيق Fustog!" -ForegroundColor Green
Write-Host ""
Write-Host "  على الكمبيوتر:" -ForegroundColor Cyan
Write-Host "  -------------" -ForegroundColor Cyan
Write-Host "  - افتح المتصفح: http://127.0.0.1:8081" -ForegroundColor White
Write-Host "  - راقب الطلبات من iPhone" -ForegroundColor White
Write-Host "  - احفظ: File > Save > HAR format" -ForegroundColor White
Write-Host ""

# الانتظار للتأكيد
Write-Host "[5/5] جاهز للبدء!" -ForegroundColor Yellow
Write-Host ""
Write-Host "⚠️  تأكد من:" -ForegroundColor Yellow
Write-Host "   • iPhone والكمبيوتر على نفس WiFi" -ForegroundColor White
Write-Host "   • Firewall لا يمنع Port 8080" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "هل أنت جاهز لبدء mitmweb? (y/n)"

if ($confirm -ne "y" -and $confirm -ne "Y" -and $confirm -ne "yes" -and $confirm -ne "Yes") {
    Write-Host ""
    Write-Host "تم الإلغاء." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "  بدء mitmweb...               " -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "✓ الواجهة ستفتح على: http://127.0.0.1:8081" -ForegroundColor Cyan
Write-Host "✓ Proxy يعمل على: http://$ipAddress:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "لإيقاف mitmweb: اضغط Ctrl+C" -ForegroundColor Yellow
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# تشغيل mitmweb
try {
    mitmweb --web-host 127.0.0.1 --web-port 8081 --listen-host 0.0.0.0 --listen-port 8080
} catch {
    Write-Host ""
    Write-Host "✗ حدث خطأ في تشغيل mitmweb" -ForegroundColor Red
    Write-Host "الخطأ: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "جرب تشغيل mitmweb يدوياً:" -ForegroundColor Yellow
    Write-Host "  mitmweb" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  تم إيقاف mitmweb             " -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "لا تنسَ:" -ForegroundColor Yellow
Write-Host "  • تعطيل Proxy من iPhone" -ForegroundColor White
Write-Host "  • حفظ HAR file إذا لم تفعل" -ForegroundColor White
Write-Host "  • تحليل HAR: python scripts\analyze_har.py <file.har>" -ForegroundColor White
Write-Host ""

Read-Host "اضغط Enter للخروج"
