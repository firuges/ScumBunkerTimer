# 🎫 Sistema de Tickets - Guía de Implementación

## 📋 Descripción General

Sistema de tickets independiente que permite a los usuarios crear canales privados para comunicarse con la administración del servidor.

## 🎯 Características Principales

### ✅ **Funcionalidades Core:**
1. **Canal Dedicado** con botón "Crear Ticket"
2. **Canales Privados** `ticket-#numero` solo para admin + usuario
3. **Límite**: 1 ticket activo por usuario por servidor
4. **Base de Datos**: Tabla `tickets` en `scum_main.db`
5. **Independiente**: Módulo separado reutilizable

### 🔧 **Flujo de Trabajo:**
```
Usuario → [Crear Ticket] → Canal privado creado → Admin + Usuario chat → [Cerrar Ticket] → Canal movido a "Tickets Cerrados" → [Borrar Ticket] (Admin) → Canal eliminado
```

## 🏗️ Estructura de Archivos

```
ticket_system.py          # Sistema principal de tickets
ticket_database.py        # Manejo de base de datos  
ticket_views.py           # Views para botones Discord
TICKET_SYSTEM_GUIDE.md    # Esta guía
```

## 🗄️ Base de Datos

### Tabla `tickets`:
```sql
CREATE TABLE tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_number INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    discord_id TEXT NOT NULL,
    discord_guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    subject TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP NULL,
    closed_by TEXT NULL,
    UNIQUE(user_id, discord_guild_id, status) -- Solo 1 ticket abierto por usuario/servidor
);
```

## 🎛️ Comandos Admin

### `/ticket_setup`
Configura el canal de tickets para el servidor
- Crea embed con botón "🎫 Crear Ticket"
- Solo administradores pueden usar

### `/ticket_close <ticket_number>`
Cierra ticket específico (admin)
- Mueve canal a categoría "Tickets Cerrados"
- Actualiza base de datos

### `/ticket_list`
Lista tickets activos del servidor (admin)

## 🔐 Permisos de Canal

### Canal de Tickets:
```python
overwrites = {
    guild.default_role: discord.PermissionOverwrite(
        view_channel=False
    ),
    user: discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True
    ),
    admin_role: discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        manage_channels=True
    )
}
```

## 📱 Interfaz de Usuario

### Botón Crear Ticket:
- Emoji: 🎫
- Label: "Crear Ticket"  
- Style: `discord.ButtonStyle.primary`

### Botón Cerrar Ticket:
- Emoji: 🔒
- Label: "Cerrar Ticket"
- Style: `discord.ButtonStyle.secondary`
- Acción: Mueve ticket a "Tickets Cerrados"

### Botón Borrar Ticket (Solo Admin):
- Emoji: 🗑️
- Label: "Borrar Ticket"
- Style: `discord.ButtonStyle.danger`
- Acción: Elimina canal permanentemente

## 🔄 Estados de Ticket

| Estado | Descripción |
|--------|-------------|
| `open` | Ticket activo - Ambos botones disponibles |
| `closed` | Ticket cerrado - Solo "Borrar" disponible (admin) |
| `deleted` | Ticket eliminado permanentemente |

## 🚀 Integración

### Con usuarios de scum_main.db:
```python
# Verificar que usuario esté registrado
user_manager = UserManager("scum_main.db")
user_data = await user_manager.get_user_by_discord_id(discord_id, guild_id)
if not user_data:
    # Solicitar registro primero
```

### Con sistema modular:
```python
# En bot principal
from ticket_system import TicketSystem

# Setup
ticket_system = TicketSystem("scum_main.db")
await bot.add_cog(ticket_system)
```

## 📝 Ejemplo de Uso

1. **Admin ejecuta** `/ticket_setup` en canal dedicado
2. **Usuario clickea** botón "🎫 Crear Ticket"  
3. **Sistema crea** canal `ticket-0001` 
4. **Usuario y admin** pueden chatear privadamente
5. **Usuario/Admin clickea** "🔒 Cerrar Ticket" cuando resuelto
6. **Canal se mueve** a categoría "Tickets Cerrados"
7. **Admin puede usar** "🗑️ Borrar Ticket" para eliminar permanentemente

## ⚠️ Validaciones

- ✅ Usuario debe estar registrado en el sistema
- ✅ Máximo 1 ticket activo por usuario por servidor
- ✅ Usuarios y admins pueden cerrar tickets
- ✅ Solo admins pueden borrar tickets permanentemente
- ✅ Permisos de canal correctos automáticamente
- ✅ Vistas se recrean automáticamente después del reinicio

## 🔧 Configuración

### Variables de entorno:
```python
TICKET_CATEGORY_NAME = "🎫 Tickets"              # Categoría para tickets activos
CLOSED_TICKET_CATEGORY_NAME = "🎫 Tickets Cerrados"  # Categoría para tickets cerrados  
TICKET_LOG_CHANNEL = "ticket-logs"              # Canal para logs de admin
```

## 🆕 Nuevas Funcionalidades

### 🎫 Fame Point Rewards:
- ✅ **Selector mejorado** - Permite re-selección del mismo item
- ✅ **Botón "Ver Premios"** - Usuarios ven premios, admins configuran
- ✅ **Configuración por servidor** - Premios personalizables por guild

### 🎫 Sistema de Tickets Mejorado:
- ✅ **Dos botones diferenciados** - Cerrar vs Borrar
- ✅ **Categoría automática** - "Tickets Cerrados" se crea automáticamente
- ✅ **Estados granulares** - open, closed, deleted
- ✅ **Vistas persistentes** - Se recrean después del reinicio
- ✅ **Botón readonly** - "Cerrar" se deshabilita tras uso

Este sistema es modular, reutilizable y se integra perfectamente con la estructura existente de scum_main.db.