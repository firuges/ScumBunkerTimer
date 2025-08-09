@echo off
title Limpieza Final - SCUM Bot
color 0E

echo ========================================
echo   LIMPIEZA FINAL - SCUM BOT
echo ========================================
echo.
echo Este script eliminará archivos innecesarios:
echo.
echo 📁 Archivos de debug y test
echo 📁 Documentación obsoleta  
echo 📁 Scripts de build antiguos
echo 📁 Archivos de plataformas no usadas
echo.
echo ⚠️  ESTA ACCION NO SE PUEDE DESHACER
echo.
pause
echo.

echo 🧹 Iniciando limpieza...
echo.

:: Archivos de debug y test
echo 📄 Eliminando archivos de debug/test...
del /q debug_*.py 2>nul
del /q test_*.py 2>nul
del /q test_*.bat 2>nul
del /q fix_*.py 2>nul
del /q force_*.py 2>nul
del /q clean_*.py 2>nul
del /q clear_*.py 2>nul
del /q migrate_*.py 2>nul
del /q *_check.py 2>nul
del /q activate_premium.py 2>nul
del /q simple_admin.py 2>nul
del /q help_command_fixed.py 2>nul
del /q update_plan_limits.py 2>nul

:: Scripts de instalación obsoletos
echo 📄 Eliminando instaladores obsoletos...
del /q install_windows_debug.bat 2>nul
del /q install_windows_fixed.bat 2>nul
del /q install_windows_simple.bat 2>nul
del /q build_v2.bat 2>nul
del /q build_linux.sh 2>nul
del /q build.sh 2>nul
del /q run_v2.bat 2>nul
del /q start.bat 2>nul
del /q cleanup.bat 2>nul

:: Documentación obsoleta
echo 📄 Eliminando documentación obsoleta...
del /q README_*.md 2>nul
del /q ACTIONS_VERIFICATION.md 2>nul
del /q BOT_STATUS_GUIDE.md 2>nul
del /q BUILD_SYSTEM_DOCUMENTATION.md 2>nul
del /q COMANDOS_GUIA.md 2>nul
del /q DEPLOY_GUIDE.md 2>nul
del /q FINAL_SOLUTION_COMPLETE.md 2>nul
del /q FLY_DEPLOY.md 2>nul
del /q GUILD_ISOLATION_COMPLETED.md 2>nul
del /q IMPLEMENTACION_COMPLETADA.md 2>nul
del /q INSTALL_FIX_RESOLVED.md 2>nul
del /q MULTIPLE_SERVERS_GUIDE.md 2>nul
del /q PREMIUM_SYSTEM_DOCS.md 2>nul
del /q PUBLIC_BOT_STATUS_GUIDE.md 2>nul
del /q PUBLIC_STATUS_ADMIN_GUIDE.md 2>nul
del /q PYTHON_3.13_SOLUCION.md 2>nul
del /q RENDER_*.md 2>nul
del /q REPLIT_DEPLOY.md 2>nul
del /q WINDOWS_*.md 2>nul

:: Archivos de plataformas no usadas
echo 📄 Eliminando archivos de plataformas no usadas...
del /q Procfile 2>nul
del /q railway.toml 2>nul
del /q render.yaml 2>nul
del /q runtime.txt 2>nul

:: Carpeta legacy completa
echo 📁 Eliminando carpeta legacy...
rmdir /s /q legacy 2>nul

:: Archivos temporales y cache
echo 📄 Limpiando archivos temporales...
del /q *.log 2>nul
rmdir /s /q __pycache__ 2>nul

echo.
echo ✅ Limpieza completada!
echo.
echo 📁 Archivos restantes (esenciales):
echo    ✅ BunkerAdvice_V2.py      - Bot principal
echo    ✅ bot_status_system.py    - Sistema de estado
echo    ✅ database_v2.py          - Base de datos
echo    ✅ premium_*.py            - Sistema premium
echo    ✅ subscription_manager.py - Gestor suscripciones
echo    ✅ bot_starter.py          - Iniciador
echo    ✅ config.py               - Configuración
echo    ✅ build.bat               - Script de build
echo    ✅ requirements.txt        - Dependencias
echo    ✅ guide.html              - Guía web
echo    ✅ .env                    - Variables de entorno
echo    ✅ README.md               - Documentación principal
echo.
pause
