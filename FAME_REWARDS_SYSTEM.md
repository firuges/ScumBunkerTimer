# 🏆 Fame Point Rewards System

## Descripción
Sistema completo para gestionar reclamaciones de puntos de fama SCUM con ranking Top 10 y sistema de notificaciones para administradores.

## Características Principales

### 🎯 Para Usuarios
- **Selector configurable** de cantidades de fama (100, 500, 1000, 2000, 5000, 10000, 15000 por defecto)
- **Ranking Top 10** ordenado por mayor fama → menor fama → primero en tiempo
- **Formulario de reclamación** con razón y evidencia opcional
- **Una reclamación pendiente** por usuario máximo
- **Notificaciones por DM** del resultado de la reclamación

### 👑 Para Administradores
- **Canal de notificaciones** dedicado con botones de confirmar/rechazar
- **Configuración personalizable** de valores de fama disponibles
- **Información completa** del usuario que reclama (Discord ID, antigüedad, etc.)
- **Sistema de logging** detallado de todas las acciones
- **Panel automático** que se restaura al reiniciar el bot

## Archivos del Sistema

### 📁 Archivos Principales
- `fame_rewards_database.py` - Base de datos y operaciones CRUD
- `fame_rewards_system.py` - Sistema principal y comandos
- `fame_rewards_views.py` - Interfaces Discord UI (botones, modales, selectores)

### 🗄️ Tablas de Base de Datos
```sql
-- Reclamaciones de puntos de fama
CREATE TABLE fame_point_claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    discord_id TEXT NOT NULL,
    discord_guild_id TEXT NOT NULL,
    fame_amount INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'confirmed', 'rejected'
    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP NULL,
    confirmed_by TEXT NULL,
    notification_message_id TEXT NULL
);

-- Configuración de valores de fama por guild
CREATE TABLE fame_point_config (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL UNIQUE,
    fame_values TEXT NOT NULL,  -- CSV: "100,500,1000,2000,5000,10000,15000"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 📋 Channel Config
Se agregan dos nuevos tipos de canal:
- `fame_rewards` - Canal principal con ranking y selector de fama
- `fame_notifications` - Canal privado para notificaciones de admin

## Comandos Disponibles

### 🔧 Comandos de Administración
- `/fame_rewards_setup` - Configurar sistema manualmente
- `/fame_config` - Configurar valores de fama disponibles
- `/ba_admin_channels_setup` - Configurar todos los canales incluyendo Fame Rewards

### 👥 Para Usuarios
- **Panel interactivo** con selector de cantidades de fama
- **Formulario modal** para proporcionar razón y evidencia
- **Ranking en tiempo real** actualizado automáticamente

## Flujo de Funcionamiento

### 📊 Proceso de Reclamación
1. **Usuario selecciona** cantidad de fama del selector
2. **Sistema verifica** que esté registrado y no tenga reclamaciones pendientes
3. **Modal aparece** solicitando razón y evidencia
4. **Notificación enviada** al canal de administradores con botones
5. **Admin confirma/rechaza** usando los botones
6. **Usuario notificado** por DM del resultado
7. **Ranking actualizado** automáticamente si se confirma

### 🔄 Restauración Automática
- **Paneles principales** se limpian y recrean al reiniciar bot
- **Rankings actualizados** con datos más recientes
- **Configuraciones persistentes** en base de datos
- **Integración completa** con sistema de channel configs

## Integración con Sistemas Existentes

### ✅ Compatibilidad
- **Usa scum_main.db** como base de datos principal
- **Integrado con UserManager** para verificar usuarios registrados
- **Sigue patrón de otros sistemas** (banking, taxi, mechanic, tickets)
- **load_channel_configs()** para restauración automática
- **Logging consistente** con el resto del bot

### 🛡️ Seguridad
- **Verificación de permisos** de administrador para comandos críticos
- **Rate limiting** implícito por límite de 1 reclamación pendiente
- **Validación de datos** en formularios y configuraciones
- **Manejo de errores** robusto con logging detallado

## Configuración Recomendada

### 📝 Valores por Defecto
```python
fame_values = [100, 500, 1000, 2000, 5000, 10000, 15000]
```

### 🎯 Ejemplo de Uso con /ba_admin_channels_setup
```
/ba_admin_channels_setup
  fame_rewards_channel: #fame-rewards
  fame_notifications_channel: #admin-fame-notifications
```

### ⚙️ Personalización
```
/fame_config values: 250,750,1500,3000,7500,12000,20000
```

## Características Técnicas

### 🎨 UI/UX
- **Embeds atractivos** con colores apropiados (oro para fama)
- **Iconos descriptivos** (🏆, ⭐, 🥇, 🥈, 🥉)
- **Formato de números** con separadores de miles (10,000)
- **Timestamps Discord** para fechas dinámicas
- **Ephemeral messages** para privacidad de usuario

### 📊 Performance
- **Índices optimizados** en base de datos para consultas rápidas
- **Límites de Discord** respetados (25 opciones en selector máximo)
- **Cleanup automático** de mensajes del bot
- **Async/await** para operaciones no bloqueantes

## Testing y Debugging

### 🧪 Verificaciones Recomendadas
1. Crear reclamación con usuario registrado
2. Verificar notificación en canal de admin
3. Confirmar/rechazar y verificar DM al usuario  
4. Comprobar actualización del ranking
5. Probar configuración de valores personalizados
6. Verificar restauración después de reinicio

### 📋 Logs Importantes
- Creación de reclamaciones con detalles
- Confirmaciones/rechazos con admin responsable
- Errores de permisos o configuración
- Restauración de paneles al iniciar bot

¡El sistema está completamente implementado y listo para usar!