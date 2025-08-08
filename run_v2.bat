@echo off
echo ========================================
echo    SCUM Bunker Bot V2 - Multi-Server
echo ========================================
echo.
echo Seleccione una opcion:
echo 1. Ejecutar Bot V2 (Recomendado)
echo 2. Ejecutar Bot V1 (Legacy)
echo 3. Migrar de V1 a V2
echo 4. Probar funcionalidad V2
echo 5. Ver estado de base de datos
echo 6. Salir
echo.
set /p choice=Ingrese su opcion (1-6): 

if "%choice%"=="1" goto runv2
if "%choice%"=="2" goto runv1
if "%choice%"=="3" goto migrate
if "%choice%"=="4" goto test
if "%choice%"=="5" goto status
if "%choice%"=="6" goto exit

echo Opcion invalida. Intente nuevamente.
pause
goto start

:runv2
echo.
echo Ejecutando Bot V2 con soporte multi-servidor...
echo Presiona Ctrl+C para detener el bot
echo.
python BunkerAdvice_V2.py
pause
goto start

:runv1
echo.
echo Ejecutando Bot V1 (version legacy)...
echo Presiona Ctrl+C para detener el bot
echo.
python BunkerAdvice_Fixed.py
pause
goto start

:migrate
echo.
echo Ejecutando migracion de V1 a V2...
echo.
python migrate_to_v2.py
echo.
echo Migracion completada. Ahora puede usar el Bot V2.
pause
goto start

:test
echo.
echo Ejecutando pruebas de funcionalidad V2...
echo.
python test_v2.py
echo.
echo Pruebas completadas.
pause
goto start

:status
echo.
echo === ESTADO DE BASE DE DATOS ===
echo.
if exist bunkers.db (
    echo [V1] bunkers.db - ENCONTRADA
) else (
    echo [V1] bunkers.db - NO ENCONTRADA
)

if exist bunkers_v2.db (
    echo [V2] bunkers_v2.db - ENCONTRADA
) else (
    echo [V2] bunkers_v2.db - NO ENCONTRADA
)

if exist test_bunkers_v2.db (
    echo [TEST] test_bunkers_v2.db - ENCONTRADA
) else (
    echo [TEST] test_bunkers_v2.db - NO ENCONTRADA
)

echo.
echo === ARCHIVOS DE BACKUP ===
dir bunkers_backup_*.db 2>nul || echo No se encontraron backups
echo.
pause
goto start

:exit
echo.
echo Gracias por usar SCUM Bunker Bot!
exit

:start
cls
goto menu
