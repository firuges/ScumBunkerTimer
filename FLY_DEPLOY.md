# 🚀 Deploy en Fly.io - GRATIS y POTENTE

## ¿Por qué Fly.io?
- ✅ **Gratis generoso** (mejor que Heroku)
- ✅ **No se duerme** como Render
- ✅ **Muy rápido** (edge computing)
- ✅ **Deploy fácil** con CLI
- ✅ **PostgreSQL gratis** incluido

## 📋 Pasos para Deploy

### 1. Instalar Fly CLI
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# O descargar desde https://fly.io/docs/getting-started/installing-flyctl/
```

### 2. Crear cuenta y login
```bash
fly auth signup    # Crear cuenta
fly auth login     # Hacer login
```

### 3. Inicializar proyecto
```bash
# En tu carpeta del proyecto
fly launch
```

**Configuración automática:**
- Detecta Python automáticamente
- Crea `fly.toml` automáticamente
- Pregunta por región (elige la más cercana)

### 4. Configurar variables de entorno
```bash
fly secrets set DISCORD_TOKEN=MTQwMzE5MzMxODQxNzg5MTQwOQ.GfKTnD.gY0U9T7X6LY-F8XxdL91xlW-KGvbZJlcZ_3718
```

### 5. Deploy
```bash
fly deploy
```

## 🔧 Configuración Manual (si es necesario)

Si `fly launch` no funciona perfecto, crea `fly.toml`:

```toml
app = "scum-bunker-bot"
primary_region = "mad"  # Madrid - cambia por tu región

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

## 🎯 Para Bots Discord (Importante)

Los bots no necesitan puerto HTTP. Modifica `fly.toml`:

```toml
app = "scum-bunker-bot"
primary_region = "mad"

[build]
  builder = "paketobuildpacks/builder:base"

# Eliminar la sección [services] ya que es un bot, no web app
```

## ✅ Comandos Útiles

```bash
fly logs                 # Ver logs en tiempo real
fly status              # Estado de la app
fly restart             # Reiniciar bot
fly destroy             # Eliminar (cuidado!)
fly secrets list        # Ver variables de entorno
```

## 🎉 Ventajas de Fly.io

- **No se duerme** como Render
- **Más recursos** en plan gratuito
- **Regiones globales** (menor latencia)
- **CLI potente** para desarrollo

## 🎯 Mi Recomendación

**Fly.io es perfecto si:**
- Quieres que el bot esté **siempre activo**
- No te importa usar CLI
- Quieres **mejor rendimiento**

**Render es perfecto si:**
- Prefieres **interfaz web**
- No te importa que se duerma 15 min
- Quieres **súper fácil**
