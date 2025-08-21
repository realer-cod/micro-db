@echo off
chcp 65001 >nul
echo.
echo 🛑 ОСТАНОВКА МИКРОСЕРВИСА
echo ========================
echo.

echo 💾 Создаем бэкап перед остановкой...
if exist "postgres_data\scripts\backup_database.ps1" (
    powershell -ExecutionPolicy Bypass -File "postgres_data\scripts\backup_database.ps1"
    echo ✅ Бэкап создан
) else (
    echo ⚠️  Скрипт бэкапа не найден
)

echo 🛑 Останавливаем систему...
docker-compose down

echo ✅ СИСТЕМА ОСТАНОВЛЕНА!
echo =======================
echo 💾 Данные сохранены в Volume
echo 🔄 Для запуска используйте start.bat
echo.
pause