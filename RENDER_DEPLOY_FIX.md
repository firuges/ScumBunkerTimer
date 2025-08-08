# 🚀 Guía de Deployment en Render - SCUM Bunker Timer V2

## ⚠️ PROBLEMA COMÚN: "Port scan timeout"

Si ves este error:
```
Timed out
Port scan timeout reached, no open ports detected. Bind your service to at least one port.
```

**Causa:** El servicio fue creado como "Web Service" en lugar de "Background Worker"

## ✅ SOLUCIÓN: Crear Background Worker

### Opción 1: Recrear el Servicio (RECOMENDADO)

1. **Eliminar el servicio actual:**
   - Ve a tu dashboard de Render
   - Selecciona el servicio actual
   - Settings → Danger Zone → Delete Service

2. **Crear nuevo Background Worker:**
   - Clic en "New +"
   - Seleccionar **"Background Worker"** (NO Web Service)
   - Conectar tu repositorio GitHub: `firuges/ScumBunkerTimer`
   - Configurar:
     ```
     Name: scum-bunker-timer
     Environment: Python 3
     Build Command: pip install -r requirements.txt
     Start Command: python BunkerAdvice_V2.py
     ```

3. **Variables de entorno:**
   ```
   DISCORD_TOKEN = tu_token_aqui
   ```

### Opción 2: Modificar Servicio Existente

Si no quieres recrear el servicio:

1. **Ir a Settings del servicio**
2. **Cambiar en "General":**
   - Service Type: Background Worker
   - Start Command: `python BunkerAdvice_V2.py`
   - Remove cualquier configuración de puerto

## 📋 Configuración Completa

### Archivos necesarios en el repo (ya incluidos):

1. **requirements.txt** ✅
   ```
   discord.py==2.5.2
   aiosqlite==0.19.0
   python-dateutil==2.9.0
   ```

2. **render.yaml** ✅
   ```yaml
   services:
     - type: worker
       name: scum-bunker-bot
       env: python
       plan: free
       buildCommand: pip install -r requirements.txt
       startCommand: python BunkerAdvice_V2.py
       envVars:
         - key: DISCORD_TOKEN
           sync: false
   ```

3. **runtime.txt** ✅
   ```
   python-3.11.0
   ```

## 🔧 Configuración en Render Dashboard

### Environment Variables:
```
DISCORD_TOKEN = Bot_Token_Aqui
```

### Build & Deploy Settings:
```
Build Command: pip install -r requirements.txt
Start Command: python BunkerAdvice_V2.py
```

## ✅ Verificación Exitosa

Cuando esté bien configurado verás en los logs:
```
2025-08-08 21:56:57,048 - __main__ - INFO - EXITO: Sincronizados 13 comandos con Discord
```

Y el servicio se mantendrá corriendo sin errores de timeout.

## 🎯 Resumen de la Solución

**El bot de Discord NO necesita exponer puertos HTTP**, por eso debe ser un **Background Worker**, no un Web Service.

Los logs que mostraste indican que el bot funciona perfectamente:
- ✅ Conectado a Discord
- ✅ 13 comandos sincronizados
- ✅ Base de datos inicializada

Solo necesitas cambiar el tipo de servicio en Render.

---

🤖 **SCUM Bunker Timer V2** está listo para funcionar 24/7 en Render como Background Worker.
