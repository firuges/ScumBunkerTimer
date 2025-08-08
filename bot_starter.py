"""
SCUM Bunker Timer - Windows Service Starter
Gestor robusto para ejecutar el bot como tarea programada de Windows
"""
import os
import sys
import time
import logging
import subprocess
from datetime import datetime
import traceback
import psutil

# Configurar directorio base
BASE_DIR = r"C:\ScumBunkerTimer"
LOG_DIR = os.path.join(BASE_DIR, "logs")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

# Crear directorios si no existen
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

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

logger = logging.getLogger(__name__)

def load_config():
    """Cargar configuración desde archivo o variables de entorno"""
    config_file = os.path.join(CONFIG_DIR, "bot_config.txt")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            logger.info("✅ Configuración cargada desde archivo")
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
    else:
        logger.info("ℹ️ Usando variables de entorno del sistema")
    
    # Verificar token
    if not os.getenv('DISCORD_TOKEN'):
        logger.error("❌ DISCORD_TOKEN no configurado")
        return False
    
    return True

def cleanup_old_processes():
    """Limpiar procesos antiguos del bot"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'BunkerAdvice_V2.py' in cmdline:
                        logger.warning(f"🔄 Terminando proceso anterior PID: {proc.info['pid']}")
                        proc.terminate()
                        proc.wait(timeout=10)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.warning(f"⚠️ Error limpiando procesos: {e}")

def check_dependencies():
    """Verificar que todas las dependencias estén instaladas"""
    required_files = [
        "BunkerAdvice_V2.py",
        "database_v2.py", 
        "premium_commands.py",
        "subscription_manager.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(BASE_DIR, file)):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"❌ Archivos faltantes: {missing_files}")
        return False
    
    logger.info("✅ Todos los archivos requeridos están presentes")
    return True

def start_bot():
    """Iniciar el bot con gestión de errores"""
    bot_script = os.path.join(BASE_DIR, "BunkerAdvice_V2.py")
    
    try:
        logger.info("🚀 Iniciando SCUM Bunker Timer...")
        
        # Cambiar al directorio del bot
        os.chdir(BASE_DIR)
        
        # Ejecutar el bot
        process = subprocess.Popen(
            [sys.executable, bot_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1,
            universal_newlines=True
        )
        
        logger.info(f"✅ Bot iniciado con PID: {process.pid}")
        
        # Monitorear el proceso y logs
        while True:
            # Verificar si el proceso sigue corriendo
            return_code = process.poll()
            if return_code is not None:
                # El proceso terminó
                remaining_output = process.stdout.read()
                if remaining_output:
                    for line in remaining_output.split('\n'):
                        if line.strip():
                            logger.info(f"BOT: {line}")
                
                logger.error(f"❌ Bot terminó con código: {return_code}")
                return False
            
            # Leer output en tiempo real
            try:
                line = process.stdout.readline()
                if line:
                    logger.info(f"BOT: {line.strip()}")
            except:
                pass
            
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"❌ Error iniciando bot: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Función principal con reinicio automático"""
    logger.info("🔧 Iniciando gestor de SCUM Bunker Timer")
    
    # Verificar configuración
    if not load_config():
        logger.error("❌ Error en configuración. Deteniendo.")
        return
    
    # Verificar dependencias
    if not check_dependencies():
        logger.error("❌ Dependencias faltantes. Deteniendo.")
        return
    
    # Limpiar procesos anteriores
    cleanup_old_processes()
    time.sleep(2)
    
    max_restarts = 10
    restart_count = 0
    
    while restart_count < max_restarts:
        logger.info(f"🔄 Intento de inicio #{restart_count + 1}")
        
        success = start_bot()
        
        if success:
            logger.info("✅ Bot funcionando correctamente")
            restart_count = 0  # Reset counter on success
        else:
            restart_count += 1
            if restart_count < max_restarts:
                wait_time = min(30 * restart_count, 300)  # Max 5 minutos
                logger.warning(f"⏳ Reintentando en {wait_time} segundos... ({restart_count}/{max_restarts})")
                time.sleep(wait_time)
            else:
                logger.error("❌ Máximo de reintentos alcanzado. Deteniendo servicio.")
                break
    
    logger.info("🛑 Gestor de bot detenido")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Interrupción manual detectada")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        logger.error(traceback.format_exc())
