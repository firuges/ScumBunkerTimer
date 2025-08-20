# 🔄 FLUJOS DEL SISTEMA - GUÍA RÁPIDA

## 📋 ÍNDICE RÁPIDO
- [🏦 Sistema Bancario](#-sistema-bancario)
- [🏢 Sistema de Bunkers](#-sistema-de-bunkers)
- [🔧 Sistema de Mecánico/Seguros](#-sistema-de-mecánicoseguros)
- [🚗 Sistema de Taxi](#-sistema-de-taxi)
- [👥 Sistema de Escuadrones](#-sistema-de-escuadrones)
- [💎 Sistema Premium](#-sistema-premium)
- [🛒 Sistema de Tienda](#-sistema-de-tienda)
- [⚙️ Sistema de Administración](#️-sistema-de-administración)

---

## 🏦 Sistema Bancario

### 📍 Canal: General/Banking
**Archivo Principal:** `banking_system.py`

### Flujos:
- **Balance** (`/banco_balance`)
  - Verifica registro del usuario
  - Consulta balance en BD → `taxi_database.py:get_user_balance()`
  - Muestra embed con dinero disponible

- **Transferir** (`/banco_transferir`)
  - Validaciones: no auto-transferencia, cantidad válida
  - Verifica fondos suficientes
  - Ejecuta transacción → `taxi_database.py:transfer_money()`
  - Registra en historial

- **Historial** (`/banco_historial`)
  - Obtiene transacciones → `taxi_database.py:get_user_transactions()`
  - Muestra últimas N transacciones con paginación

**Conexiones:** `taxi_database.py`, `rate_limiter.py`

---

## 🏢 Sistema de Bunkers

### 📍 Canal: Configurado por admin
**Archivo Principal:** `BunkerAdvice_V2.py`

### Flujos:

#### 🔍 Consultar Bunker (`/ba_check_bunker`)
- Autocompletado de servidores → `database_v2.py:get_unique_servers()`
- Consulta estado del bunker → `database_v2.py:get_bunker_status()`
- Muestra embed con estado, tiempo restante, responsable
- Botones: Registrar/Actualizar según estado

#### 📊 Estado General (`/ba_status_all`)
- Obtiene todos los bunkers → `database_v2.py:get_all_bunkers_status()`
- Agrupa por estado (activos, cerrados, expirados)
- Embed con resumen + navegación por páginas

#### 🎯 Mi Uso (`/ba_my_usage`)
- Filtra bunkers del usuario → `database_v2.py:get_user_bunkers()`
- Muestra contribuciones personales
- Estadísticas de participación

#### ⚙️ Gestión de Servidores
- **Agregar** (`/ba_add_server`) → `database_v2.py:add_server()`
- **Remover** (`/ba_remove_server`) → `database_v2.py:remove_server()`
- **Listar** (`/ba_list_servers`) → `database_v2.py:get_servers()`

**Conexiones:** `database_v2.py`, `premium_utils.py`, `rate_limiter.py`

---

## 🔧 Sistema de Mecánico/Seguros

### 📍 Canal: Taller (configurado por admin)
**Archivo Principal:** `mechanic_system.py`

### Flujos:

#### 🛡️ Solicitar Seguro (`/seguro_solicitar`)
- Modal para datos del vehículo
- Verificación: vehículo no asegurado → `check_vehicle_insurance_status()`
- Selector de vehículos disponibles
- Creación de solicitud → `create_insurance_request()`
- Notificación a mecánicos

#### 🔍 Consultar Seguro (`/seguro_consultar`)
- Busca seguros del usuario → Query con JOIN de tablas
- Muestra información completa del seguro
- Estado: pendiente/confirmado/rechazado

#### 🔔 Sistema de Notificaciones
- **Configurar** (`/mechanic_notifications`)
- **Envío automático** → `send_mechanic_notification()`
- **Notificación pública** → `send_channel_notification()` - Mensaje editable
- **Verificación de estado** → Previene procesamiento duplicado
- Canal configurable por servidor

#### ⚙️ Administración de Mecánicos
- **Registrar** (`/mechanic_admin_register`)
- **Remover** (`/mechanic_admin_remove`)
- **Listar** (`/mechanic_admin_list`)
- **Configurar PVP** (`/mechanic_admin_config_pvp`)

#### 💰 Gestión de Precios/Límites
- **Establecer precios** (`/mechanic_admin_set_price`)
- **Ver precios** (`/mechanic_admin_list_prices`)
- **Configurar límites** (`/mechanic_admin_set_limit`)
- **Ver límites** (`/mechanic_admin_list_limits`)

**Conexiones:** `taxi_database.py`, `taxi_admin.py` (panel admin), `rate_limiter.py`

---

## 🚗 Sistema de Taxi

### 📍 Canal: Configurado por admin
**Archivo Principal:** `taxi_system.py`

### Flujos:

#### 🚕 Solicitar Taxi (`/taxi_solicitar`)
- Modal con origen/destino
- Cálculo automático de tarifa → `calculate_fare()`
- Verificación de fondos
- Creación de viaje → `create_taxi_trip()`
- Notificación a taxistas

#### 📊 Estado (`/taxi_status`)
- Consulta viajes activos → `get_active_trips()`
- Información de viaje en curso
- Opción de cancelar

#### ❌ Cancelar (`/taxi_cancelar`)
- Verificación de viaje activo
- Aplicación de penalización si corresponde
- Actualización de estado → `cancel_trip()`

#### 📍 Zonas y Tarifas
- **Ver zonas** (`/taxi_zonas`) → `get_taxi_zones()`
- **Ver tarifas** (`/taxi_tarifas`) → `get_taxi_rates()`

#### 🔄 Reset Alertas (`/ba_reset_alerts`)
- Limpia notificaciones acumuladas
- Resetea contadores de alertas

**Administración:** `taxi_admin.py`
- Estadísticas, configuración de tarifas, renovación de licencias, etc.

**Conexiones:** `taxi_database.py`, `taxi_admin.py`, `rate_limiter.py`

---

## 👥 Sistema de Escuadrones

### 📍 Integrado en Mecánico
**Archivo Principal:** `mechanic_system.py` (sección Squadron)

### Flujos:

#### ⚙️ Configuración (`/squadron_admin_config_limits`)
- Establece límites por escuadrón
- Configuración de miembros máximos
- Permisos y restricciones

#### 👀 Visualización
- **Ver configuración** (`/squadron_admin_view_config`)
- **Ver miembro** (`/squadron_admin_view_member`)

#### 🗑️ Gestión
- **Remover miembro** (`/squadron_admin_remove_member`)
- **Limpieza** (`/squadron_admin_cleanup`)

#### 🚗 Gestión de Vehículos
- **Ver Mis Vehículos** → `VehicleManagementView`
- **Editar ID** → `VehicleEditModal` - Corregir IDs mal ingresados
- **Dar de Baja** → `unregister_vehicle()` - Baja lógica (status='inactive')
- **Protección de Seguros** → Actualiza `vehicle_insurance` automáticamente

**Conexiones:** `taxi_database.py`, `rate_limiter.py`

---

## 💎 Sistema Premium

### 📍 Canal: General
**Archivos:** `premium_commands.py`, `premium_exclusive_commands.py`

### Flujos:

#### 📋 Planes (`/ba_plans`)
- Información de suscripciones
- Botones dinámicos según plan actual
- Contacto para upgrade/gestión

#### 🔧 Administración (`/ba_admin_subs`)
- **Acciones:** upgrade, cancel, status, list
- Verificación de permisos admin
- Gestión de suscripciones por guild

#### 💎 Funciones Exclusivas
- **Estadísticas avanzadas** (`/ba_stats`)
- **Notificaciones personalizadas** (`/ba_notifications`)
- **Verificación del sistema** (`/ba_check_notifications`)
- **Exportación de datos** (`/ba_export`)

**Conexiones:** `subscription_manager.py`, `premium_utils.py`, `database_v2.py`

---

## 🛒 Sistema de Tienda

### 📍 Canal: Configurado por admin
**Archivos:** `shop_config.py`, debug en `taxi_admin.py`

### Flujos:

#### 📦 Configuración de Stock
- **Packs por tiers** → `shop_config.py:SHOP_PACKS`
- **Categorías** → `shop_config.py:PACK_CATEGORIES`
- **Límites y cooldowns** → `shop_config.py:TIER_CONFIG`

#### 🔍 Debug (`/debug_shop_stock`)
- Visualización del stock actual
- Agrupación por tiers
- Información de disponibilidad

#### 🛍️ Funciones de Tienda
- **Obtener pack** → `get_pack_by_id()`
- **Packs por tier** → `get_packs_by_tier()`
- **Disponibilidad** → `get_available_packs()`

**Conexiones:** `taxi_database.py:get_all_shop_stock()`, `taxi_admin.py`

---

## ⚙️ Sistema de Administración

### 📍 Canal: Admin configurado
**Archivo Principal:** `taxi_admin.py`

### Flujos:

#### 🎛️ Panel Administrativo
- **Crear panel** → `AdminPanelView`
- **Botones dinámicos:** Seguros pendientes, configuraciones
- **Recrear panel** → `recreate_admin_panel()`

#### 🔧 Configuración de Canales (`/ba_admin_channels_setup`)
- Configuración completa del servidor
- Integra setup de notificaciones de mecánico
- Guarda configuraciones → `save_admin_channels()`

#### 📊 Gestión de Seguros Pendientes
- **Vista de seguros** → `PendingInsuranceView`
- **Selector de seguros** → `PendingInsuranceSelect`
- **Confirmación/Rechazo** → `InsuranceConfirmationView`
- **Coordinación con canal mecánico** → Verificación de estado en tiempo real
- **Prevención de duplicados** → Mensaje amigable si ya fue procesado

#### 🚕 Administración de Taxi
- **Estadísticas** (`/taxi_admin_stats`)
- **Configurar tarifas** (`/taxi_admin_tarifa`)
- **Renovar licencias** (`/taxi_admin_refresh`)
- **Configurar expiración** (`/taxi_admin_expiration`)
- **Leaderboard** (`/taxi_admin_leaderboard`)

**Conexiones:** `taxi_database.py`, `mechanic_system.py`, `rate_limiter.py`

---

## 🔄 Rate Limiting

### 📍 Sistema Transversal
**Archivo:** `rate_limiter.py`

### Implementación:
```python
# Manual rate limiting check
from rate_limiter import rate_limiter
if not await rate_limiter.check_and_record(interaction, "command_name"):
    return
```

### Configuración:
- **Por usuario:** límites individuales
- **Por servidor:** límites globales del guild
- **Cooldowns:** tiempo entre usos
- **Configuraciones específicas** por comando en `command_limits`

**Aplicado en:** TODOS los comandos del sistema

---

## 🎛️ BaseView - Sistema de Vistas

### 📍 Sistema Transversal de UI
**Archivos:** `mechanic_system.py`, `taxi_admin.py`

### Problema Resuelto:
- **Error asyncio:** `TypeError: a coroutine was expected, got None`
- **Views sin timeout:** Métodos `on_timeout` no async

### Implementación:
```python
class BaseView(discord.ui.View):
    """Clase base para todas las vistas con manejo correcto de timeout"""
    
    async def on_timeout(self):
        """Manejar timeout de la vista de forma asíncrona"""
        for item in self.children:
            item.disabled = True

# Uso en nuevas vistas
class MiVista(BaseView):  # En lugar de discord.ui.View
    def __init__(self):
        super().__init__(timeout=300)
```

### Cuándo Usar:
- **SIEMPRE** para nuevas vistas Discord
- **Reemplazar** `discord.ui.View` por `BaseView`
- **Vistas críticas ya migradas:**
  - `VehicleInsuranceSelectView`
  - `InsuranceConfirmationView` 
  - `AdminPanelView`
  - `PendingInsuranceView`

### Beneficios:
- ✅ Previene errores de timeout
- ✅ Manejo async correcto
- ✅ Cierre limpio de recursos

**Ubicación:** Definida al inicio de archivos con Views

---

## 📁 Estructura de Archivos Clave

```
├── BunkerAdvice_V2.py          # Comandos principales de bunkers
├── banking_system.py           # Sistema bancario completo
├── mechanic_system.py          # Mecánico, seguros y escuadrones
├── taxi_system.py              # Sistema de taxi usuario
├── taxi_admin.py               # Administración y panel admin
├── premium_commands.py         # Comandos premium básicos
├── premium_exclusive_commands.py # Funciones premium exclusivas
├── shop_config.py              # Configuración de tienda
├── rate_limiter.py             # Sistema de rate limiting
├── taxi_database.py            # Base de datos principal
├── database_v2.py              # Base de datos bunkers
└── premium_utils.py            # Utilidades premium
```

---

## 🔍 Búsqueda Rápida

**Para encontrar:**
- **Comando específico** → Buscar `@app_commands.command(name="comando")`
- **Función de BD** → Buscar en `taxi_database.py` o `database_v2.py`
- **Rate limiting** → Todos los archivos tienen `rate_limiter.check_and_record`
- **Configuración admin** → `taxi_admin.py` sección específica
- **Embedds y UI** → Buscar `discord.Embed` o `discord.ui.View`
- **Notificaciones** → Buscar `send_` o `notification`
- **BaseView implementation** → Buscar `class BaseView` en archivos con Views
- **Views con timeout** → Buscar `class.*BaseView` para vistas migradas
- **Error de timeout** → Usar `BaseView` en lugar de `discord.ui.View`

Esta guía te permite navegar rápidamente a cualquier funcionalidad del sistema. 🚀