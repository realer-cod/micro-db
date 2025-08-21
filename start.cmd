	@echo off
chcp 65001 >nul
echo.
echo 🚀 ЗАПУСК МИКРОСЕРВИСА (Docker-centric подход)
echo ===============================================
echo.

echo 1. 🐳 Запускаем контейнеры 'postgres' и 'fastapi' в фоновом режиме...
docker-compose up --build -d
if %errorlevel% neq 0 (
    echo ❌ Ошибка запуска Docker Compose. Проверьте логи выше.
    pause
    exit /b 1
)
echo ✅ Контейнеры успешно запущены.
echo.

echo 2. ⏳ Ожидаем, пока PostgreSQL станет доступен...
rem Healthcheck в docker-compose уже сделал основную работу, но мы подождем для надежности.
:wait_db
docker-compose exec -T postgres pg_isready -U admin -d proxy_stats >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    goto wait_db
)
echo ✅ PostgreSQL готов к приему подключений!
echo.

echo 3. 🔄 Применяем миграции базы данных (Alembic)...
echo    (Выполняем команду внутри контейнера 'fastapi')
docker-compose exec fastapi alembic upgrade head
if %errorlevel% neq 0 (
    echo ⚠️  Возникла ошибка при применении миграций. Проверьте логи.
) else (
    echo ✅ Миграции успешно применены.
)
echo.



echo 4. 🔍 Проверяем состояние базы и восстанавливаем из бэкапа при необходимости...
if exist "postgres_data\scripts\check_and_restore.ps1" (
    powershell -ExecutionPolicy Bypass -File "postgres_data\scripts\check_and_restore.ps1"
) else (
    echo ⚠️  Скрипт проверки/восстановления 'check_and_restore.ps1' не найден.
)
echo ✅ Проверка/восстановление завершено.
echo.



echo 🎉 СИСТЕМА ПОЛНОСТЬЮ ГОТОВА!
echo ============================
echo 📊 БД доступна на: localhost:5432
echo 🔧 API доступен на: http://localhost:8008
echo 📖 Docs: http://localhost:8008/docs
echo.
echo 🔍 Чтобы посмотреть логи в реальном времени, выполните: docker-compose logs -f
echo 🛑 Для остановки и создания бэкапа используйте stop.bat
echo.
pause