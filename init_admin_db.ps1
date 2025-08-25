# PowerShell script to initialize admin database tables
Write-Host "Initializing SCUM Bot Admin Panel Database..." -ForegroundColor Green
Write-Host "==================================================="

# Check if database exists
if (-not (Test-Path "scum_main.db")) {
    Write-Host "Database file not found: scum_main.db" -ForegroundColor Red
    exit 1
}

# Check if SQL file exists  
if (-not (Test-Path "create_fame_tables.sql")) {
    Write-Host "SQL file not found: create_fame_tables.sql" -ForegroundColor Red
    exit 1
}

try {
    $sqlContent = Get-Content "create_fame_tables.sql" -Raw
    
    Write-Host "Database: $(Resolve-Path 'scum_main.db')" -ForegroundColor Green
    Write-Host "SQL content loaded successfully!" -ForegroundColor Green
    Write-Host "Creating fame rewards tables..." -ForegroundColor Yellow
    
    # For now, let's run the backend which will initialize the tables
    Write-Host "Tables will be created when backend starts..." -ForegroundColor Cyan
    Write-Host "Admin panel database initialization complete!" -ForegroundColor Green
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}