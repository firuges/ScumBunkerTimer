# 🤖 Permisos Requeridos del Bot - SCUM System

## 🎫 **Para Sistema de Tickets:**

### ✅ **Permisos CRÍTICOS (Obligatorios):**
- **Manage Channels** - Crear/eliminar canales de tickets
- **Manage Permissions** - Configurar permisos privados de canales
- **View Channels** - Ver todos los canales del servidor
- **Send Messages** - Enviar mensajes en canales
- **Embed Links** - Crear embeds para paneles y notificaciones
- **Read Message History** - Leer historial para recrear vistas
- **Use Slash Commands** - Ejecutar comandos de administración

### 🔧 **Permisos IMPORTANTES (Recomendados):**
- **Manage Messages** - Limpiar mensajes anteriores del bot
- **Add Reactions** - Reacciones en mensajes (opcional)
- **Attach Files** - Adjuntar archivos en tickets (opcional)
- **Manage Roles** - Para permisos avanzados de roles (opcional)

## 🏆 **Para Fame Point Rewards:**
- **Send Messages** - Enviar notificaciones de admin
- **Embed Links** - Crear embeds de reclamaciones
- **Use Slash Commands** - Comandos de configuración

## 🏦 **Para Sistemas Bancarios/Taxi/etc:**
- **Send Messages** - Mensajes del sistema
- **Embed Links** - Paneles y embeds
- **Use Slash Commands** - Comandos de usuario

## ⚙️ **Configuración en Discord:**

### 1. **Servidor → Configuración → Roles:**
```
Buscar el rol del bot (nombre del bot)
Permisos del Servidor:
☑️ Ver Canales
☑️ Gestionar Canales  
☑️ Gestionar Permisos
☑️ Enviar Mensajes
☑️ Insertar Enlaces
☑️ Leer Historial de Mensajes
☑️ Usar Comandos de Aplicación
☑️ Gestionar Mensajes (recomendado)
```

### 2. **Por Categoría (Recomendado):**
```
🎫 Tickets:
- El bot debe tener permisos COMPLETOS en esta categoría
- Gestionar Canales, Permisos, Mensajes

🎫 Tickets Cerrados:  
- El bot debe poder ver y gestionar estos canales
- Solo lectura para usuarios, gestión completa para bot
```

## 🚨 **Problemas Comunes sin Permisos:**

| Error | Permiso Faltante | Solución |
|-------|------------------|----------|
| `Missing Permissions: manage_channels` | Manage Channels | Dar permiso "Gestionar Canales" |
| `Missing Permissions: manage_permissions` | Manage Permissions | Dar permiso "Gestionar Permisos" |
| `Cannot send messages` | Send Messages | Dar permiso "Enviar Mensajes" |
| `Cannot create category` | Manage Channels | Dar permiso "Gestionar Canales" |
| `Bot commands not working` | Use Slash Commands | Dar permiso "Usar Comandos de Aplicación" |

## 🔧 **Verificación de Permisos:**

### Comando para verificar:
```python
# En un canal donde el bot tenga acceso:
/bot_permisos  # (si implementamos este comando)

# O verificar manualmente:
# Server Settings → Roles → [Bot Role] → Permissions
```

## 🛡️ **Seguridad:**

### ✅ **Permisos que SÍ necesita:**
- Manage Channels (para tickets)
- Manage Permissions (para canales privados)
- Send Messages (básico)
- Embed Links (embeds)

### ❌ **Permisos que NO necesita:**
- **Administrator** (demasiado poder)
- **Manage Server** (innecesario)
- **Manage Roles** (solo si usas roles específicos)
- **Ban Members** (no relacionado)
- **Kick Members** (no relacionado)

## 📋 **Checklist de Configuración:**

- [ ] Bot añadido al servidor
- [ ] Rol del bot creado automáticamente
- [ ] Permisos básicos asignados al rol del bot
- [ ] Permisos específicos en categorías de tickets
- [ ] Comandos slash sincronizados (`/sync` si es necesario)
- [ ] Canales de configuración creados
- [ ] Panel de tickets configurado (`/ticket_setup`)

## 🔗 **Links Útiles:**

- [Discord Permissions Calculator](https://discordapi.com/permissions.html)
- [Bot Permissions Guide](https://discord.com/developers/docs/topics/permissions)

---

**💡 Tip:** Es mejor dar permisos específicos que "Administrator". Esto es más seguro y permite mejor control de acceso.