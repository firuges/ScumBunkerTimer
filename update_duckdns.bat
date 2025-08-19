@echo off
REM Reemplazar TOKEN con tu token de DuckDNS
REM Reemplazar scumbottimer con tu subdominio

set DUCKDNS_TOKEN=237953e4-d5da-4fe0-a9d3-5c5b49d81816
set DUCKDNS_SUBDOMAIN=scumbottimer

echo Actualizando DuckDNS...

REM Intentar con curl ignorando certificados SSL
curl -k "https://www.duckdns.org/update?domains=%DUCKDNS_SUBDOMAIN%&token=%DUCKDNS_TOKEN%&ip="

REM Si curl falla, intentar con PowerShell como alternativa
if %errorlevel% neq 0 (
    echo Curl falló, intentando con PowerShell...
    powershell -Command "try { $response = Invoke-RestMethod -Uri 'https://www.duckdns.org/update?domains=%DUCKDNS_SUBDOMAIN%&token=%DUCKDNS_TOKEN%&ip=' -SkipCertificateCheck; Write-Host $response } catch { $response = Invoke-WebRequest -Uri 'https://www.duckdns.org/update?domains=%DUCKDNS_SUBDOMAIN%&token=%DUCKDNS_TOKEN%&ip=' -UseBasicParsing; Write-Host $response.Content }"
)

echo %date% %time% - DuckDNS actualizado >> C:\inetpub\stock\backend\logs\duckdns.log