# 🚀 Deploy en Render.com - SCUM Bunker Timer V2

## ⚠️ IMPORTANTE: Background Worker, NO Web Service

Este bot debe ser desplegado como **Background Worker** porque:
- No necesita exponer puertos HTTP
- Es un bot de Discord que se conecta vía WebSocket
- Funciona 24/7 en background

## 🔧 Paso a Paso

### 1. Preparar el Repositorio
```bash
git clone https://github.com/firuges/ScumBunkerTimer.git
cd ScumBunkerTimer
```

### 2. Crear Background Worker en Render

1. **Ir a [Render.com](https://render.com)**
2. **Crear nueva cuenta o login**
3. **Clic en "New +"**
4. **Seleccionar "Background Worker"** ⚠️ (NO Web Service)
5. **Conectar repositorio GitHub:** `firuges/ScumBunkerTimer`

### 3. Configuración del Servicio

```
Name: scum-bunker-timer
Environment: Python 3
Region: Oregon (US West) - recomendado para Discord
Plan: Starter (Free)

Build Command: pip install -r requirements.txt
Start Command: python BunkerAdvice_V2.py
```

### 4. Variables de Entorno

Agregar en Environment Variables:
```
DISCORD_TOKEN = tu_token_del_bot_aqui
```

### 5. Deploy

1. **Clic en "Create Background Worker"**
2. **Esperar el build (2-3 minutos)**
3. **Verificar logs:**

```
✅ Logs exitosos:
2025-08-08 21:56:57,048 - __main__ - INFO - EXITO: Sincronizados 13 comandos con Discord
```

## 📁 Archivos de Configuración (ya incluidos)

### requirements.txt
```txt
discord.py==2.5.2
aiosqlite==0.19.0
python-dateutil==2.9.0
```

### render.yaml
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

### runtime.txt
```txt
python-3.11.0
```

## ❌ Errores Comunes

### "Port scan timeout reached"
**Causa:** Servicio creado como Web Service en lugar de Background Worker
**Solución:** Recrear como Background Worker

### "Module not found"
**Causa:** requirements.txt no instalado
**Solución:** Verificar Build Command: `pip install -r requirements.txt`

### "Invalid token"
**Causa:** DISCORD_TOKEN incorrecto o faltante
**Solución:** Verificar variable de entorno

## ✅ Verificación Exitosa

El bot estará funcionando cuando veas:
```
- Base de datos V2 inicializada correctamente
- Sistema de suscripciones inicializado
- Scum Bunker Timer#6315 conectado a Discord!
- EXITO: Sincronizados 13 comandos con Discord
```

## 🎯 Características Desplegadas

- ✅ 13 comandos slash sincronizados
- ✅ Sistema de notificaciones automáticas
- ✅ Base de datos SQLite persistente
- ✅ Sistema premium con límites diarios
- ✅ Documentación HTML completa
- ✅ Funcionamiento 24/7

## 📞 Soporte

Si tienes problemas:
1. Verificar que sea Background Worker
2. Revisar logs en Render Dashboard
3. Verificar token de Discord
4. Consultar RENDER_DEPLOY_FIX.md para errores específicos

---
🤖 **SCUM Bunker Timer V2** - Ready for production on Render!
