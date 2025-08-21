# Улучшенный скрипт бэкапа PostgreSQL
Write-Host "Начинаем создание бэкапа..." -ForegroundColor Green

# Проверка что контейнер запущен
$containerRunning = docker ps --filter "name=proxy_stats_db" --format "{{.Names}}" 2>$null
if (-not $containerRunning) {
    Write-Host "Ошибка: Контейнер proxy_stats_db не запущен" -ForegroundColor Red
    Write-Host "Запустите контейнер перед созданием бэкапа" -ForegroundColor Yellow
    exit 1
}

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupFile = "postgres_data\backups\backup_$timestamp.sql"
Write-Host "Файл бэкапа: $backupFile" -ForegroundColor Cyan

# Убедимся что папка бэкапов существует
if (-not (Test-Path "postgres_data\backups")) {
    New-Item -ItemType Directory -Path "postgres_data\backups" -Force | Out-Null
    Write-Host "Создана папка бэкапов" -ForegroundColor Yellow
}

# Проверка что база данных содержит данные перед бэкапом
Write-Host "Проверяем содержимое базы данных..." -ForegroundColor Cyan
$recordCount = docker exec proxy_stats_db psql -U admin -d proxy_stats -t -c "SELECT COUNT(*) FROM proxy_earnings;" 2>$null

if ($LASTEXITCODE -eq 0 -and $recordCount) {
    $recordCount = $recordCount.Trim()
    Write-Host "Записей в базе для бэкапа: $recordCount" -ForegroundColor Green
} else {
    Write-Host "Предупреждение: Не удалось определить количество записей" -ForegroundColor Yellow
    Write-Host "Продолжаем создание бэкапа..." -ForegroundColor Yellow
}

# Создание бэкапа
Write-Host "Выполняем pg_dump..." -ForegroundColor Yellow
docker exec -t proxy_stats_db pg_dump -U admin --data-only --no-owner --no-privileges proxy_stats > $backupFile

# Проверяем результат
# Проверяем результат
if ($LASTEXITCODE -eq 0) {
    $fileSize = (Get-Item $backupFile).Length

    # НОВАЯ УЛУЧШЕННАЯ ПРОВЕРКА: ищем только команду COPY, так как мы используем --data-only
    $hasContent = Get-Content $backupFile | Select-String -Pattern "COPY " -Quiet

    if ($hasContent) {
        # Бэкап содержит данные (команда COPY найдена)
        Write-Host "Бэкап с данными успешно создан!" -ForegroundColor Green
        Write-Host "Размер файла: $fileSize байт" -ForegroundColor Green
        Write-Host "Расположение: $(Resolve-Path $backupFile)" -ForegroundColor Green
        
        # Показываем количество бэкапов
        $backupCount = (Get-ChildItem "postgres_data\backups" -Filter "*.sql").Count
        Write-Host "Всего бэкапов в папке: $backupCount" -ForegroundColor Green
        
    } else {
        # Бэкап НЕ содержит данных (команда COPY не найдена)
        Write-Host "ИНФОРМАЦИЯ: База данных была пуста. Бэкап содержит только структуру." -ForegroundColor Yellow
        Write-Host "Размер файла: $fileSize байт" -ForegroundColor Yellow
        
        # НЕ удаляем файл, но сообщаем, что он без данных
        Write-Host "Файл сохранен, но восстановление данных из него не требуется." -ForegroundColor Cyan
    }
    
}
