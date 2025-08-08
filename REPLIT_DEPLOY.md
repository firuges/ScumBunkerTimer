# 🚀 Deploy en Replit - SÚPER FÁCIL

## ¿Por qué Replit?
- ✅ **Súper fácil** - solo copiar código
- ✅ **Editor online** incluido
- ✅ **Deploy en 2 minutos**
- ✅ **Perfecto para probar**
- ✅ **No necesitas GitHub**

## 📋 Pasos (MUY FÁCIL)

### 1. Crear cuenta
1. Ve a **https://replit.com**
2. **Sign Up** gratis
3. Verificar email

### 2. Crear Repl
1. **Create Repl**
2. **Template:** Python
3. **Name:** `SCUM-Bunker-Bot`
4. **Create Repl**

### 3. Subir archivos
**Opción A - Copiar y pegar:**
1. **Files** → Delete `main.py`
2. **Create file** → `BunkerAdvice_V2.py`
3. Copiar todo tu código
4. **Create file** → `database_v2.py`
5. Copiar código de database
6. **Create file** → `requirements.txt`
7. Copiar dependencias

**Opción B - Import from GitHub:**
1. **Create** → **Import from GitHub**
2. URL: `https://github.com/TU-USUARIO/ScumBunkerTimer`

### 4. Configurar variables
1. **Secrets** (icono de candado) →
2. **New Secret:**
   - **Key:** `DISCORD_TOKEN`
   - **Value:** `XXXX`

### 5. Instalar dependencias
En la **Console:**
```bash
pip install discord.py aiosqlite python-dotenv
```

### 6. Ejecutar
1. **Run** (botón verde)
2. ¡Tu bot está online!

## 🔧 Configuración para 24/7

### Opción A: GRATIS (Con limitaciones)
- Bot se duerme tras ~1 hora sin actividad
- Se despierta con cualquier comando
- **Usar:** UptimeRobot para hacer ping cada 5 min

### Opción B: Always On ($7/mes)
1. **Boost** → **Always On**
2. Bot nunca se duerme
3. Online 24/7 real

## 🎯 Keep Alive Hack (GRATIS)

Para mantener el bot despierto gratis, agrega esto a tu código:

```python
# Al final de BunkerAdvice_V2.py, antes de asyncio.run(main())

from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# Llamar antes de main()
if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
```

Y agregar a `requirements.txt`:
```
flask
```

Luego usar **UptimeRobot.com** para hacer ping a tu repl cada 5 minutos.

## ✅ Verificación

1. **Console:** Ver "Bot conectado a Discord!"
2. **Discord:** Probar comandos `/ba_help`
3. **Webview:** Ver "Bot is alive!" si usas keep_alive

## 🎉 Ventajas de Replit

- **Desarrollo online** - puedes editar desde cualquier lugar
- **Colaboración** - compartir código fácilmente
- **Packages** - instala automáticamente dependencias
- **Hosting integrado** - todo en un lugar

## 💡 Mi Recomendación

**Replit es perfecto para:**
- **Principiantes** que quieren algo súper fácil
- **Probar** el bot sin complicaciones
- **Desarrollar online** sin instalar nada local

**Para producción seria:** Usar Render o Fly.io
