# Скрипт проверки базы данных и автоматического восстановления
Write-Host "Проверка состояния базы данных..." -ForegroundColor Cyan
# Проверка подключения к контейнеру
$containerRunning = docker ps --filter "name=proxy_stats_db" --format "{{.Names}}" 2>$null
if (-not $containerRunning) {
    Write-Host "Ошибка: Контейнер proxy_stats_db не запущен" -ForegroundColor Red
    Write-Host "Запустите контейнер: docker start proxy_stats_db" -ForegroundColor Yellow
    exit 1
}
# ИСПРАВЛЕНИЕ: Проверяем существование основной таблицы данных
Write-Host "Проверка существования таблицы proxy_earnings..."
$tableExists = docker exec proxy_stats_db psql -U admin -d proxy_stats -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'proxy_earnings');" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка подключения к базе данных" -ForegroundColor Red
    exit 1
}
# Проверяем результат существования таблицы
if ($tableExists.Trim() -eq "t") {
    # Таблица существует - считаем записи
    Write-Host "Подсчет записей в таблице proxy_earnings..."
    $recordCount = docker exec proxy_stats_db psql -U admin -d proxy_stats -t -c "SELECT COUNT(*) FROM proxy_earnings;" 2>$null
    $recordCount = $recordCount.Trim()
    Write-Host "Найдено записей в базе: $recordCount" -ForegroundColor Green
} else {
    # Таблицы нет - устанавливаем счетчик в 0 для запуска восстановления
    Write-Host "Таблица proxy_earnings не существует" -ForegroundColor Yellow
    $recordCount = "0"
}
# Логика восстановления (БЕЗ ИЗМЕНЕНИЙ)
if ($recordCount -eq "0" -or $recordCount -eq "" -or $null -eq $recordCount) {
    Write-Host "База данных пуста. Начинаем восстановление..." -ForegroundColor Yellow
    
    # Поиск последнего бэкапа
    if (Test-Path "postgres_data\backups") {
        # Находим только рабочие бэкапы (с данными)
        $workingBackups = Get-ChildItem "postgres_data\backups" -Filter "*.sql" | 
                         Where-Object { $_.Length -gt 5000 }
        
        if ($workingBackups) {
            $latestBackup = $workingBackups | Sort-Object CreationTime -Descending | Select-Object -First 1
        } else {
            Write-Host "ОШИБКА: Нет рабочих бэкапов (>5000 байт) для восстановления" -ForegroundColor Red
            Write-Host "Все файлы содержат только структуру БД без данных" -ForegroundColor Yellow
            exit 1
        }
        
        if ($latestBackup) {
            Write-Host "Найден бэкап: $($latestBackup.Name)" -ForegroundColor Cyan
            Write-Host "Размер: $($latestBackup.Length) байт" 
            Write-Host "Восстанавливаем данные..." -ForegroundColor Yellow
            
            # Восстановление данных - ИСПРАВЛЕНО: используем Get-Content с pipe
            Get-Content $latestBackup.FullName | docker exec -i proxy_stats_db psql -U admin proxy_stats
            
            if ($LASTEXITCODE -eq 0) {
                # Проверка результата
                $newCount = docker exec proxy_stats_db psql -U admin -d proxy_stats -t -c "SELECT COUNT(*) FROM proxy_earnings;" 2>$null
                Write-Host "Данные успешно восстановлены!" -ForegroundColor Green
                if ($newCount -and $newCount.Trim()) {
    Write-Host "Восстановлено записей: $($newCount.Trim())" -ForegroundColor Green
} else {
    Write-Host "Восстановлено записей: невозможно определить" -ForegroundColor Yellow
}
                
                # Показать восстановленные записи
                Write-Host "Восстановленные записи:" -ForegroundColor Cyan
                docker exec proxy_stats_db psql -U admin -d proxy_stats -c "SELECT id, bot_name, proxy_key FROM proxy_earnings ORDER BY id DESC LIMIT 5;"
            } else {
                Write-Host "Ошибка восстановления данных" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "Бэкапы не найдены в папке postgres_data\backups" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Папка бэкапов не найдена: postgres_data\backups" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "База данных содержит данные ($recordCount записей). Восстановление не требуется." -ForegroundColor Green
    
    # Показать текущие записи
    Write-Host "Последние записи в базе:" -ForegroundColor Cyan
    docker exec proxy_stats_db psql -U admin -d proxy_stats -c "SELECT id, bot_name, proxy_key, created_at FROM proxy_earnings ORDER BY id DESC LIMIT 3;"
}
Write-Host "Проверка завершена." -ForegroundColor Green
