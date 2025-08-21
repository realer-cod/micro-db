@echo off
chcp 65001 >nul

:: Конфигурация API (при необходимости измените)
set "API_BASE=http://localhost:8008"
set "ENDPOINT=%API_BASE%/earnings/"

:: Генерируем уникальные значения
for /f %%i in ('powershell -NoProfile -Command "[DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffffffZ")"') do set "TS=%%i"
for /f %%i in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString("N")"') do set "GUID=%%i"
set "UNIQUE_KEY=%TS%_%GUID%"

:: Поля запроса (ТЕКУЩИЙ ВАРИАНТ СХЕМЫ)
set "PROXY_IP=203.0.113.10"
set "PROXY_PORT=8080"
set "PROXY_KEY=%PROXY_IP%:%PROXY_PORT%"
set "SERVER_ID=srv-eu-01"
set "BOT_ID=bot-42"
set "BOT_NAME=MyEarner"
set "FAUCET_NAME=manual_submit"
set "FAUCET_URL=https://example-faucet.com/session/123"
set "REWARD_AMOUNT=0.00025000"
set "REWARD_CURRENCY=BTC"
set "SUCCESS=true"
set "ERROR_MESSAGE="
for /f %%i in ('powershell -NoProfile -Command "[DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")"') do set "EVENT_TS=%%i"
set "EXTRA_DATA={"session_id":"%GUID%","asn":12345,"asn_org":"ExampleNet"}"

:: Собираем JSON
setlocal EnableDelayedExpansion
set "JSON={"
set "JSON=!JSON!"proxy_ip":"%PROXY_IP%","
set "JSON=!JSON!"proxy_port":%PROXY_PORT%,"
set "JSON=!JSON!"proxy_key":"%PROXY_KEY%","
set "JSON=!JSON!"server_id":"%SERVER_ID%","
set "JSON=!JSON!"bot_id":"%BOT_ID%","
set "JSON=!JSON!"bot_name":"%BOT_NAME%","
set "JSON=!JSON!"faucet_name":"%FAUCET_NAME%","
set "JSON=!JSON!"faucet_url":"%FAUCET_URL%","
set "JSON=!JSON!"reward_amount":"%REWARD_AMOUNT%","
set "JSON=!JSON!"reward_currency":"%REWARD_CURRENCY%","
set "JSON=!JSON!"unique_key":"%UNIQUE_KEY%","
set "JSON=!JSON!"success":%SUCCESS%,"
set "JSON=!JSON!"error_message":null,"
set "JSON=!JSON!"event_timestamp":"%EVENT_TS%","
set "JSON=!JSON!"extra_data":"%EXTRA_DATA%""
set "JSON=!JSON!}"

echo.
echo Отправляем запрос в %ENDPOINT%
echo Unique-Key: %UNIQUE_KEY%
echo.

curl -s -X POST ^
-H "Content-Type: application/json" ^
-d "!JSON!" ^
"%ENDPOINT%" | powershell -NoProfile -Command "$input | Write-Output"

if errorlevel 1 (
echo.
echo Ошибка отправки запроса (curl errorlevel %errorlevel%)
exit /b 1
)

echo.
echo Готово.
endlocal

pause