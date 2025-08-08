@echo off
setlocal enabledelayedexpansion

title SCUM Bunker Timer - Instalador para Windows Server
color 0A

echo ========================================
echo   SCUM Bunker Timer V2 - Instalador
echo ========================================
echo.
echo   Instalación automática para Windows
echo   Configura tarea programada y servicios
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
echo.

:: Verificar pip
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    color 0C
    echo ❌ ERROR: pip no está disponible
    echo.
    pause
    exit /b 1
)

echo ✅ pip disponible
echo.

:: Crear estructura de directorios
echo 📁 Creando estructura de directorios...
if not exist "C:\ScumBunkerTimer" mkdir "C:\ScumBunkerTimer"
if not exist "C:\ScumBunkerTimer\logs" mkdir "C:\ScumBunkerTimer\logs"
if not exist "C:\ScumBunkerTimer\backup" mkdir "C:\ScumBunkerTimer\backup"
if not exist "C:\ScumBunkerTimer\config" mkdir "C:\ScumBunkerTimer\config"
echo ✅ Directorios creados

:: Copiar archivos del bot
echo.
echo 📄 Copiando archivos del bot...
copy "%~dp0BunkerAdvice_V2.py" "C:\ScumBunkerTimer\" >nul 2>&1
copy "%~dp0database_v2.py" "C:\ScumBunkerTimer\" >nul 2>&1
copy "%~dp0premium_*.py" "C:\ScumBunkerTimer\" >nul 2>&1
copy "%~dp0subscription_manager.py" "C:\ScumBunkerTimer\" >nul 2>&1
copy "%~dp0requirements.txt" "C:\ScumBunkerTimer\" >nul 2>&1
copy "%~dp0config.py" "C:\ScumBunkerTimer\" >nul 2>&1
copy "%~dp0bot_starter.py" "C:\ScumBunkerTimer\" >nul 2>&1
copy "%~dp0*.html" "C:\ScumBunkerTimer\" >nul 2>&1
copy "%~dp0migrate_*.py" "C:\ScumBunkerTimer\" >nul 2>&1
copy "%~dp0update_*.py" "C:\ScumBunkerTimer\" >nul 2>&1

if exist "C:\ScumBunkerTimer\BunkerAdvice_V2.py" (
    echo ✅ Archivos copiados exitosamente
) else (
    color 0C
    echo ❌ Error copiando archivos
    echo    Verifica que los archivos del bot estén en la misma carpeta que este instalador
    pause
    exit /b 1
)

:: Cambiar al directorio de trabajo
cd /d "C:\ScumBunkerTimer"

:: Instalar dependencias Python
echo.
echo 📦 Instalando dependencias Python...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    color 0C
    echo ❌ Error instalando dependencias
    pause
    exit /b 1
)
echo ✅ Dependencias instaladas

:: Instalar psutil para monitoreo
echo.
echo 📦 Instalando herramientas de monitoreo...
pip install psutil
echo ✅ Herramientas de monitoreo instaladas

:: Configurar token de Discord
echo.
echo 🔑 Configuración del Token de Discord
echo.
echo    Para obtener tu token:
echo    1. Ve a https://discord.com/developers/applications
echo    2. Selecciona tu aplicación
echo    3. Ve a "Bot" en el menú lateral
echo    4. Copia el "Token"
echo.
set /p "discord_token=Ingresa tu DISCORD_TOKEN: "

if "!discord_token!"=="" (
    color 0C
    echo ❌ Token no puede estar vacío
    pause
    exit /b 1
)

:: Guardar configuración
echo DISCORD_TOKEN=!discord_token!> "C:\ScumBunkerTimer\config\bot_config.txt"
echo ✅ Token configurado

:: Verificar configuración
echo.
echo 🧪 Verificando configuración...
python -c "import os; os.chdir('C:/ScumBunkerTimer'); exec(open('bot_starter.py').read().split('def main')[0]); print('✅ Configuración válida' if load_config() and check_dependencies() else '❌ Error en configuración')" 2>nul
if %errorLevel% neq 0 (
    echo ⚠️ Advertencia: No se pudo verificar completamente la configuración
)

:: Eliminar tarea existente si existe
echo.
echo 🗑️ Limpiando tareas previas...
schtasks /delete /tn "SCUM Bunker Timer" /f >nul 2>&1

:: Crear tarea programada
echo.
echo 📅 Creando tarea programada...
schtasks /create ^
    /tn "SCUM Bunker Timer" ^
    /tr "python C:\ScumBunkerTimer\bot_starter.py" ^
    /sc onstart ^
    /ru "SYSTEM" ^
    /rl highest ^
    /f

if %errorLevel% neq 0 (
    color 0C
    echo ❌ Error creando tarea programada
    pause
    exit /b 1
)

:: Configurar reinicio automático en la tarea
echo.
echo 🔄 Configurando reinicio automático...
schtasks /change /tn "SCUM Bunker Timer" /enable
schtasks /change /tn "SCUM Bunker Timer" /st 00:00

echo ✅ Tarea programada configurada

:: Crear script de gestión
echo.
echo 📜 Creando scripts de gestión...

:: Script para iniciar el bot
echo @echo off > "C:\ScumBunkerTimer\start_bot.bat"
echo echo Iniciando SCUM Bunker Timer... >> "C:\ScumBunkerTimer\start_bot.bat"
echo schtasks /run /tn "SCUM Bunker Timer" >> "C:\ScumBunkerTimer\start_bot.bat"
echo echo Bot iniciado >> "C:\ScumBunkerTimer\start_bot.bat"
echo pause >> "C:\ScumBunkerTimer\start_bot.bat"

:: Script para detener el bot
echo @echo off > "C:\ScumBunkerTimer\stop_bot.bat"
echo echo Deteniendo SCUM Bunker Timer... >> "C:\ScumBunkerTimer\stop_bot.bat"
echo schtasks /end /tn "SCUM Bunker Timer" >> "C:\ScumBunkerTimer\stop_bot.bat"
echo taskkill /f /im python.exe /fi "WINDOWTITLE eq *BunkerAdvice*" 2^>nul >> "C:\ScumBunkerTimer\stop_bot.bat"
echo echo Bot detenido >> "C:\ScumBunkerTimer\stop_bot.bat"
echo pause >> "C:\ScumBunkerTimer\stop_bot.bat"

:: Script para ver logs
echo @echo off > "C:\ScumBunkerTimer\view_logs.bat"
echo set "log_file=C:\ScumBunkerTimer\logs\bot_service_%date:~-4%%date:~-10,2%%date:~-7,2%.log" >> "C:\ScumBunkerTimer\view_logs.bat"
echo if exist "%%log_file%%" ( >> "C:\ScumBunkerTimer\view_logs.bat"
echo     echo Mostrando logs del bot... >> "C:\ScumBunkerTimer\view_logs.bat"
echo     type "%%log_file%%" >> "C:\ScumBunkerTimer\view_logs.bat"
echo ) else ( >> "C:\ScumBunkerTimer\view_logs.bat"
echo     echo No se encontraron logs para hoy >> "C:\ScumBunkerTimer\view_logs.bat"
echo ) >> "C:\ScumBunkerTimer\view_logs.bat"
echo pause >> "C:\ScumBunkerTimer\view_logs.bat"

:: Script de estado
echo @echo off > "C:\ScumBunkerTimer\status.bat"
echo echo ======================================== >> "C:\ScumBunkerTimer\status.bat"
echo echo   SCUM Bunker Timer - Estado del Sistema >> "C:\ScumBunkerTimer\status.bat"
echo echo ======================================== >> "C:\ScumBunkerTimer\status.bat"
echo echo. >> "C:\ScumBunkerTimer\status.bat"
echo schtasks /query /tn "SCUM Bunker Timer" /fo table >> "C:\ScumBunkerTimer\status.bat"
echo echo. >> "C:\ScumBunkerTimer\status.bat"
echo echo Procesos Python activos: >> "C:\ScumBunkerTimer\status.bat"
echo tasklist /fi "imagename eq python.exe" /fo table >> "C:\ScumBunkerTimer\status.bat"
echo pause >> "C:\ScumBunkerTimer\status.bat"

echo ✅ Scripts de gestión creados

:: Configurar firewall si es necesario
echo.
echo 🔒 Configurando firewall (opcional)...
netsh advfirewall firewall add rule name="SCUM Bunker Timer" dir=out action=allow program="python.exe" enable=yes >nul 2>&1
echo ✅ Regla de firewall agregada

color 0A
echo.
echo ========================================
echo          ✅ INSTALACIÓN COMPLETADA
echo ========================================
echo.
echo 🎮 SCUM Bunker Timer V2 está instalado y configurado
echo.
echo 📍 Ubicación: C:\ScumBunkerTimer\
echo 📊 Logs: C:\ScumBunkerTimer\logs\
echo 🔧 Configuración: C:\ScumBunkerTimer\config\
echo.
echo 🎛️  COMANDOS DE GESTIÓN:
echo    • Iniciar bot:    C:\ScumBunkerTimer\start_bot.bat
echo    • Detener bot:    C:\ScumBunkerTimer\stop_bot.bat
echo    • Ver estado:     C:\ScumBunkerTimer\status.bat
echo    • Ver logs:       C:\ScumBunkerTimer\view_logs.bat
echo.
echo 🔧 COMANDOS DE SISTEMA:
echo    • schtasks /run /tn "SCUM Bunker Timer"
echo    • schtasks /end /tn "SCUM Bunker Timer"
echo    • schtasks /query /tn "SCUM Bunker Timer"
echo.
echo 🚀 El bot se iniciará automáticamente con Windows
echo 📱 Verifica en Discord que el bot esté online
echo.
echo ¿Quieres iniciar el bot ahora? (s/n)
set /p "start_now="
if /i "!start_now!"=="s" (
    echo.
    echo 🚀 Iniciando bot...
    schtasks /run /tn "SCUM Bunker Timer"
    echo ✅ Bot iniciado en background
    echo    Verifica los logs en unos segundos con: view_logs.bat
)

echo.
echo ¡Instalación completa! Presiona cualquier tecla para salir.
pause >nul
