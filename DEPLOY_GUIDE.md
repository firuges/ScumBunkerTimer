# 🚀 Deploy Guide - SCUM Bunker Bot V2

## Opciones de Deploy Gratuitas

### 🌟 Railway (RECOMENDADO)

1. **Crear cuenta en Railway.app**
2. **Conectar GitHub:**
   - Sube tu proyecto a GitHub
   - Conecta el repositorio en Railway
3. **Configurar variables:**
   - `DISCORD_TOKEN`: Tu token de Discord
4. **Deploy automático:**
   - Railway detecta automáticamente el proyecto Python
   - Se despliega usando `railway.toml`

**Ventajas:**
- ✅ Gratis hasta 500 horas/mes
- ✅ Deploy automático desde GitHub
- ✅ Base de datos PostgreSQL incluida
- ✅ SSL automático

### 🔷 Render

1. **Crear cuenta en Render.com**
2. **Conectar repositorio:**
   - Autorizar GitHub
   - Seleccionar repositorio
3. **Configurar como Worker:**
   - Service Type: Worker
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python BunkerAdvice_V2.py`
4. **Variables de entorno:**
   - `DISCORD_TOKEN`: Tu token

### 🟣 Heroku

1. **Crear cuenta en Heroku.com**
2. **Instalar Heroku CLI**
3. **Comandos:**
```bash
heroku create tu-bot-name
heroku config:set DISCORD_TOKEN=tu_token_aqui
git push heroku main
```

### 🟢 Replit

1. **Crear cuenta en Replit.com**
2. **Import from GitHub:**
   - Conectar repositorio
   - Seleccionar como Python project
3. **Configurar variables:**
   - Secrets: `DISCORD_TOKEN`
4. **Ejecutar:**
   - Presionar Run
   - Para Always On: Upgrade required

## 🗃️ Base de Datos en Producción

### Para SQLite (Simple)
- Funciona en todos los servicios
- Archivo `bunkers_v2.db` se guarda automáticamente
- **Limitación:** Se borra en algunos servicios al hacer redeploy

### Para PostgreSQL (Profesional)
1. **Railway/Heroku:** Base de datos automática
2. **Modificar código:** Cambiar SQLite por PostgreSQL
3. **Variables adicionales:**
   - `DATABASE_URL`
   - Instalar `psycopg2`

## 🔐 Variables de Entorno Requeridas

```env
DISCORD_TOKEN=tu_token_de_discord_aqui
```

## 📦 Archivos de Deploy Incluidos

- `Procfile` - Para Heroku
- `railway.toml` - Para Railway  
- `render.yaml` - Para Render
- `runtime.txt` - Versión de Python
- `.gitignore` - Archivos a ignorar
- `requirements.txt` - Dependencias

## 🚀 Deploy Rápido con Railway

1. **Sube a GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/tu-usuario/scum-bunker-bot.git
git push -u origin main
```

2. **En Railway.app:**
   - New Project → Deploy from GitHub
   - Seleccionar repositorio
   - Add variable: `DISCORD_TOKEN`
   - ¡Listo!

## 🔧 Troubleshooting

### Bot no se conecta
- Verificar que `DISCORD_TOKEN` esté configurado
- Revisar logs del servicio

### Base de datos no funciona
- En producción, usar PostgreSQL
- Verificar permisos de escritura

### Comandos no aparecen
- Esperar hasta 1 hora para propagación global
- Verificar permisos del bot en Discord

## 💡 Recomendación Final

**Para empezar:** Railway (gratis y fácil)
**Para producción:** DigitalOcean ($5/mes)
**Para hobby:** Heroku ($7/mes)
