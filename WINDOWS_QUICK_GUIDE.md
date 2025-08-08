# 🖥️ SCUM Bunker Timer - Guía Rápida Windows

## 🚀 Instalación Ultra-Rápida

1. **Descargar archivos** del bot a una carpeta
2. **Ejecutar como administrador:** `install_windows.bat`
3. **Ingresar tu DISCORD_TOKEN** cuando se solicite
4. **¡Listo!** El bot funcionará 24/7

## 🎛️ Gestión Diaria

### Scripts de Control (Doble-clic)
- `start_bot.bat` - Iniciar bot
- `stop_bot.bat` - Detener bot  
- `status.bat` - Ver estado
- `view_logs.bat` - Ver logs

### Comandos de Sistema
```batch
# Gestión de tarea programada
schtasks /run /tn "SCUM Bunker Timer"    # Iniciar
schtasks /end /tn "SCUM Bunker Timer"    # Detener
schtasks /query /tn "SCUM Bunker Timer"  # Estado

# Ver procesos
tasklist /fi "imagename eq python.exe"

# Logs en tiempo real
powershell Get-Content C:\ScumBunkerTimer\logs\bot_service_*.log -Wait -Tail 10
```

## 📊 Ubicaciones Importantes

- **Bot:** `C:\ScumBunkerTimer\`
- **Logs:** `C:\ScumBunkerTimer\logs\`
- **Config:** `C:\ScumBunkerTimer\config\bot_config.txt`
- **Base de datos:** `C:\ScumBunkerTimer\bunkers_v2.db`

## 🔧 Configuración Avanzada

### Cambiar Token
Editar: `C:\ScumBunkerTimer\config\bot_config.txt`
```
DISCORD_TOKEN=nuevo_token_aqui
```

### Horario de Reinicio
```batch
# Reiniciar diariamente a las 3 AM
schtasks /change /tn "SCUM Bunker Timer" /st 03:00 /sc daily
```

### Configurar Notificaciones por Email (Opcional)
Agregar a `bot_config.txt`:
```
EMAIL_ALERTS=true
SMTP_SERVER=smtp.gmail.com
EMAIL_USER=tu_email@gmail.com
EMAIL_PASS=tu_app_password
```

## ❌ Resolución de Problemas

### Bot no inicia
1. Verificar token en `bot_config.txt`
2. Ejecutar: `start_bot.bat`
3. Ver logs: `view_logs.bat`

### "Módulo no encontrado"
```batch
cd C:\ScumBunkerTimer
pip install -r requirements.txt
```

### Token inválido
1. Ir a https://discord.com/developers/applications
2. Bot → Reset Token
3. Actualizar `bot_config.txt`

### Ver errores detallados
```batch
cd C:\ScumBunkerTimer
python BunkerAdvice_V2.py
```

## 🌐 Configurar IIS (Opcional)

### Para servir archivos HTML:
```powershell
# Instalar IIS
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole

# Crear sitio
Import-Module WebAdministration
New-Website -Name "ScumTimer-Docs" -Port 8080 -PhysicalPath "C:\ScumBunkerTimer"
```

### Acceder a documentación:
- http://localhost:8080/guide.html
- http://localhost:8080/presentation.html

## ✅ Verificación de Funcionamiento

### En Discord:
- Bot aparece **Online**
- Comando `/ba_help` funciona
- Puede registrar bunkers

### En Windows:
- Tarea programada: **Running**
- Proceso python.exe activo
- Logs sin errores

### Logs exitosos:
```
✅ Configuración cargada desde archivo
✅ Todos los archivos requeridos están presentes
🚀 Iniciando SCUM Bunker Timer...
✅ Bot iniciado con PID: 1234
BOT: Scum Bunker Timer#6315 conectado a Discord!
BOT: EXITO: Sincronizados 13 comandos con Discord
```

## 🚨 Mantenimiento

### Backup diario automático
Crear tarea para backup:
```batch
schtasks /create /tn "SCUM Timer Backup" /tr "robocopy C:\ScumBunkerTimer C:\ScumBunkerTimer\backup /MIR" /sc daily /st 02:00
```

### Limpiar logs antiguos
```batch
forfiles /p C:\ScumBunkerTimer\logs /m *.log /d -7 /c "cmd /c del @path"
```

### Actualizar bot
1. Detener: `stop_bot.bat`
2. Reemplazar archivos Python
3. Iniciar: `start_bot.bat`

---

🤖 **SCUM Bunker Timer V2** funcionando 24/7 en Windows Server con máxima confiabilidad!
