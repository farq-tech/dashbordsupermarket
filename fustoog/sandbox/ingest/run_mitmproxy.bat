@echo off
REM Run mitmproxy with the AWFR ingest addon
REM يتطلب تثبيت mitmproxy مسبقًا (https://mitmproxy.org/)

set SCRIPT_DIR=%~dp0
set ADDON=%SCRIPT_DIR%send_to_ingest.py

echo Starting mitmproxy on http://localhost:8080 ...
echo Addon: %ADDON%

mitmproxy -s "%ADDON%"


