# 🖥️ Deploy en Windows Server con Tarea Programada - SCUM Bunker Timer V2

## 🎯 ¿Por qué Tarea Programada?

- ✅ **Inicio automático** con Windows
- ✅ **Reinicio automático** si falla
- ✅ **Control total** del proceso
- ✅ **Logs detallados** en Windows Event Log
- ✅ **Sin dependencias adicionales**
- ✅ **Fácil gestión** desde interfaz gráfica

## 📋 Requisitos Previos

- Windows Server o Windows 10/11
- Python 3.8+ instalado
- Acceso administrativo
- IIS (opcional, solo para servir archivos HTML)

## 🚀 Paso a Paso

### 1. **Preparar Directorio de Aplicación**

```batch
# Crear directorio principal
mkdir C:\ScumBunkerTimer
cd C:\ScumBunkerTimer

# Crear subdirectorios
mkdir logs
mkdir backup
mkdir config
```

### 2. **Copiar Archivos del Bot**

Copiar todos los archivos del proyecto a `C:\ScumBunkerTimer\`:
- BunkerAdvice_V2.py
- database_v2.py
- premium_*.py
- subscription_manager.py
- requirements.txt
- config.py
- guide.html
- presentation.html
- Todos los archivos migrate_*.py

### 3. **Instalar Dependencias**

```batch
cd C:\ScumBunkerTimer
pip install -r requirements.txt
```

### 4. **Configurar Variables de Entorno**

Opción A - Variables del Sistema:
```batch
setx DISCORD_TOKEN "TU_TOKEN_AQUI" /M
```

Opción B - Archivo de configuración:
```
# Crear C:\ScumBunkerTimer\config\bot_config.txt
DISCORD_TOKEN=TU_TOKEN_AQUI
```

## 📝 Scripts de Gestión

### Script de Inicio (bot_starter.py)

```python
import os
import sys
import time
import logging
import subprocess
from datetime import datetime
import traceback

# Configurar directorio base
BASE_DIR = r"C:\ScumBunkerTimer"
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar logging
log_file = os.path.join(LOG_DIR, f"bot_service_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def load_config():
    """Cargar configuración desde archivo o variables de entorno"""
    config_file = os.path.join(BASE_DIR, "config", "bot_config.txt")
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        logging.info("✅ Configuración cargada desde archivo")
    else:
        logging.info("ℹ️ Usando variables de entorno del sistema")

def start_bot():
    """Iniciar el bot con gestión de errores"""
    bot_script = os.path.join(BASE_DIR, "BunkerAdvice_V2.py")
    
    if not os.path.exists(bot_script):
        logging.error(f"❌ No se encuentra el bot en: {bot_script}")
        return False
    
    try:
        logging.info("🚀 Iniciando SCUM Bunker Timer...")
        
        # Cambiar al directorio del bot
        os.chdir(BASE_DIR)
        
        # Ejecutar el bot
        process = subprocess.Popen(
            [sys.executable, bot_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        logging.info(f"✅ Bot iniciado con PID: {process.pid}")
        
        # Monitorear el proceso
        while True:
            return_code = process.poll()
            if return_code is not None:
                # El proceso terminó
                stdout, stderr = process.communicate()
                logging.error(f"❌ Bot terminó con código: {return_code}")
                if stdout:
                    logging.info(f"STDOUT: {stdout}")
                if stderr:
                    logging.error(f"STDERR: {stderr}")
                return False
            time.sleep(5)  # Verificar cada 5 segundos
            
    except Exception as e:
        logging.error(f"❌ Error iniciando bot: {e}")
        logging.error(traceback.format_exc())
        return False

def main():
    """Función principal con reinicio automático"""
    load_config()
    
    max_restarts = 10
    restart_count = 0
    
    while restart_count < max_restarts:
        logging.info(f"🔄 Intento de inicio #{restart_count + 1}")
        
        if start_bot():
            logging.info("✅ Bot funcionando correctamente")
            restart_count = 0  # Reset counter on success
        else:
            restart_count += 1
            if restart_count < max_restarts:
                wait_time = min(60 * restart_count, 300)  # Max 5 minutos
                logging.warning(f"⏳ Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)
            else:
                logging.error("❌ Máximo de reintentos alcanzado. Deteniendo servicio.")
                break

if __name__ == "__main__":
    main()
```

### Script de Instalación (install.bat)

```batch
@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   SCUM Bunker Timer - Instalador
echo ========================================
echo.

:: Verificar permisos de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ ERROR: Este script requiere permisos de administrador
    echo    Haz clic derecho y selecciona "Ejecutar como administrador"
    pause
    exit /b 1
)

:: Crear directorios
echo 📁 Creando directorios...
mkdir C:\ScumBunkerTimer 2>nul
mkdir C:\ScumBunkerTimer\logs 2>nul
mkdir C:\ScumBunkerTimer\backup 2>nul
mkdir C:\ScumBunkerTimer\config 2>nul

:: Copiar archivos
echo 📄 Copiando archivos del bot...
copy "%~dp0*" "C:\ScumBunkerTimer\" >nul 2>&1

:: Instalar dependencias
echo 📦 Instalando dependencias Python...
cd C:\ScumBunkerTimer
pip install -r requirements.txt

:: Configurar token
echo.
echo 🔑 Configuración del Token de Discord:
set /p "discord_token=Ingresa tu DISCORD_TOKEN: "
echo DISCORD_TOKEN=!discord_token!> C:\ScumBunkerTimer\config\bot_config.txt

:: Crear tarea programada
echo 📅 Creando tarea programada...
schtasks /create /tn "SCUM Bunker Timer" /tr "python C:\ScumBunkerTimer\bot_starter.py" /sc onstart /ru "SYSTEM" /rl highest /f

:: Configurar tarea para reinicio automático
schtasks /change /tn "SCUM Bunker Timer" /st 00:00 /ri 60 /du 24:00

echo.
echo ✅ Instalación completada exitosamente!
echo.
echo 🎮 Para gestionar el bot:
echo    • Iniciar: schtasks /run /tn "SCUM Bunker Timer"
echo    • Detener: schtasks /end /tn "SCUM Bunker Timer"
echo    • Estado: schtasks /query /tn "SCUM Bunker Timer"
echo.
echo 📊 Logs disponibles en: C:\ScumBunkerTimer\logs\
echo.
pause
```

## 🔧 Configuración de Tarea Programada

### Método 1: Script Automático (Recomendado)
Ejecutar `install.bat` como administrador.

### Método 2: Manual (Interfaz Gráfica)

1. **Abrir Programador de Tareas**
   - `Windows + R` → `taskschd.msc`

2. **Crear Tarea Básica**
   - Nombre: `SCUM Bunker Timer`
   - Descripción: `Bot de Discord para gestión de bunkers SCUM`

3. **Desencadenador**
   - Tipo: `Al iniciar el sistema`
   - Retrasar: `1 minuto`

4. **Acción**
   - Programa: `python`
   - Argumentos: `C:\ScumBunkerTimer\bot_starter.py`
   - Directorio: `C:\ScumBunkerTimer`

5. **Configuración Avanzada**
   - ✅ Ejecutar con privilegios más altos
   - ✅ Reiniciar si falla cada: `5 minutos`
   - ✅ Intentar reiniciar hasta: `3 veces`
   - ✅ Si la tarea ya se está ejecutando: `No iniciar nueva instancia`

## 🌐 Configurar IIS para Archivos HTML (Opcional)

### 1. **Instalar IIS**
```powershell
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServer
Enable-WindowsOptionalFeature -Online -FeatureName IIS-CommonHttpFeatures
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpErrors
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpRedirect
Enable-WindowsOptionalFeature -Online -FeatureName IIS-ApplicationDevelopment
Enable-WindowsOptionalFeature -Online -FeatureName IIS-NetFxExtensibility45
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HealthAndDiagnostics
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpLogging
Enable-WindowsOptionalFeature -Online -FeatureName IIS-Security
Enable-WindowsOptionalFeature -Online -FeatureName IIS-RequestFiltering
Enable-WindowsOptionalFeature -Online -FeatureName IIS-Performance
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerManagementTools
Enable-WindowsOptionalFeature -Online -FeatureName IIS-ManagementConsole
Enable-WindowsOptionalFeature -Online -FeatureName IIS-IIS6ManagementCompatibility
Enable-WindowsOptionalFeature -Online -FeatureName IIS-Metabase
```

### 2. **Configurar Sitio Web**
```powershell
# Crear sitio web para documentación
Import-Module WebAdministration
New-Website -Name "ScumBunkerTimer-Docs" -Port 8080 -PhysicalPath "C:\ScumBunkerTimer"
```

## 📊 Gestión y Monitoreo

### Comandos de Gestión
```batch
# Iniciar manualmente
schtasks /run /tn "SCUM Bunker Timer"

# Detener
schtasks /end /tn "SCUM Bunker Timer"

# Ver estado
schtasks /query /tn "SCUM Bunker Timer" /fo table

# Ver logs
type C:\ScumBunkerTimer\logs\bot_service_20250808.log
```

### Monitoreo con PowerShell
```powershell
# Script de monitoreo
$taskName = "SCUM Bunker Timer"
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($task) {
    $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
    Write-Host "Estado: $($task.State)"
    Write-Host "Última ejecución: $($taskInfo.LastRunTime)"
    Write-Host "Próxima ejecución: $($taskInfo.NextRunTime)"
    Write-Host "Último resultado: $($taskInfo.LastTaskResult)"
} else {
    Write-Host "❌ Tarea no encontrada"
}
```

## 🔍 Resolución de Problemas

### Verificar Estado
```batch
# Ver procesos Python activos
tasklist /fi "imagename eq python.exe"

# Ver logs en tiempo real
powershell Get-Content C:\ScumBunkerTimer\logs\bot_service_20250808.log -Wait -Tail 10
```

### Errores Comunes

1. **"No se puede encontrar el módulo"**
   - Verificar que Python esté en PATH
   - Reinstalar requirements: `pip install -r requirements.txt`

2. **"Acceso denegado"**
   - Ejecutar tarea como SYSTEM o administrador
   - Verificar permisos en directorio

3. **"Token inválido"**
   - Verificar archivo de configuración
   - Regenerar token en Discord Developer Portal

## ✅ Ventajas de esta Solución

- 🔄 **Reinicio automático** si el bot falla
- 📊 **Logs detallados** para debugging
- 🖥️ **Gestión visual** con interfaz de Windows
- 🌐 **Documentación web** opcional con IIS
- 🛡️ **Ejecutión como servicio del sistema**
- 📈 **Monitoreo integrado** con herramientas de Windows

---

🤖 **SCUM Bunker Timer V2** funcionará 24/7 en tu servidor Windows con máxima confiabilidad.
