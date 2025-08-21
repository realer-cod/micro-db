# Создайте скрипт определения путей
@"
# Универсальный скрипт определения путей проекта
function Get-ProjectPaths {
    # Определяем корень проекта (где есть app/, alembic/, requirements.txt)
    `$currentPath = Get-Location
    `$projectRoot = `$currentPath
    
    # Ищем корень проекта вверх по дереву
    while (`$projectRoot.Parent -and -not (Test-Path (Join-Path `$projectRoot "requirements.txt"))) {
        `$projectRoot = `$projectRoot.Parent
    }
    
    if (-not (Test-Path (Join-Path `$projectRoot "requirements.txt"))) {
        # Если не нашли, используем текущую папку
        `$projectRoot = `$currentPath
    }
    
    return @{
        ProjectRoot = `$projectRoot.Path
        BackupsDir = Join-Path `$projectRoot.Path "postgres_data\backups"
        ScriptsDir = Join-Path `$projectRoot.Path "postgres_data\scripts"
        ConfigDir = Join-Path `$projectRoot.Path "postgres_data\config"
    }
}

# Экспортируем функцию
Export-ModuleMember -Function Get-ProjectPaths
"@ | Out-File -FilePath "./postgres_data/scripts/get_project_paths.ps1" -Encoding UTF8

echo "✅ Скрипт определения путей создан"
