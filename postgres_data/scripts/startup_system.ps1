# Создайте master скрипт запуска всей системы
@'
# Главный скрипт автозапуска микросервиса
param([switch]$Silent)

$ErrorActionPreference = "Continue"

if (-not $Silent) {
    Write-Host "🚀 АВТОЗАПУСК МИКРОСЕРВИСА СТАТИСТИКИ БОТОВ" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
}

# Определяем пути проекта
$projectRoot = $PSScriptRoot
while ($projectRoot.Parent -and -not (Test-Path (Join-Path $projectRoot "requirements.txt"))) {
    $projectRoot = $projectRoot.Parent
}
if (-not (Test-Path (Join-Path $projectRoot "requirements.txt"))) {
    $projectRoot = Split-Path $PSScriptRoot -Parent | Split-Path -Parent
}

Set-Location $projectRoot.Path
if (-not $Silent) { Write-Host "📁 Корень проекта: $($projectRoot.Path)" -ForegroundColor Cyan }

# Шаг 1: Проверка и запуск Docker
if (-not $Silent) { Write-Host "🐳 Проверяем Docker..." -ForegroundColor Yellow }
$dockerRunning = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
if (-not $dockerRunning) {
    if (-not $Silent) { Write-Host "⚠️  Docker не запущен. Ожидаем запуска..." -ForegroundColor Yellow }
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
    
    # Ждем запуска Docker (до 60 секунд)
    $timeout = 60
    do {
        Start-Sleep -Seconds 5
        $timeout -= 5
        $dockerCheck = docker ps 2>$null
    } while ((-not $dockerCheck) -and ($timeout -gt 0))
    
    if ($timeout -le 0) {
        Write-Host "❌ Docker не запустился в течение 60 секунд" -ForegroundColor Red
        exit 1
    }
}

# Шаг 2: Проверка PostgreSQL контейнера
if (-not $Silent) { Write-Host "🗄️  Проверяем PostgreSQL контейнер..." -ForegroundColor Yellow }
$containerStatus = docker ps --filter "name=proxy_stats_db" --format "{{.Status}}" 2>$null

if (-not $containerStatus) {
    if (-not $Silent) { Write-Host "🔄 Запускаем PostgreSQL контейнер..." -ForegroundColor Yellow }
    docker start proxy_stats_db
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ошибка запуска контейнера PostgreSQL" -ForegroundColor Red
        exit 1
    }
}

# Шаг 3: Ожидание готовности PostgreSQL (до 30 секунд)
if (-not $Silent) { Write-Host "⏳ Ожидаем готовности PostgreSQL..." -ForegroundColor Yellow }
$dbTimeout = 30
do {
    Start-Sleep -Seconds 2
    $dbTimeout -= 2
    $dbReady = docker exec proxy_stats_db pg_isready -U admin 2>$null
} while (($LASTEXITCODE -ne 0) -and ($dbTimeout -gt 0))

if ($dbTimeout -le 0) {
    Write-Host "❌ PostgreSQL не готов в течение 30 секунд" -ForegroundColor Red
    exit 1
}

if (-not $Silent) { Write-Host "✅ PostgreSQL готов к работе" -ForegroundColor Green }

# Шаг 4: Автоматическая проверка и восстановление базы данных
if (-not $Silent) { Write-Host "🔍 Запускаем проверку состояния базы данных..." -ForegroundColor Yellow }

$checkScript = Join-Path $projectRoot.Path "postgres_data\scripts\check_and_restore.ps1"
if (Test-Path $checkScript) {
    & $checkScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ошибка при проверке/восстановлении базы данных" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  Скрипт проверки базы не найден: $checkScript" -ForegroundColor Yellow
}

# Шаг 5: Применение миграций Alembic
if (-not $Silent) { Write-Host "🔄 Применяем миграции базы данных..." -ForegroundColor Yellow }
if (Test-Path ".venv\Scripts\activate.ps1") {
    & .venv\Scripts\activate.ps1
    alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Предупреждение: ошибка применения миграций" -ForegroundColor Yellow
    }
}

# Шаг 6: Запуск FastAPI сервера (опционально, в фоне)
if (-not $Silent) { 
    Write-Host "🌐 Готов к запуску FastAPI сервера..." -ForegroundColor Green
    Write-Host "💡 Для запуска API выполните: uvicorn app.main:app --host 0.0.0.0 --port 8008" -ForegroundColor Cyan
}

# Создание файла статуса готовности
$statusFile = Join-Path $projectRoot.Path "postgres_data\.system_ready"
Get-Date | Out-File -FilePath $statusFile -Encoding UTF8

if (-not $Silent) {
    Write-Host ""
    Write-Host "🎉 СИСТЕМА МИКРОСЕРВИСА ГОТОВА К РАБОТЕ!" -ForegroundColor Green -BackgroundColor Black
    Write-Host "📊 Статус базы данных: ГОТОВА" -ForegroundColor Green
    Write-Host "🔗 API будет доступен на: http://localhost:8008" -ForegroundColor Cyan
    Write-Host "📖 Документация: http://localhost:8008/docs" -ForegroundColor Cyan
}

exit 0
'@ | Out-File -FilePath ".\postgres_data\scripts\startup_system.ps1" -Encoding UTF8

Write-Host "✅ Главный скрипт автозапуска создан"
