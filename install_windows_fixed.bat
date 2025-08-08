@echo off
setlocal enabledelayedexpansion

title SCUM Bunker Timer - Instalador Corregido
color 0A

echo ========================================
echo   SCUM Bunker Timer V2 - Instalador
echo ========================================
echo.
echo   INSTALADOR CORREGIDO PARA PYTHON 3.13
echo   Soluciona problemas de compilacion
echo.
echo ========================================

:: Verificar permisos de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    color 0C
    echo.
    echo ❌ ERROR: Este script requiere permisos de administrador
    echo.
    echo    Para ejecutar correctamente:
    echo    1. Haz clic derecho en este archivo
    echo    2. Selecciona "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

echo ✅ Permisos de administrador verificados
echo.

:: Verificar Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    color 0C
    echo ❌ ERROR: Python no está instalado o no está en PATH
    echo.
    echo    Instala Python desde: https://python.org
    echo    Asegúrate de marcar "Add to PATH" durante la instalación
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado:
python --version

:: Verificar versión de Python
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo    Versión detectada: %PYTHON_VERSION%
echo.

:: Crear estructura de directorios
set "INSTALL_DIR=C:\ScumBunkerTimer"
echo 📁 Creando estructura de directorios...

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"
if not exist "%INSTALL_DIR%\backup" mkdir "%INSTALL_DIR%\backup"
if not exist "%INSTALL_DIR%\config" mkdir "%INSTALL_DIR%\config"

echo ✅ Directorios creados

:: Verificar que los archivos fuente existen
echo.
echo 📄 Verificando archivos del bot...

if not exist "BunkerAdvice_V2.py" (
    color 0C
    echo ❌ ERROR: No se encuentra BunkerAdvice_V2.py
    echo.
    echo    Asegúrate de ejecutar este instalador desde la carpeta
    echo    que contiene todos los archivos del bot.
    echo.
    pause
    exit /b 1
)

echo ✅ Archivos fuente verificados

:: Copiar archivos del bot
echo.
echo 📄 Copiando archivos del bot...
copy "BunkerAdvice_V2.py" "%INSTALL_DIR%\" >nul 2>&1
copy "database_v2.py" "%INSTALL_DIR%\" >nul 2>&1
copy "premium_*.py" "%INSTALL_DIR%\" >nul 2>&1
copy "subscription_manager.py" "%INSTALL_DIR%\" >nul 2>&1
copy "config.py" "%INSTALL_DIR%\" >nul 2>&1
copy "bot_starter.py" "%INSTALL_DIR%\" >nul 2>&1
copy "*.html" "%INSTALL_DIR%\" >nul 2>&1
copy "migrate_*.py" "%INSTALL_DIR%\" >nul 2>&1
copy "update_*.py" "%INSTALL_DIR%\" >nul 2>&1

:: Crear requirements.txt optimizado para Python 3.13
echo.
echo 📦 Creando requirements.txt optimizado...
echo discord.py==2.4.0 > "%INSTALL_DIR%\requirements.txt"
echo python-dotenv==1.0.1 >> "%INSTALL_DIR%\requirements.txt"
echo aiosqlite==0.19.0 >> "%INSTALL_DIR%\requirements.txt"
echo psutil==5.9.8 >> "%INSTALL_DIR%\requirements.txt"
echo python-dateutil==2.9.0 >> "%INSTALL_DIR%\requirements.txt"

echo ✅ Archivos copiados exitosamente

:: Cambiar al directorio de instalación
cd /d "%INSTALL_DIR%"

:: Actualizar pip primero
echo.
echo 🔧 Actualizando pip...
python -m pip install --upgrade pip --quiet

:: Instalar dependencias con manejo de errores
echo.
echo 📦 Instalando dependencias Python (versiones compatibles)...
echo    Esto puede tomar unos minutos...

:: Instalar dependencias una por una para mejor control
echo.
echo [1/5] Instalando discord.py 2.4.0...
python -m pip install discord.py==2.4.0 --quiet
if %errorLevel% neq 0 (
    echo ⚠️ Intentando con una versión alternativa...
    python -m pip install discord.py --quiet
)

echo [2/5] Instalando python-dotenv...
python -m pip install python-dotenv==1.0.1 --quiet

echo [3/5] Instalando aiosqlite...
python -m pip install aiosqlite==0.19.0 --quiet

echo [4/5] Instalando psutil...
python -m pip install psutil==5.9.8 --quiet

echo [5/5] Instalando python-dateutil...
python -m pip install python-dateutil==2.9.0 --quiet

:: Verificar instalación
echo.
echo 🧪 Verificando instalación...
python -c "import discord; print(f'✅ discord.py {discord.__version__} OK')" 2>nul
if %errorLevel% neq 0 (
    echo ❌ Error verificando discord.py
    echo.
    echo Intentando solución alternativa...
    python -m pip install discord.py --force-reinstall --quiet
)

python -c "import aiosqlite; print('✅ aiosqlite OK')" 2>nul
python -c "import psutil; print('✅ psutil OK')" 2>nul

echo ✅ Dependencias instaladas correctamente

:: Configurar token de Discord
echo.
echo ========================================
echo   CONFIGURACION DEL TOKEN DISCORD
echo ========================================
echo.
echo Para obtener tu token:
echo 1. Ve a https://discord.com/developers/applications
echo 2. Selecciona tu aplicación (o crea una nueva)
echo 3. Ve a "Bot" en el menú lateral
echo 4. Copia el "Token"
echo.
set /p "discord_token=Ingresa tu DISCORD_TOKEN: "

if "!discord_token!"=="" (
    color 0C
    echo ❌ Token no puede estar vacío
    pause
    exit /b 1
)

:: Guardar configuración
echo DISCORD_TOKEN=!discord_token!> "%INSTALL_DIR%\config\bot_config.txt"
echo ✅ Token configurado

:: Prueba rápida de configuración
echo.
echo 🧪 Probando configuración del bot...
python -c "
import os
import sys
sys.path.insert(0, r'%INSTALL_DIR%')

# Cargar configuración
try:
    with open(r'%INSTALL_DIR%\config\bot_config.txt', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    # Verificar importaciones críticas
    import discord
    import aiosqlite
    import database_v2
    
    print('✅ Configuración válida')
    print(f'✅ Discord.py: {discord.__version__}')
except Exception as e:
    print(f'⚠️ Advertencia: {e}')
" 2>nul

:: Crear scripts de gestión mejorados
echo.
echo 📜 Creando scripts de gestión...

:: Script de inicio mejorado
echo @echo off > "%INSTALL_DIR%\start_bot.bat"
echo title SCUM Bunker Timer >> "%INSTALL_DIR%\start_bot.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%\start_bot.bat"
echo echo Iniciando SCUM Bunker Timer... >> "%INSTALL_DIR%\start_bot.bat"
echo python bot_starter.py >> "%INSTALL_DIR%\start_bot.bat"
echo pause >> "%INSTALL_DIR%\start_bot.bat"

:: Script de parada
echo @echo off > "%INSTALL_DIR%\stop_bot.bat"
echo title Detener SCUM Bunker Timer >> "%INSTALL_DIR%\stop_bot.bat"
echo echo Deteniendo SCUM Bunker Timer... >> "%INSTALL_DIR%\stop_bot.bat"
echo taskkill /f /im python.exe /fi "WINDOWTITLE eq *SCUM*" 2^>nul >> "%INSTALL_DIR%\stop_bot.bat"
echo echo Bot detenido >> "%INSTALL_DIR%\stop_bot.bat"
echo timeout /t 3 /nobreak >> "%INSTALL_DIR%\stop_bot.bat"

:: Script de estado
echo @echo off > "%INSTALL_DIR%\status_bot.bat"
echo title Estado SCUM Bunker Timer >> "%INSTALL_DIR%\status_bot.bat"
echo echo ======================================== >> "%INSTALL_DIR%\status_bot.bat"
echo echo   SCUM Bunker Timer - Estado del Sistema >> "%INSTALL_DIR%\status_bot.bat"
echo echo ======================================== >> "%INSTALL_DIR%\status_bot.bat"
echo echo. >> "%INSTALL_DIR%\status_bot.bat"
echo echo Procesos Python activos: >> "%INSTALL_DIR%\status_bot.bat"
echo tasklist /fi "imagename eq python.exe" /fo table 2^>nul >> "%INSTALL_DIR%\status_bot.bat"
echo echo. >> "%INSTALL_DIR%\status_bot.bat"
echo echo Presiona cualquier tecla para continuar... >> "%INSTALL_DIR%\status_bot.bat"
echo pause ^>nul >> "%INSTALL_DIR%\status_bot.bat"

:: Script para ver logs
echo @echo off > "%INSTALL_DIR%\view_logs.bat"
echo title Logs SCUM Bunker Timer >> "%INSTALL_DIR%\view_logs.bat"
echo set "today=%%date:~-4%%%%date:~-10,2%%%%date:~-7,2%%" >> "%INSTALL_DIR%\view_logs.bat"
echo set "log_file=%INSTALL_DIR%\logs\bot_service_%%today%%.log" >> "%INSTALL_DIR%\view_logs.bat"
echo if exist "%%log_file%%" ( >> "%INSTALL_DIR%\view_logs.bat"
echo     type "%%log_file%%" >> "%INSTALL_DIR%\view_logs.bat"
echo ) else ( >> "%INSTALL_DIR%\view_logs.bat"
echo     echo No hay logs para hoy >> "%INSTALL_DIR%\view_logs.bat"
echo ) >> "%INSTALL_DIR%\view_logs.bat"
echo pause >> "%INSTALL_DIR%\view_logs.bat"

:: Script de prueba rápida
echo @echo off > "%INSTALL_DIR%\test_bot.bat"
echo title Prueba SCUM Bunker Timer >> "%INSTALL_DIR%\test_bot.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%\test_bot.bat"
echo echo Probando bot por 30 segundos... >> "%INSTALL_DIR%\test_bot.bat"
echo timeout /t 5 /nobreak >> "%INSTALL_DIR%\test_bot.bat"
echo start /min python BunkerAdvice_V2.py >> "%INSTALL_DIR%\test_bot.bat"
echo echo Bot iniciado en segundo plano >> "%INSTALL_DIR%\test_bot.bat"
echo echo Verifica Discord en 10-15 segundos >> "%INSTALL_DIR%\test_bot.bat"
echo pause >> "%INSTALL_DIR%\test_bot.bat"

echo ✅ Scripts de gestión creados

:: Eliminar tarea programada anterior si existe
echo.
echo 🗑️ Limpiando configuraciones anteriores...
schtasks /delete /tn "SCUM Bunker Timer" /f >nul 2>&1
schtasks /delete /tn "ScumBunkerTimer" /f >nul 2>&1

:: Crear tarea programada
echo.
echo 📅 Creando tarea programada...
schtasks /create ^
    /tn "SCUM Bunker Timer" ^
    /tr "\"%INSTALL_DIR%\start_bot.bat\"" ^
    /sc onstart ^
    /ru "SYSTEM" ^
    /rl highest ^
    /f

if %errorLevel% equ 0 (
    echo ✅ Tarea programada creada correctamente
    
    :: Configurar para que no se cierre
    schtasks /change /tn "SCUM Bunker Timer" /enable
    echo ✅ Tarea programada habilitada
) else (
    echo ⚠️ Advertencia: No se pudo crear la tarea programada
    echo    Puedes iniciar el bot manualmente con start_bot.bat
)

color 0A
echo.
echo ========================================
echo          ✅ INSTALACIÓN COMPLETADA
echo ========================================
echo.
echo 🎮 SCUM Bunker Timer V2 instalado correctamente
echo.
echo 📍 Ubicación: %INSTALL_DIR%
echo 📊 Logs: %INSTALL_DIR%\logs\
echo 🔧 Config: %INSTALL_DIR%\config\bot_config.txt
echo.
echo 🎛️  SCRIPTS DE GESTIÓN:
echo    🚀 start_bot.bat     - Iniciar bot
echo    🛑 stop_bot.bat      - Detener bot
echo    📊 status_bot.bat    - Ver estado
echo    📄 view_logs.bat     - Ver logs
echo    🧪 test_bot.bat      - Prueba rápida
echo.
echo 💡 PRÓXIMOS PASOS:
echo    1. El bot se iniciará automáticamente con Windows
echo    2. Usa test_bot.bat para una prueba rápida
echo    3. Verifica en Discord que el bot esté online
echo    4. Usa el comando /ba_help en Discord
echo.
set /p "start_test=¿Quieres hacer una prueba rápida ahora? (s/n): "
if /i "!start_test!"=="s" (
    echo.
    echo 🧪 Iniciando prueba...
    start "" "%INSTALL_DIR%\test_bot.bat"
    echo.
    echo ✅ Bot iniciado para prueba
    echo    Verifica Discord en 10-15 segundos
    echo    El bot aparecerá como 'Online'
)

echo.
echo 🎉 ¡Instalación completada exitosamente!
echo    Presiona cualquier tecla para salir
pause >nul
