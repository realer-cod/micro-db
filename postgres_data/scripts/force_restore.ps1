# Скрипт принудительного восстановления PostgreSQL
param([string]$BackupFile)

Write-Host "🔧 СКРИПТ ПРИНУДИТЕЛЬНОГО ВОССТАНОВЛЕНИЯ" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow

# Проверка подключения к контейнеру
Write-Host "🔍 Проверяем подключение к PostgreSQL..."
$containerRunning = docker ps --filter "name=proxy_stats_db" --format "{{.Names}}" 2>$null
if (-not $containerRunning) {
    Write-Host "❌ Контейнер proxy_stats_db не запущен" -ForegroundColor Red
    Write-Host "💡 Запустите: docker start proxy_stats_db" -ForegroundColor Yellow
    exit 1
}

# Показать текущее состояние базы
Write-Host "📊 Текущее состояние базы данных:"
$currentCount = docker exec proxy_stats_db psql -U admin -d proxy_stats -t -c "SELECT COUNT(*) FROM proxy_earnings;" 2>$null
if ($currentCount) {
    Write-Host "   Записей в базе: $($currentCount.Trim())" -ForegroundColor Cyan
    
    # Показать текущие записи
    Write-Host "   Текущие записи:" -ForegroundColor Cyan
    docker exec proxy_stats_db psql -U admin -d proxy_stats -c "SELECT id, bot_name, proxy_key FROM proxy_earnings ORDER BY id LIMIT 5;"
} else {
    Write-Host "   База данных недоступна или пуста" -ForegroundColor Yellow
}

Write-Host ""

# Если не указан файл бэкапа - показать список
if (-not $BackupFile) {
    Write-Host "📂 Доступные бэкапы:" -ForegroundColor Green
    if (Test-Path "postgres_data\backups") {
        $backups = Get-ChildItem "postgres_data\backups" -Filter "*.sql" | Sort-Object CreationTime -Descending
        if ($backups) {
            $backups | ForEach-Object {
                $size = [math]::Round($_.Length / 1KB, 2)
                Write-Host "   📄 $($_.Name)" -ForegroundColor White
                Write-Host "      Создан: $($_.CreationTime)" -ForegroundColor Gray
                Write-Host "      Размер: $size KB" -ForegroundColor Gray
                Write-Host ""
            }
            Write-Host "💡 Использование: .\force_restore.ps1 -BackupFile 'имя_файла.sql'" -ForegroundColor Yellow
            Write-Host "💡 Пример: .\force_restore.ps1 -BackupFile '$($backups[0].Name)'" -ForegroundColor Yellow
        } else {
            Write-Host "   Бэкапы не найдены" -ForegroundColor Red
        }
    } else {
        Write-Host "   Папка бэкапов не найдена" -ForegroundColor Red
    }
    exit 0
}

# Проверка существования файла бэкапа
$fullBackupPath = "postgres_data\backups\$BackupFile"
if (-not (Test-Path $fullBackupPath)) {
    Write-Host "❌ Файл бэкапа не найден: $fullBackupPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "📂 Доступные бэкапы:"
    Get-ChildItem "postgres_data\backups" -Filter "*.sql" | ForEach-Object {
        Write-Host "   $($_.Name)" -ForegroundColor White
    }
    exit 1
}

# Информация о выбранном бэкапе
$backupInfo = Get-Item $fullBackupPath
$backupSize = [math]::Round($backupInfo.Length / 1KB, 2)
Write-Host "📄 Выбранный бэкап:" -ForegroundColor Green
Write-Host "   Файл: $($backupInfo.Name)" -ForegroundColor White
Write-Host "   Создан: $($backupInfo.CreationTime)" -ForegroundColor Gray
Write-Host "   Размер: $backupSize KB" -ForegroundColor Gray

# КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ
Write-Host ""
Write-Host "⚠️  ВНИМАНИЕ! ПРИНУДИТЕЛЬНОЕ ВОССТАНОВЛЕНИЕ!" -ForegroundColor Red -BackgroundColor Yellow
Write-Host "🚨 Это действие:" -ForegroundColor Red
Write-Host "   • Удалит ВСЕ текущие данные в таблице proxy_earnings" -ForegroundColor Red
Write-Host "   • Сбросит счетчик автоинкремента" -ForegroundColor Red
Write-Host "   • Заменит данные на состояние из бэкапа" -ForegroundColor Red
Write-Host ""
Write-Host "⏰ Текущие данные будут БЕЗВОЗВРАТНО потеряны!" -ForegroundColor Red

# Двойное подтверждение
Write-Host ""
Write-Host "🔐 Для продолжения введите 'FORCE' (заглавными буквами):" -ForegroundColor Yellow
$confirmation1 = Read-Host
if ($confirmation1 -ne "FORCE") {
    Write-Host "❌ Неверное подтверждение. Восстановление отменено." -ForegroundColor Red
    exit 0
}

Write-Host "🔐 Подтвердите еще раз, введите 'YES':" -ForegroundColor Yellow
$confirmation2 = Read-Host
if ($confirmation2 -ne "YES") {
    Write-Host "❌ Восстановление отменено пользователем." -ForegroundColor Red
    exit 0
}

# Процесс восстановления
Write-Host ""
Write-Host "🚀 Начинаем принудительное восстановление..." -ForegroundColor Green

# Шаг 1: Очистка данных
Write-Host "🧹 Очищаем все данные из таблицы..."
docker exec -it proxy_stats_db psql -U admin -d proxy_stats -c "TRUNCATE TABLE proxy_earnings RESTART IDENTITY CASCADE;"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка очистки таблицы" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Таблица очищена" -ForegroundColor Green

# Шаг 2: Восстановление данных
Write-Host "📥 Восстанавливаем данные из бэкапа..."
Get-Content $fullBackupPath | docker exec -i proxy_stats_db psql -U admin proxy_stats

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Данные успешно восстановлены!" -ForegroundColor Green
    
    # Проверка результата
    Write-Host ""
    Write-Host "🔍 Проверяем результат восстановления..."
    $newCount = docker exec proxy_stats_db psql -U admin -d proxy_stats -t -c "SELECT COUNT(*) FROM proxy_earnings;" 2>$null
    Write-Host "📊 Восстановлено записей: $($newCount.Trim())" -ForegroundColor Green
    
    # Показать восстановленные записи
    Write-Host ""
    Write-Host "📋 Восстановленные записи:" -ForegroundColor Cyan
    docker exec proxy_stats_db psql -U admin -d proxy_stats -c "SELECT id, bot_name, proxy_key, created_at FROM proxy_earnings ORDER BY id;"
    
    Write-Host ""
    Write-Host "🎉 ПРИНУДИТЕЛЬНОЕ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!" -ForegroundColor Green -BackgroundColor Black
} else {
    Write-Host "❌ Ошибка восстановления данных (код: $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}
