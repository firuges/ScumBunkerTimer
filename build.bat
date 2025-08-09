@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: ===========================================
::   SCUM Bunker Timer V2 - Build Generator
:: ===========================================
title SCUM Bunker Timer - Build Generator
color 0B

echo ========================================
echo   SCUM Bunker Timer V2 - Build Generator
echo ========================================
echo.
echo   Genera una carpeta portable para despliegue
echo   Lista para llevar a cualquier servidor
echo.
echo ========================================

:: Cambiar al directorio del script
cd /d "%~dp0"
color 0B

echo ========================================
echo   SCUM Bunker Timer V2 - Build Generator
echo ========================================
echo.
echo   Genera una carpeta portable para despliegue
echo   Lista para llevar a cualquier servidor
echo.
echo ========================================

:: Cambiar al directorio del script
cd /d "%~dp0"

:: Verificar que los archivos fuente existen
echo.
echo 📄 Verificando archivos fuente...

if not exist "BunkerAdvice_V2.py" (
    color 0C
    echo ❌ ERROR: No se encuentra BunkerAdvice_V2.py
    echo.
    echo    Asegúrate de ejecutar este script desde la carpeta
    echo    que contiene todos los archivos del bot.
    echo.
    pause
    exit /b 1
)

if not exist "bot_status_system.py" (
    color 0C
    echo ❌ ERROR: No se encuentra bot_status_system.py
    echo.
    echo    Este archivo es requerido para el sistema de estado del bot.
    echo.
    pause
    exit /b 1
)

echo ✅ Archivos fuente verificados

:: Definir directorio de build
set "BUILD_DIR=build"
set "BUILD_TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "BUILD_TIMESTAMP=%BUILD_TIMESTAMP: =0%"
set "BUILD_FULL_DIR=%BUILD_DIR%\ScumBunkerTimer_%BUILD_TIMESTAMP%"

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
mkdir "%BUILD_FULL_DIR%\installers"

echo ✅ Directorio creado: %BUILD_FULL_DIR%

:: Copiar archivos principales del bot
echo.
echo 📄 Copiando archivos del bot...

copy "BunkerAdvice_V2.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "database_v2.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "bot_status_system.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "server_monitor.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "server_database.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "server_commands.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "premium_*.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "subscription_manager.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "bot_starter.py" "%BUILD_FULL_DIR%\" >nul 2>&1
copy "requirements.txt" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Archivos principales copiados

:: Leer token del .env usando PowerShell
echo.
echo ⚙️ Leyendo configuración del .env...

set "DISCORD_TOKEN_VALUE="
if exist ".env" (
    for /f "usebackq delims=" %%i in (`powershell -command "if (Test-Path '.env') { (Get-Content '.env' | Where-Object { $_ -match '^DISCORD_TOKEN=' }) -replace 'DISCORD_TOKEN=', '' }"`) do (
        set "DISCORD_TOKEN_VALUE=%%i"
    )
)

:: Crear config.py con el token
echo.
echo ⚙️ Creando configuración...

if defined DISCORD_TOKEN_VALUE (
    echo # Configuración del bot Discord > "%BUILD_FULL_DIR%\config.py"
    call echo DISCORD_TOKEN = '%%DISCORD_TOKEN_VALUE%%' >> "%BUILD_FULL_DIR%\config.py"
    echo ✅ Token configurado automáticamente desde .env
) else (
    echo # Configuración del bot Discord > "%BUILD_FULL_DIR%\config.py"
    echo DISCORD_TOKEN = 'TU_TOKEN_AQUI' >> "%BUILD_FULL_DIR%\config.py"
    echo ⚠️ No se pudo leer el token del .env, usando placeholder
)

echo BOT_CREATOR_ID = 418198613210955776  # Tu Discord User ID >> "%BUILD_FULL_DIR%\config.py"
echo. >> "%BUILD_FULL_DIR%\config.py"
echo # Administradores del bot ^(para comandos admin^) >> "%BUILD_FULL_DIR%\config.py"
echo BOT_ADMIN_IDS = [418198613210955776]  # Lista de IDs que pueden usar comandos admin >> "%BUILD_FULL_DIR%\config.py"
echo PREFIX = '/' >> "%BUILD_FULL_DIR%\config.py"
echo DEBUG = True >> "%BUILD_FULL_DIR%\config.py"
echo. >> "%BUILD_FULL_DIR%\config.py"
echo # Base de datos >> "%BUILD_FULL_DIR%\config.py"
echo DATABASE_NAME = 'bunkers_v2.db' >> "%BUILD_FULL_DIR%\config.py"
echo. >> "%BUILD_FULL_DIR%\config.py"
echo # Configuración de logs >> "%BUILD_FULL_DIR%\config.py"
echo LOG_LEVEL = 'INFO' >> "%BUILD_FULL_DIR%\config.py"
echo LOG_FILE = 'logs/bot.log' >> "%BUILD_FULL_DIR%\config.py"

echo ✅ config.py creado

:: Copiar instaladores
echo.
echo 🛠️ Copiando instaladores...

copy "install_windows_simple.bat" "%BUILD_FULL_DIR%\installers\" >nul 2>&1
copy "install_windows_fixed.bat" "%BUILD_FULL_DIR%\installers\" >nul 2>&1
copy "install_windows_debug.bat" "%BUILD_FULL_DIR%\installers\" >nul 2>&1

echo ✅ Instaladores copiados

:: Crear archivo de inicio
echo.
echo 📄 Creando archivos de inicio...

echo @echo off > "%BUILD_FULL_DIR%\start_bot.bat"
echo title SCUM Bunker Timer V2 >> "%BUILD_FULL_DIR%\start_bot.bat"
echo color 0A >> "%BUILD_FULL_DIR%\start_bot.bat"
echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo :: Cambiar al directorio del script >> "%BUILD_FULL_DIR%\start_bot.bat"
echo cd /d "%%~dp0" >> "%BUILD_FULL_DIR%\start_bot.bat"
echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo   SCUM Bunker Timer V2 - Iniciando... >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo 📁 Directorio: %%CD%% >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo 📄 Verificando archivos del bot... >> "%BUILD_FULL_DIR%\start_bot.bat"
echo if not exist "BunkerAdvice_V2.py" ^( >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     color 0C >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo ❌ ERROR: No se encuentra BunkerAdvice_V2.py >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo    Asegúrate de ejecutar start_bot.bat desde >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo    la carpeta que contiene los archivos del bot. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo    Directorio actual: %%CD%% >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     pause >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     exit /b 1 >> "%BUILD_FULL_DIR%\start_bot.bat"
echo ^) >> "%BUILD_FULL_DIR%\start_bot.bat"
echo if not exist "bot_status_system.py" ^( >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     color 0C >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo ❌ ERROR: No se encuentra bot_status_system.py >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo    Este archivo es requerido para el sistema de estado. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     pause >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     exit /b 1 >> "%BUILD_FULL_DIR%\start_bot.bat"
echo ^) >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo ✅ Archivos del bot encontrados >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo 🚀 Iniciando bot... >> "%BUILD_FULL_DIR%\start_bot.bat"
echo echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo python BunkerAdvice_V2.py >> "%BUILD_FULL_DIR%\start_bot.bat"
echo if errorlevel 1 ^( >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo ERROR: El bot se cerro inesperadamente >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo Revisa los logs para mas informacion >> "%BUILD_FULL_DIR%\start_bot.bat"
echo     echo. >> "%BUILD_FULL_DIR%\start_bot.bat"
echo ^) >> "%BUILD_FULL_DIR%\start_bot.bat"
echo pause >> "%BUILD_FULL_DIR%\start_bot.bat"

echo ✅ start_bot.bat creado

:: Crear instalador portable
echo.
echo 📦 Creando instalador portable mejorado...

echo @echo off > "%BUILD_FULL_DIR%\INSTALL.bat"
echo chcp 65001 ^>nul 2^>^&1 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo setlocal enabledelayedexpansion >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo title SCUM Bunker Timer - Instalador Portable >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo color 0A >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ======================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo   SCUM Bunker Timer V2 - Instalador >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ======================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo   Version portable - Compatible Python 3.13 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ======================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo :: Cambiar al directorio del script >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo cd /d "%%~dp0" >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo 📁 Directorio actual: %%CD%% >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo 📄 Verificando archivos necesarios... >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo if not exist "requirements.txt" ^( >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     color 0C >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo ❌ ERROR: No se encuentra requirements.txt >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo    Asegúrate de ejecutar este instalador desde >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo    la carpeta que contiene todos los archivos del bot. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo    Archivos en directorio actual: >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     dir *.py *.txt *.bat >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     pause >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     exit /b 1 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo ^) >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ✅ requirements.txt encontrado >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo 🐍 Verificando Python... >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo python --version ^>nul 2^>^&1 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo if errorlevel 1 ^( >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     color 0C >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo ❌ Python no está instalado >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo    Instala Python desde: https://python.org >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo    Asegúrate de marcar "Add to PATH" >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     pause >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     exit /b 1 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo ^) >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ✅ Python encontrado: >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo python --version >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo 📦 Instalando dependencias... >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo pip install --user -r requirements.txt >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo if errorlevel 1 ^( >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     color 0C >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     echo ❌ Error instalando dependencias >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     pause >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo     exit /b 1 >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo ^) >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ✅ Dependencias instaladas >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo   🎉 INSTALACIÓN COMPLETADA >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo 📋 PRÓXIMOS PASOS: >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
if defined DISCORD_TOKEN_VALUE (
    echo echo ✅ Token ya configurado automáticamente >> "%BUILD_FULL_DIR%\INSTALL.bat"
    echo echo 🚀 Ejecutar: start_bot.bat >> "%BUILD_FULL_DIR%\INSTALL.bat"
) else (
    echo echo 1️⃣ Editar config.py con tu token >> "%BUILD_FULL_DIR%\INSTALL.bat"
    echo echo 2️⃣ Ejecutar start_bot.bat >> "%BUILD_FULL_DIR%\INSTALL.bat"
)
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo ========================================== >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo echo. >> "%BUILD_FULL_DIR%\INSTALL.bat"
echo pause >> "%BUILD_FULL_DIR%\INSTALL.bat"

echo ✅ INSTALL.bat creado

:: Crear README para el build
echo.
echo 📋 Creando documentación...

echo # SCUM Bunker Timer V2 - Build Portable > "%BUILD_FULL_DIR%\README.md"
echo. >> "%BUILD_FULL_DIR%\README.md"
echo ## 🚀 Instalación Rápida >> "%BUILD_FULL_DIR%\README.md"
echo. >> "%BUILD_FULL_DIR%\README.md"
echo 1. **Instalar dependencias:** >> "%BUILD_FULL_DIR%\README.md"
echo    ```batch >> "%BUILD_FULL_DIR%\README.md"
echo    INSTALL.bat >> "%BUILD_FULL_DIR%\README.md"
echo    ``` >> "%BUILD_FULL_DIR%\README.md"
echo. >> "%BUILD_FULL_DIR%\README.md"
if defined DISCORD_TOKEN_VALUE (
    echo 2. **✅ Token ya configurado automáticamente** >> "%BUILD_FULL_DIR%\README.md"
    echo. >> "%BUILD_FULL_DIR%\README.md"
    echo 3. **Ejecutar bot:** >> "%BUILD_FULL_DIR%\README.md"
) else (
    echo 2. **Configurar token:** >> "%BUILD_FULL_DIR%\README.md"
    echo    - Editar `config.py` >> "%BUILD_FULL_DIR%\README.md"
    echo    - Reemplazar `TU_TOKEN_AQUI` con tu token de Discord >> "%BUILD_FULL_DIR%\README.md"
    echo. >> "%BUILD_FULL_DIR%\README.md"
    echo 3. **Ejecutar bot:** >> "%BUILD_FULL_DIR%\README.md"
)
echo    ```batch >> "%BUILD_FULL_DIR%\README.md"
echo    start_bot.bat >> "%BUILD_FULL_DIR%\README.md"
echo    ``` >> "%BUILD_FULL_DIR%\README.md"
echo. >> "%BUILD_FULL_DIR%\README.md"
echo ## 📁 Estructura de Archivos >> "%BUILD_FULL_DIR%\README.md"
echo. >> "%BUILD_FULL_DIR%\README.md"
echo - `BunkerAdvice_V2.py` - Bot principal >> "%BUILD_FULL_DIR%\README.md"
echo - `config.py` - Configuración ^(EDITAR AQUÍ^) >> "%BUILD_FULL_DIR%\README.md"
echo - `requirements.txt` - Dependencias Python >> "%BUILD_FULL_DIR%\README.md"
echo - `INSTALL.bat` - Instalador automático >> "%BUILD_FULL_DIR%\README.md"
echo - `start_bot.bat` - Ejecutar bot >> "%BUILD_FULL_DIR%\README.md"
echo - `logs/` - Archivos de registro >> "%BUILD_FULL_DIR%\README.md"
echo - `installers/` - Instaladores avanzados >> "%BUILD_FULL_DIR%\README.md"
echo. >> "%BUILD_FULL_DIR%\README.md"
echo ## ⚙️ Configuración >> "%BUILD_FULL_DIR%\README.md"
echo. >> "%BUILD_FULL_DIR%\README.md"
if defined DISCORD_TOKEN_VALUE (
    echo ✅ **Token ya configurado automáticamente desde .env** >> "%BUILD_FULL_DIR%\README.md"
    echo. >> "%BUILD_FULL_DIR%\README.md"
    echo El bot está listo para usar directamente después de instalar dependencias. >> "%BUILD_FULL_DIR%\README.md"
) else (
    echo Edita `config.py` y reemplaza: >> "%BUILD_FULL_DIR%\README.md"
    echo ```python >> "%BUILD_FULL_DIR%\README.md"
    echo DISCORD_TOKEN = 'tu_token_real_aqui' >> "%BUILD_FULL_DIR%\README.md"
    echo ``` >> "%BUILD_FULL_DIR%\README.md"
)
echo. >> "%BUILD_FULL_DIR%\README.md"
echo ## 🛠️ Instaladores Avanzados >> "%BUILD_FULL_DIR%\README.md"
echo. >> "%BUILD_FULL_DIR%\README.md"
echo En la carpeta `installers/` encontrarás: >> "%BUILD_FULL_DIR%\README.md"
echo - `install_windows_simple.bat` - Instalación local >> "%BUILD_FULL_DIR%\README.md"
echo - `install_windows_fixed.bat` - Instalación como servicio >> "%BUILD_FULL_DIR%\README.md"
echo - `install_windows_debug.bat` - Diagnóstico >> "%BUILD_FULL_DIR%\README.md"
echo. >> "%BUILD_FULL_DIR%\README.md"
echo ## 📊 Características >> "%BUILD_FULL_DIR%\README.md"
echo. >> "%BUILD_FULL_DIR%\README.md"
echo ✅ Compatible con Python 3.13 >> "%BUILD_FULL_DIR%\README.md"
echo ✅ 13 comandos de Discord funcionales >> "%BUILD_FULL_DIR%\README.md"
echo ✅ Sistema de bunkers SCUM >> "%BUILD_FULL_DIR%\README.md"
echo ✅ Base de datos SQLite >> "%BUILD_FULL_DIR%\README.md"
echo ✅ Sistema premium integrado >> "%BUILD_FULL_DIR%\README.md"
echo ✅ Logs automáticos >> "%BUILD_FULL_DIR%\README.md"

echo ✅ README.md creado

:: Copiar documentación adicional
echo.
echo 📚 Copiando documentación adicional...

if exist "guide.html" copy "guide.html" "%BUILD_FULL_DIR%\" >nul 2>&1
if exist "presentation.html" copy "presentation.html" "%BUILD_FULL_DIR%\" >nul 2>&1
if exist "PYTHON_3.13_SOLUCION.md" copy "PYTHON_3.13_SOLUCION.md" "%BUILD_FULL_DIR%\" >nul 2>&1

echo ✅ Documentación adicional copiada

:: Crear archivo .gitignore para el build
echo.
echo 📄 Creando .gitignore...

echo # Archivos de configuración > "%BUILD_FULL_DIR%\.gitignore"
echo config.py >> "%BUILD_FULL_DIR%\.gitignore"
echo .env >> "%BUILD_FULL_DIR%\.gitignore"
echo. >> "%BUILD_FULL_DIR%\.gitignore"
echo # Base de datos >> "%BUILD_FULL_DIR%\.gitignore"
echo *.db >> "%BUILD_FULL_DIR%\.gitignore"
echo *.db-journal >> "%BUILD_FULL_DIR%\.gitignore"
echo. >> "%BUILD_FULL_DIR%\.gitignore"
echo # Logs >> "%BUILD_FULL_DIR%\.gitignore"
echo logs/*.log >> "%BUILD_FULL_DIR%\.gitignore"
echo *.log >> "%BUILD_FULL_DIR%\.gitignore"
echo. >> "%BUILD_FULL_DIR%\.gitignore"
echo # Python >> "%BUILD_FULL_DIR%\.gitignore"
echo __pycache__/ >> "%BUILD_FULL_DIR%\.gitignore"
echo *.pyc >> "%BUILD_FULL_DIR%\.gitignore"
echo *.pyo >> "%BUILD_FULL_DIR%\.gitignore"
echo. >> "%BUILD_FULL_DIR%\.gitignore"
echo # Backups >> "%BUILD_FULL_DIR%\.gitignore"
echo backup/*.db >> "%BUILD_FULL_DIR%\.gitignore"

echo ✅ .gitignore creado

:: Mostrar resumen del build
echo.
echo ===============================================
echo   🎉 BUILD GENERADO EXITOSAMENTE
echo ===============================================
echo.
echo 📁 Ubicación: %BUILD_FULL_DIR%
echo 📊 Timestamp: %BUILD_TIMESTAMP%
echo.
if defined DISCORD_TOKEN_VALUE (
    echo 🔑 Token: ✅ Configurado automáticamente
) else (
    echo 🔑 Token: ⚠️ Requiere configuración manual
)
echo.
echo 📋 CONTENIDO DEL BUILD:
echo.
dir "%BUILD_FULL_DIR%" /B | findstr /V "logs backup config"
echo.
echo 📁 Carpetas:
echo    - logs/     (para archivos de registro)
echo    - backup/   (para respaldos de BD)
echo    - config/   (configuraciones adicionales)
echo    - installers/ (instaladores avanzados)
echo.
echo ===============================================
echo   📦 LISTO PARA DESPLIEGUE
echo ===============================================
echo.
echo 🚀 PARA USAR EN OTRO SERVIDOR:
echo.
echo 1️⃣ Copiar toda la carpeta: %BUILD_FULL_DIR%
echo 2️⃣ En el servidor destino, ejecutar: INSTALL.bat
if defined DISCORD_TOKEN_VALUE (
    echo 3️⃣ ✅ Token ya configurado automáticamente
    echo 4️⃣ Ejecutar directamente: start_bot.bat
) else (
    echo 3️⃣ Configurar token en config.py
    echo 4️⃣ Ejecutar: start_bot.bat
)
echo.
echo ===============================================
echo.

color 0A
pause
