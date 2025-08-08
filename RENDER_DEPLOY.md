# 🚀 Deploy en Render.com - GRATIS

## ¿Por qué Render?
- ✅ **100% Gratis** para bots Discord
- ✅ **Deploy automático** desde GitHub
- ✅ **PostgreSQL gratis** incluido
- ✅ **No se cierra** (solo se duerme tras 15 min inactivo)
- ✅ **SSL y dominio** incluidos

## 📋 Pasos para Deploy

### 1. Subir a GitHub (Si no lo has hecho)
```bash
# En tu carpeta del proyecto
git init
git add .
git commit -m "SCUM Bunker Bot V2 - Deploy Ready"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/ScumBunkerTimer.git
git push -u origin main
```

### 2. Crear cuenta en Render
1. Ve a **https://render.com**
2. **Sign Up** con GitHub
3. Autoriza Render a acceder a tus repositorios

### 3. Crear el servicio
1. **Dashboard** → **New +** → **Web Service**
2. **Connect** tu repositorio `ScumBunkerTimer`
3. **Configurar:**
   - **Name:** `scum-bunker-bot`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python BunkerAdvice_V2.py`
   - **Plan:** `Free`

### 4. Configurar Variables de Entorno
1. En tu servicio → **Environment**
2. **Add Environment Variable:**
   - **Key:** `DISCORD_TOKEN`
   - **Value:** `MTQwMzE5MzMxODQxNzg5MTQwOQ.GfKTnD.gY0U9T7X6LY-F8XxdL91xlW-KGvbZJlcZ_3718`

### 5. Deploy
1. **Create Web Service**
2. ¡Render automáticamente construye y despliega!
3. **Logs** → Ver si todo funciona

## 🎯 Configuración Específica para Bots

Como es un bot (no web), necesitas cambiar el tipo:

### Opción A: Web Service (Más fácil)
- Usar como está
- Render detecta que es un bot automáticamente

### Opción B: Background Worker (Más correcto)
1. **New +** → **Background Worker**
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `python BunkerAdvice_V2.py`

## ✅ Verificación

1. **Logs:** Deberías ver "Bot conectado a Discord!"
2. **Discord:** Comandos `/ba_help` funcionando
3. **Estado:** Online 24/7 (se duerme solo si nadie usa comandos por 15 min)

## 🔧 Troubleshooting

### Bot no se conecta
```bash
# Ver logs en Render Dashboard
# Buscar errores de token o permisos
```

### Comandos no aparecen
- Esperar hasta 1 hora para propagación
- Verificar que el bot tenga permisos en Discord

### Bot se duerme
- Normal en plan gratuito
- Se despierta automáticamente con cualquier comando
- Para 24/7 real: upgrade a plan de pago ($7/mes)

## 💡 Tips Pro

1. **Logs en tiempo real:** Dashboard → Logs
2. **Redeploy manual:** Deploy → Manual Deploy
3. **Auto-deploy:** Cada push a main = nuevo deploy automático

## 🎉 ¡Listo!

Tu bot estará online 24/7 gratis en Render. Solo se "dormirá" tras 15 minutos sin comandos, pero se despertará instantáneamente cuando alguien use un comando.

**URL del proyecto:** https://scum-bunker-bot.onrender.com
**Logs:** https://dashboard.render.com/
