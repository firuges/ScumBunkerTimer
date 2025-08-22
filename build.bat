@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: ===========================================
::   SCUM Bot V2 - Build Generator Completo
:: ===========================================
title SCUM Bot V2 - Build Generator
color 0B

echo ========================================
echo   SCUM Bot V2 - Build Generator
echo ========================================
echo.
echo   Genera una carpeta portable completa
echo   Con TODOS los sistemas integrados
echo.
echo ========================================

:: Cambiar al directorio del script
cd /d "%~dp0"

:: Verificar archivos esenciales
echo.
echo 📄 Verificando archivos esenciales...

if not exist "BunkerAdvice_V2.py" (
    color 0C
    echo ❌ ERROR: No se encuentra BunkerAdvice_V2.py
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    color 0C
    echo ❌ ERROR: No se encuentra requirements.txt
    pause
    exit /b 1
)

echo ✅ Archivos esenciales verificados

:: Definir directorio de build
set "BUILD_DIR=build"
set "BUILD_TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "BUILD_TIMESTAMP=%BUILD_TIMESTAMP: =0%"
set "BUILD_FULL_DIR=%BUILD_DIR%\ScumBot_Complete_%BUILD_TIMESTAMP%"

:: Crear directorio de build
echo.
echo 📁 Creando directorio de build...
if exist "%BUILD_DIR%" (
    echo    Limpiando build anterior...
    rmdir /s /q "%BUILD_DIR%" >nul 2>&1
)

mkdir "%BUILD_FULL_DIR%"
mkdir "%BUILD_FULL_DIR%\logs"
mkdir "%BUILD_FULL_DIR%\backup"
mkdir "%BUILD_FULL_DIR%\config"
mkdir "%BUILD_FULL_DIR%\scripts"
mkdir "%BUILD_FULL_DIR%\docs"
mkdir "%BUILD_FULL_DIR%\databases"

echo ✅ Directorio creado: %BUILD_FULL_DIR%

:: ===========================================
::   COPIAR ARCHIVOS PRINCIPALES
:: ===========================================
echo.
echo 📄 Copiando archivos principales del bot...

:: Archivo principal
copy "BunkerAdvice_V2.py" "%BUILD_FULL_DIR%\" >nul 2>&1

:: Sistemas principales
copy "database_v2.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "bot_status_system.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "bot_starter.py" "%BUILD_FULL_DIR%\" >nul 2>&1

:: Sistema de servidores
copy "server_monitor.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "server_database.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "server_commands.py" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Archivos principales copiados

:: ===========================================
::   MODULO CORE REFACTORIZADO (NUEVO)
:: ===========================================
echo.
echo 🔧 Copiando módulo core refactorizado...

:: Crear directorio core
mkdir "%BUILD_FULL_DIR%\core" >nul 2>&1

copy "core\__init__.py" "%BUILD_FULL_DIR%\core\" >nul 2>&1
copy "core\user_manager.py" "%BUILD_FULL_DIR%\core\" >nul 2>&1

echo ✅ Módulo core copiado (sistema de usuarios centralizado)

:: ===========================================
::   SISTEMA DE TAXI COMPLETO
:: ===========================================
echo.
echo 🚖 Copiando sistema de taxi completo...

copy "taxi_system.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "taxi_database.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "taxi_admin.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "taxi_config.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "banking_system.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "welcome_system.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "translation_manager.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "migrate_taxi_db.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "migrate_mechanic_db.py" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Sistema de taxi copiado

:: ===========================================
::   SISTEMA DE MECANICO
:: ===========================================
echo.
echo 🔧 Copiando sistema de mecánico...

copy "mechanic_system.py" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Sistema de mecánico copiado

:: ===========================================
::   SISTEMA PREMIUM
:: ===========================================
echo.
echo 💎 Copiando sistema premium...

copy "premium_commands.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "premium_exclusive_commands.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "premium_utils.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "subscription_manager.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "shop_config.py" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Sistema premium copiado

:: ===========================================
::   SISTEMA DE RATE LIMITING Y ESCALABILIDAD
:: ===========================================
echo.
echo ⚡ Copiando sistema de rate limiting y escalabilidad...

copy "rate_limiter.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "rate_limit_admin.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "database_pool.py" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Sistema de rate limiting copiado

:: ===========================================
::   SISTEMA DE ALERTAS
:: ===========================================
echo.
echo 🔔 Copiando sistema de alertas...

copy "reset_alerts_admin.py" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Sistema de alertas copiado

::  ===========================================
::   UTILIDADES Y HERRAMIENTAS
:: ===========================================
echo.
echo 🛠️ Copiando utilidades...

copy "economic_calculator.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "economic_optimization.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "verify_optimization.py" "%BUILD_FULL_DIR%\" >nul 2>&1

:: Herramientas de testing (opcionales pero útiles)
copy "test_taxi_system.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "test_database_fix.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "debug_user.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "check_db.py" "%BUILD_FULL_DIR%\" >nul 2>&1

:: Scripts de prueba para rate limiting y escalabilidad
copy "test_rate_limiting.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "test_bot_integration.py" "%BUILD_FULL_DIR%\" >nul 2>&1

:: Scripts de migración críticos
copy "migrate_system_tables.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "migrate_user_languages.py" "%BUILD_FULL_DIR%\" >nul 2>&1

:: ===========================================
::   TESTS DE CORRECCIONES CRÍTICAS (NUEVO)
:: ===========================================
echo.
echo 🧪 Copiando tests de correcciones críticas...

:: Tests de correcciones de botones
copy "test_button_fixes.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "test_architecture_fix.py" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Tests de correcciones copiados

:: Archivos esenciales
copy "requirements.txt" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Utilidades copiadas

:: ===========================================
::   SCRIPTS DE INSTALACION
:: ===========================================
echo.
echo 📦 Copiando scripts de instalación...

copy "scripts\install_windows_simple.bat" "%BUILD_FULL_DIR%\scripts\" >nul 2>&1
copy "scripts\install_windows_fixed.bat" "%BUILD_FULL_DIR%\scripts\" >nul 2>&1
copy "scripts\install_windows_debug.bat" "%BUILD_FULL_DIR%\scripts\" >nul 2>&1
copy "scripts\cleanup.bat" "%BUILD_FULL_DIR%\scripts\" >nul 2>&1

echo ✅ Scripts de instalación copiados

:: ===========================================
::   SISTEMA DE TRADUCCIONES
:: ===========================================
echo.
echo 🌍 Copiando archivos de traducciones...

:: Crear carpeta de traducciones
if not exist "%BUILD_FULL_DIR%\translations" mkdir "%BUILD_FULL_DIR%\translations" >nul 2>&1

:: Copiar archivos de traducciones
copy "translations\*.json" "%BUILD_FULL_DIR%\translations\" >nul 2>&1

echo ✅ Sistema de traducciones copiado

:: ===========================================
::   DOCUMENTACION COMPLETA
:: ===========================================
echo.
echo 📚 Copiando documentación completa...

:: Documentación principal
copy "README.md" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "TAXI_SYSTEM_README.md" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "TAXI_SYSTEM_FINAL.md" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "MECHANIC_SYSTEM_GUIDE.md" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "MECHANIC_SYSTEM_CHANGELOG.md" "%BUILD_FULL_DIR%\" >nul 2>&1

:: Documentación en carpeta docs
copy "docs\COMANDOS_GUIA.md" "%BUILD_FULL_DIR%\docs\" >nul 2>&1
copy "docs\DEPLOY_GUIDE.md" "%BUILD_FULL_DIR%\docs\" >nul 2>&1
copy "docs\PYTHON_3.13_SOLUCION.md" "%BUILD_FULL_DIR%\docs\" >nul 2>&1
copy "docs\WINDOWS_DEPLOY.md" "%BUILD_FULL_DIR%\docs\" >nul 2>&1
copy "docs\WINDOWS_INSTALL_FIX.md" "%BUILD_FULL_DIR%\docs\" >nul 2>&1
copy "docs\TAXI_TUTORIAL.html" "%BUILD_FULL_DIR%\docs\" >nul 2>&1
copy "docs\BOT_STATUS_GUIDE.md" "%BUILD_FULL_DIR%\docs\" >nul 2>&1
copy "docs\PREMIUM_SYSTEM_DOCS.md" "%BUILD_FULL_DIR%\docs\" >nul 2>&1
copy "docs\MULTIPLE_SERVERS_GUIDE.md" "%BUILD_FULL_DIR%\docs\" >nul 2>&1

:: Documentación de correcciones críticas (NUEVO)
copy "BOTONES_CORREGIDOS.md" "%BUILD_FULL_DIR%\docs\" >nul 2>&1

:: Archivos HTML
copy "guide.html" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "bot_presentation.html" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "bot_presentation_multilang.html" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "bot_presentation.py" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Documentación copiada

:: ===========================================
::   BASES DE DATOS EXISTENTES
:: ===========================================
echo.
echo 🗄️ Copiando bases de datos existentes...

:: Verificar y copiar bases de datos si existen
set "DB_COUNT=0"

:: bunkers_v2.db ya no se usa directamente - datos migrados a scum_main.db
if exist "bunkers_v2.db" (
    echo    ⚠️  bunkers_v2.db - LEGACY (datos en scum_main.db)
) else if exist "legacy_backups\bunkers_v2.db" (
    echo    ✅ bunkers_v2.db - Movida a legacy_backups (datos en scum_main.db)
)

if exist "scum_main.db" (
    copy "scum_main.db" "%BUILD_FULL_DIR%\databases\" >nul 2>&1
    echo    ✅ scum_main.db - Base principal unificada (taxi+bank+usuarios)
    set /a DB_COUNT+=1
)

:: Mantener compatibilidad con bases antiguas si existen
if exist "taxi_system.db" (
    if not exist "scum_main.db" (
        copy "taxi_system.db" "%BUILD_FULL_DIR%\databases\" >nul 2>&1
        echo    ⚠️  taxi_system.db - Base antigua (migrar a scum_main.db)
        set /a DB_COUNT+=1
    )
)

:: scum_bank.db ya no se usa - datos migrados a scum_main.db
if exist "scum_bank.db" (
    echo    ⚠️  scum_bank.db - LEGACY (datos migrados a scum_main.db)
) else if exist "legacy_backups\scum_bank.db" (
    echo    ✅ scum_bank.db - Movida a legacy_backups (datos en scum_main.db)
)

if exist "subscriptions.db" (
    copy "subscriptions.db" "%BUILD_FULL_DIR%\databases\" >nul 2>&1
    echo    ✅ subscriptions.db - Sistema premium
    set /a DB_COUNT+=1
)

:: Buscar otras bases de datos .db
for %%f in (*.db) do (
    if not "%%f"=="scum_main.db" (
        if not "%%f"=="taxi_system.db" (
            if not "%%f"=="subscriptions.db" (
                copy "%%f" "%BUILD_FULL_DIR%\databases\" >nul 2>&1
                echo    ✅ %%f - Base de datos adicional
                set /a DB_COUNT+=1
            )
        )
    )
)

if !DB_COUNT! gtr 0 (
    echo ✅ !DB_COUNT! base(s) de datos copiada(s)
    echo    📁 Ubicación: databases\
    echo    💡 Estas BD contienen datos reales del servidor
) else (
    echo ⚠️ No se encontraron bases de datos existentes
    echo    💡 El bot creará nuevas BD automáticamente
)

:: ===========================================
::   CONFIGURACION AUTOMATICA
:: ===========================================
echo.
echo ⚙️ Creando configuración automática...

:: Leer token del .env si existe
set "DISCORD_TOKEN_VALUE="
if exist ".env" (
    for /f "usebackq delims=" %%i in (`powershell -command "if (Test-Path '.env') { (Get-Content '.env' | Where-Object { $_ -match '^DISCORD_TOKEN=' }) -replace 'DISCORD_TOKEN=', '' }"`) do (
        set "DISCORD_TOKEN_VALUE=%%i"
    )
)

:: Crear config.py completo
if defined DISCORD_TOKEN_VALUE (
    echo # Configuración completa del SCUM Bot > "%BUILD_FULL_DIR%\config.py"
    call echo DISCORD_TOKEN = '%%DISCORD_TOKEN_VALUE%%' >> "%BUILD_FULL_DIR%\config.py"
    echo ✅ Token configurado automáticamente desde .env
) else (
    echo # Configuración completa del SCUM Bot > "%BUILD_FULL_DIR%\config.py"
    echo DISCORD_TOKEN = 'TU_TOKEN_AQUI' >> "%BUILD_FULL_DIR%\config.py"
    echo ⚠️ Token requiere configuración manual
)

:: Configuración completa
echo. >> "%BUILD_FULL_DIR%\config.py"
echo # Administración del bot >> "%BUILD_FULL_DIR%\config.py"
echo BOT_CREATOR_ID = 418198613210955776 >> "%BUILD_FULL_DIR%\config.py"
echo BOT_ADMIN_IDS = [418198613210955776] >> "%BUILD_FULL_DIR%\config.py"
echo PREFIX = '/' >> "%BUILD_FULL_DIR%\config.py"
echo DEBUG = True >> "%BUILD_FULL_DIR%\config.py"
echo. >> "%BUILD_FULL_DIR%\config.py"
echo # Base de datos >> "%BUILD_FULL_DIR%\config.py"
echo DATABASE_NAME = 'scum_main.db' >> "%BUILD_FULL_DIR%\config.py"
echo TAXI_DATABASE_NAME = 'scum_main.db' >> "%BUILD_FULL_DIR%\config.py"
echo. >> "%BUILD_FULL_DIR%\config.py"
echo # Configuración de logs >> "%BUILD_FULL_DIR%\config.py"
echo LOG_LEVEL = 'INFO' >> "%BUILD_FULL_DIR%\config.py"
echo LOG_FILE = 'logs/bot.log' >> "%BUILD_FULL_DIR%\config.py"
echo. >> "%BUILD_FULL_DIR%\config.py"
echo # Sistemas habilitados >> "%BUILD_FULL_DIR%\config.py"
echo TAXI_SYSTEM_ENABLED = True >> "%BUILD_FULL_DIR%\config.py"
echo PREMIUM_SYSTEM_ENABLED = True >> "%BUILD_FULL_DIR%\config.py"
echo MECHANIC_SYSTEM_ENABLED = True >> "%BUILD_FULL_DIR%\config.py"
echo SERVER_MONITOR_ENABLED = True >> "%BUILD_FULL_DIR%\config.py"
echo RATE_LIMITING_ENABLED = True >> "%BUILD_FULL_DIR%\config.py"
echo DATABASE_POOL_ENABLED = True >> "%BUILD_FULL_DIR%\config.py"

echo ✅ config.py creado con configuración completa

:: ===========================================
::   CREAR INSTALADOR PRINCIPAL
:: ===========================================
echo.
echo 📦 Creando instalador principal...

echo @echo off > "%BUILD_FULL_DIR%\INSTALL.bat"
echo chcp 65001 ^>nul 2^>^&1 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo setlocal enabledelayedexpansion >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo title SCUM Bot V2 - Instalador Completo >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo color 0A >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ======================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo   SCUM Bot V2 - Instalador Completo >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ======================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo   Sistema completo con 10 subsistemas: >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo   ^🏠 Bunkers ^🚖 Taxi ^🏦 Bancario ^🔧 Mecánico ^🏆 Escuadrones >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo   ^📊 Monitoreo ^💎 Premium ^🔔 Alertas ^⚙️ Admin ^⚡ Rate Limiting >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ======================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo cd /d "%%~dp0" >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo 📄 Verificando archivos del sistema... >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo if not exist "requirements.txt" ^( >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     color 0C >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo ❌ ERROR: Archivos del sistema incompletos >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     pause >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     exit /b 1 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo ^) >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ✅ Archivos del sistema verificados >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo 🐍 Verificando Python... >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo python --version ^>nul 2^>^&1 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo if errorlevel 1 ^( >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     color 0C >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo ❌ Python no está instalado >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo    Descarga Python desde: https://python.org >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo    Marca "Add to PATH" durante la instalación >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     pause >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     exit /b 1 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo ^) >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ✅ Python encontrado: >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo python --version >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo 📦 Instalando dependencias completas... >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo pip install --user -r requirements.txt >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo if errorlevel 1 ^( >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     color 0C >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo ❌ Error instalando dependencias >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo    Intenta ejecutar: scripts\install_windows_debug.bat >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     pause >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     exit /b 1 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo ^) >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ✅ Dependencias instaladas correctamente >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo   🎉 INSTALACIÓN COMPLETADA >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo 📋 PRÓXIMOS PASOS: >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
if defined DISCORD_TOKEN_VALUE (
    echo echo ✅ 1. Token ya configurado automáticamente >> "%BUILD_FULL_DIR%\INSTALL.bat"
    echo echo 🗄️ 2. Migrar base de datos: python migrate_system_tables.py >> "%BUILD_FULL_DIR%\INSTALL.bat"
    echo echo 🚀 3. Ejecutar: start_bot.bat >> "%BUILD_FULL_DIR%\INSTALL.bat"
) else (
    echo echo 📝 1. Editar config.py con tu token >> "%BUILD_FULL_DIR%\INSTALL.bat"
    echo echo 🗄️ 2. Migrar base de datos: python migrate_system_tables.py >> "%BUILD_FULL_DIR%\INSTALL.bat"
    echo echo 🚀 3. Ejecutar start_bot.bat >> "%BUILD_FULL_DIR%\INSTALL.bat"
)
echo echo 📚 4. Ver docs\ para guías completas >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo pause >> "%BUILD_FULL_DIR%\INSTALL.bat"

echo ✅ INSTALL.bat creado

:: ===========================================
::   CREAR EJECUTOR PRINCIPAL
:: ===========================================
echo.
echo 🚀 Creando ejecutor principal...

echo @echo off > "%BUILD_FULL_DIR%\start_bot.bat"
echo chcp 65001 ^>nul 2^>^&1 >> "%BUILD_FULL_DIR%\start_bot.bat"
echo title SCUM Bot V2 - Sistema Completo >> "%BUILD_FULL_DIR%\start_bot.bat"
echo color 0A >> "%BUILD_FULL_DIR%\start_bot.bat"
echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo cd /d "%%~dp0" >> "%BUILD_FULL_DIR%\start_bot.bat"
echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo   SCUM Bot V2 - Iniciando Sistema Completo >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo 📍 Directorio: %%CD%% >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo 📄 Verificando sistema... >> "%BUILD_FULL_DIR%\start_bot.bat"
echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo :: Verificar archivos críticos >> "%BUILD_FULL_DIR%\start_bot.bat"
echo if not exist "BunkerAdvice_V2.py" ^( >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     color 0C >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo ❌ ERROR: Sistema incompleto >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo    Ejecuta INSTALL.bat primero >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     pause >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     exit /b 1 >> "%BUILD_FULL_DIR%\start_bot.bat"
echo ^) >> "%BUILD_FULL_DIR%\start_bot.bat"
echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo ✅ Sistema verificado - Iniciando bot... >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo 🤖 Sistemas activos: >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo    ^🏠 Bunkers   ^🚖 Taxi      ^🏦 Bancario  ^🔧 Mecánico  ^🏆 Escuadrones >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo    ^📊 Monitor   ^💎 Premium   ^🔔 Alertas   ^⚙️ Admin    ^⚡ RateLimit >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo python BunkerAdvice_V2.py >> "%BUILD_FULL_DIR%\start_bot.bat"
echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo if errorlevel 1 ^( >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     color 0C >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo ❌ El bot se cerró inesperadamente >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo 📋 Revisa los logs en: logs\bot.log >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo 🛠️ Para diagnóstico: scripts\install_windows_debug.bat >> "%BUILD_FULL_DIR%\start_bot.bat"
echo ^) >> "%BUILD_FULL_DIR%\start_bot.bat"
echo pause >> "%BUILD_FULL_DIR%\start_bot.bat"

echo ✅ start_bot.bat creado

:: ===========================================
::   CREAR README COMPLETO
:: ===========================================
echo.
echo 📋 Creando documentación completa...

echo # SCUM Bot V2 - Sistema Completo > "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ## 🚀 Instalación Rápida >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo 1. **Instalar sistema completo:** >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo    ```batch >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo    INSTALL.bat >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo    ``` >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
if defined DISCORD_TOKEN_VALUE (
    echo 2. **✅ Token ya configurado automáticamente** >> "%BUILD_FULL_DIR%\README_BUILD.md"
    echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
    echo 3. **Ejecutar bot:** >> "%BUILD_FULL_DIR%\README_BUILD.md"
) else (
    echo 2. **Configurar token:** >> "%BUILD_FULL_DIR%\README_BUILD.md"
    echo    - Editar `config.py` >> "%BUILD_FULL_DIR%\README_BUILD.md"
    echo    - Reemplazar `TU_TOKEN_AQUI` con tu token real >> "%BUILD_FULL_DIR%\README_BUILD.md"
    echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
    echo 3. **Ejecutar bot:** >> "%BUILD_FULL_DIR%\README_BUILD.md"
)
echo    ```batch >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo    start_bot.bat >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo    ``` >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ## 🎮 Sistemas Incluidos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### 🏠 Sistema de Bunkers >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Monitoreo automático de 4 bunkers SCUM >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Alertas con timezone automático ^(Uruguay, Argentina, Brasil^) >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Comandos de administración avanzados >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### 🚖 Sistema de Taxi >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Sistema completo con 5 tipos de vehículos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Registro de conductores con niveles >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Zonas del mapa con tarifas diferenciadas >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Comisiones automáticas para conductores >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### 🏦 Sistema Bancario >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Cuentas automáticas para usuarios >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Transferencias entre jugadores >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Historial completo de transacciones >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Canje diario optimizado: $500 >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Welcome bonus: $7,500 >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### 🔧 Sistema de Mecánico >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Registro y gestión de vehículos personales >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Seguros vinculados a vehículos registrados >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Límites configurables por tipo de vehículo >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Diferenciación PVP/PVE con recargo configurable >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Notificaciones DM a mecánicos registrados >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Métodos de pago: Discord y InGame >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Panel interactivo para gestión de vehículos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - **NUEVO:** Gestión de precios con botones interactivos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - **NUEVO:** Selectores visuales para tipos de vehículos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - **NUEVO:** Precios dinámicos que se actualizan automáticamente >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### 🛠️ Correcciones Críticas ^(AGOSTO 2025^) >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - **RESUELTO:** Error 404 "Unknown interaction" en botones de bunkers >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - **RESUELTO:** Error 400 "Interaction already acknowledged" >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - **MEJORADO:** Arquitectura modular ^(bunkers separados de taxi^) >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - **AÑADIDO:** Manejo robusto de errores de Discord >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - **AÑADIDO:** Tests automatizados para verificar correcciones >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Ver: `docs/BOTONES_CORREGIDOS.md` para detalles técnicos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### 🏆 Sistema de Escuadrones ^(NUEVO^) >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Creación de escuadrones con selector PvP/PvE visual >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Unión a escuadrones existentes con confirmación >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Detección automática de zona basada en membresía >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Gestión de miembros y límites personalizables >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Canal dedicado con panel persistente >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Integración completa con sistema de seguros >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### 📊 Sistema de Monitoreo >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Estado en tiempo real de servidores SCUM >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Top servidores por popularidad >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Estadísticas detalladas de uso >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### 💎 Sistema Premium >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Comandos exclusivos para usuarios premium >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Gestión de suscripciones >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Tienda virtual integrada >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### 🔔 Sistema de Alertas >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Alertas de reinicio personalizables >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Detección automática de timezone >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Horarios convertidos a zona local >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### ⚙️ Sistema de Administración >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Panel de control completo >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Configuración por servidor >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Herramientas de diagnóstico >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### ⚡ Sistema de Rate Limiting ^(NUEVO^) >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Control de uso por usuario y servidor >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Cooldowns configurables por comando >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Prevención de spam y sobrecarga >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Estadísticas de uso en tiempo real >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Comandos administrativos para gestión >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo - Pool de conexiones de base de datos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ## 📊 Estadísticas del Sistema >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ```yaml >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo Comandos Totales: 60+ >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo Sistemas Integrados: 10 >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo Tipos de Vehículos: 6 ^(Moto, Ranger, Laika, WW, Avion, Barca^) >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo Zonas del Mapa: 20+ >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo Canales Configurables: 8 ^(incluye Canal de Escuadrones^) >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo Tipos de Escuadrones: 2 ^(PvP, PvE^) >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo Detección Automática: ✅ Zona PvP/PvE por escuadrón >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo Compatibilidad: Python 3.13 >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ``` >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ## 📁 Estructura del Build >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ```tree >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ScumBot_Complete/ >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── BunkerAdvice_V2.py          # Bot principal >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── config.py                   # Configuración ^(**EDITAR AQUÍ**^) >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── requirements.txt            # Dependencias Python >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── INSTALL.bat                 # Instalador automático >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── start_bot.bat               # Ejecutar bot >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │ >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── Sistema de Bunkers: >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── database_v2.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   └── bot_status_system.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │ >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── Sistema de Taxi: >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── taxi_system.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── taxi_database.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── taxi_admin.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── banking_system.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   └── welcome_system.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │ >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── Sistema de Mecánico: >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── mechanic_system.py          # Mecánico + Escuadrones >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   └── migrate_mechanic_db.py      # Migración de BD >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │ >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── Sistema Premium: >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── premium_commands.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── premium_exclusive_commands.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── subscription_manager.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   └── shop_config.py >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │ >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── Sistema Rate Limiting: >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── rate_limiter.py               # Core rate limiting >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── rate_limit_admin.py           # Comandos administrativos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── database_pool.py              # Pool de conexiones DB >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   ├── test_rate_limiting.py         # Pruebas unitarias >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │   └── test_bot_integration.py       # Pruebas de integración >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo │ >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── docs/                       # Documentación completa >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── scripts/                    # Scripts de instalación >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── databases/                  # Bases de datos existentes >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ├── logs/                       # Archivos de registro >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo └── backup/                     # Respaldos automáticos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ``` >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ## 🛠️ Resolución de Problemas >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### Error de instalación >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ```batch >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo scripts\install_windows_debug.bat >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ``` >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### Bot se cierra inesperadamente >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo 1. Revisa `logs\bot.log` >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo 2. Verifica token en `config.py` >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo 3. Ejecuta diagnóstico: `debug_user.py` >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### Base de datos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ```python >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo python check_db.py              # Verificar base de datos >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo python migrate_taxi_db.py       # Migrar datos de taxi >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo python migrate_mechanic_db.py   # Migrar sistema de mecánico >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo python test_rate_limiting.py    # Probar sistema de rate limiting >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo python test_bot_integration.py  # Verificar integración completa >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ``` >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ### Tests de Correcciones Críticas ^(NUEVO^) >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ```python >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo python test_button_fixes.py     # Verificar correcciones de botones >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo python test_architecture_fix.py # Verificar arquitectura modular >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo ``` >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo **Estos tests verifican que las correcciones críticas funcionan correctamente** >> "%BUILD_FULL_DIR%\README_BUILD.md"
echo. >> "%BUILD_FULL_DIR%\README_BUILD.md"

echo ✅ README_BUILD.md creado

:: ===========================================
::   CREAR GITIGNORE
:: ===========================================
echo.
echo 📄 Creando .gitignore...

echo # Configuración > "%BUILD_FULL_DIR%\.gitignore"
echo config.py >> "%BUILD_FULL_DIR%\.gitignore"
echo .env >> "%BUILD_FULL_DIR%\.gitignore"
echo. >> "%BUILD_FULL_DIR%\.gitignore"
echo # Base de datos >> "%BUILD_FULL_DIR%\.gitignore"
echo *.db >> "%BUILD_FULL_DIR%\.gitignore"
echo *.db-journal >> "%BUILD_FULL_DIR%\.gitignore"
echo backup/*.db >> "%BUILD_FULL_DIR%\.gitignore"
echo. >> "%BUILD_FULL_DIR%\.gitignore"
echo # Logs >> "%BUILD_FULL_DIR%\.gitignore"
echo logs/*.log >> "%BUILD_FULL_DIR%\.gitignore"
echo *.log >> "%BUILD_FULL_DIR%\.gitignore"
echo. >> "%BUILD_FULL_DIR%\.gitignore"
echo # Python >> "%BUILD_FULL_DIR%\.gitignore"
echo __pycache__/ >> "%BUILD_FULL_DIR%\.gitignore"
echo *.pyc >> "%BUILD_FULL_DIR%\.gitignore"
echo *.pyo >> "%BUILD_FULL_DIR%\.gitignore"
echo .pytest_cache/ >> "%BUILD_FULL_DIR%\.gitignore"

echo ✅ .gitignore creado

:: ===========================================
::   RESUMEN FINAL
:: ===========================================
echo.
echo ===============================================
echo   🎉 BUILD COMPLETO GENERADO EXITOSAMENTE
echo ===============================================
echo.
echo 📁 Ubicación: %BUILD_FULL_DIR%
echo 📊 Timestamp: %BUILD_TIMESTAMP%
echo.
echo 🎮 SISTEMA COMPLETO INCLUIDO:
echo    🏠 Bunkers         📊 Monitor      💎 Premium     🔔 Alertas
echo    🚖 Taxi           🏦 Bancario     🔧 Mecánico    🏆 Escuadrones
echo    ⚙️ Admin          ⚡ RateLimit
echo.
echo 📊 ESTADÍSTICAS DEL BUILD:
echo    ✅ 60+ comandos de Discord funcionales
echo    ✅ 10 sistemas completamente integrados
echo    ✅ 25+ archivos Python principales
echo    ✅ Documentación completa incluida
echo    ✅ Scripts de instalación automática
echo    ✅ Compatible con Python 3.13
echo    ✅ Sistema de escuadrones con detección automática
echo    ✅ Gestión de precios con interfaz interactiva
echo    ✅ **NUEVO:** Errores críticos de botones resueltos
echo    ✅ **NUEVO:** Arquitectura modular corregida
echo.
if defined DISCORD_TOKEN_VALUE (
    echo 🔑 Token: ✅ Configurado automáticamente
) else (
    echo 🔑 Token: ⚠️ Requiere configuración manual en config.py
)
echo.
echo 📋 CONTENIDO PRINCIPAL:
dir "%BUILD_FULL_DIR%" /B | findstr /V "logs backup config scripts docs"
echo.
echo 📁 Carpetas incluidas:
echo    - docs/       (documentación completa)
echo    - scripts/    (instaladores avanzados)
echo    - logs/       (archivos de registro)
echo    - backup/     (respaldos automáticos)
echo    - config/     (configuraciones adicionales)
echo.
echo ===============================================
echo   📦 LISTO PARA DESPLIEGUE COMPLETO
echo ===============================================
echo.
echo 🚀 PARA USAR EN CUALQUIER SERVIDOR:
echo.
echo 1️⃣ Copiar carpeta completa: %BUILD_FULL_DIR%
echo 2️⃣ En el servidor destino ejecutar: INSTALL.bat
if defined DISCORD_TOKEN_VALUE (
    echo 3️⃣ ✅ Token ya configurado - Listo para usar
    echo 4️⃣ Ejecutar directamente: start_bot.bat
) else (
    echo 3️⃣ Configurar token en config.py
    echo 4️⃣ Ejecutar: start_bot.bat
)
echo 5️⃣ Ver docs\ para configuración avanzada
echo.
echo 🎯 CARACTERÍSTICAS ÚNICAS:
echo    ✅ Sistema económico balanceado para progresión rápida
echo    ✅ Timezone automático para Uruguay/Argentina/Brasil
echo    ✅ Interfaz con botones interactivos persistentes
echo    ✅ Multi-servidor con configuración independiente
echo    ✅ Sistema de niveles para conductores de taxi
echo    ✅ Registro y gestión personal de vehículos
echo    ✅ Seguros vehiculares vinculados a vehículos registrados
echo    ✅ Límites configurables por tipo de vehículo
echo    ✅ Diferenciación PVP/PVE con recargos personalizables
echo    ✅ Sistema de escuadrones con creación y unión automática
echo    ✅ Detección automática de zona por membresía de escuadrón
echo    ✅ Gestión de precios con interfaz interactiva ^(botones + selectores^)
echo    ✅ 6 tipos de vehículos soportados ^(eliminado hydroavion^)
echo    ✅ Paneles que se limpian y recrean automáticamente
echo    ✅ Monitoreo en tiempo real de servidores SCUM
echo    ✅ Sistema premium con tienda virtual integrada
echo    ✅ Rate limiting avanzado con cooldowns configurables
echo    ✅ Pool de conexiones de base de datos para mejor rendimiento
echo    ✅ Comandos administrativos para gestión de límites
echo    ✅ Estadísticas de uso en tiempo real
echo    ✅ Prevención automática de spam y sobrecarga
echo    ✅ **NUEVO:** Correcciones críticas de interacciones de botones
echo    ✅ **NUEVO:** Arquitectura modular mejorada ^(bunkers separados^)
echo    ✅ **NUEVO:** Manejo robusto de errores Discord ^(404/400 resueltos^)
echo    ✅ **NUEVO:** Tests automatizados para verificar correcciones
echo.
echo ===============================================
echo.

color 0A
pause