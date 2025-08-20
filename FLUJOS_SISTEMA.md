# 🔄 FLUJOS DEL SISTEMA - GUÍA RÁPIDA

## 📋 ÍNDICE RÁPIDO
- [🏗️ Arquitectura Modular](#-arquitectura-modular-nueva)
- [🏦 Sistema Bancario](#-sistema-bancario)
- [🏢 Sistema de Bunkers](#-sistema-de-bunkers)
- [🔧 Sistema de Mecánico/Seguros](#-sistema-de-mecánicoseguros)
- [🚗 Sistema de Taxi](#-sistema-de-taxi)
- [👥 Sistema de Escuadrones](#-sistema-de-escuadrones)
- [💎 Sistema Premium](#-sistema-premium)
- [🛒 Sistema de Tienda](#-sistema-de-tienda)
- [⚙️ Sistema de Administración](#️-sistema-de-administración)
- [🎯 Patrones para Nuevos Módulos](#-patrones-para-nuevos-módulos)

---

## 🏗️ Arquitectura Modular (NUEVA)

### 📍 Sistema de UserManager Centralizado
**Archivo Principal:** `core/user_manager.py` ⭐ **NUEVO MÓDULO**

### 🎯 **Filosofía de Modularización:**
La refactorización implementó una **separación clara** entre:
- **🧑‍💻 Gestión de Usuarios** → `core/user_manager.py`
- **⚙️ Lógica de Sistema** → Archivos específicos (`taxi_database.py`, etc.)

### 📊 **Migración Completada:**
✅ **4 Módulos Migrados Exitosamente:**
1. **`welcome_system.py`** - Bienvenida y registro
2. **`banking_system.py`** - Sistema bancario  
3. **`mechanic_system.py`** - Mecánico y seguros
4. **`taxi_admin.py`** - Administración de taxi

✅ **1 Módulo Analizado (No requiere migración):**
- **`BunkerAdvice_V2.py`** - Solo funciones de sistema

### 🏗️ **Estructura Modular Actual:**
```
SCUM/
├── core/                               ⭐ NUEVO MÓDULO CENTRALIZADO
│   ├── __init__.py                     # Configuración del módulo
│   └── user_manager.py                 # Sistema de usuarios (695+ líneas)
│
├── welcome_system.py                   ✅ MIGRADO (funciones de usuario)
├── banking_system.py                   ✅ MIGRADO (funciones de usuario)  
├── mechanic_system.py                  ✅ MIGRADO (funciones de usuario)
├── taxi_admin.py                       ✅ MIGRADO (funciones de usuario)
├── BunkerAdvice_V2.py                  ✅ NO REQUIERE MIGRACIÓN (sistema)
│
├── taxi_database.py                    🔄 SOLO FUNCIONES DE SISTEMA
├── database_v2.py                      ➖ ESPECÍFICO BUNKERS
├── server_database.py                  ➖ ESPECÍFICO MONITOREO
```

### 🎯 **UserManager - Funciones Centralizadas:**

#### **Gestión Básica de Usuarios:**
```python
- register_user(discord_id, guild_id, username, display_name, timezone, ingame_name)
- get_user_by_discord_id(discord_id, guild_id)  
- get_user_by_id(user_id)
- update_user_last_active(user_id)
- user_exists(user_id)
```

#### **Gestión Financiera Completa:**
```python
- get_user_balance(user_id)
- add_money(user_id, amount, description)
- subtract_money(user_id, amount, description)
- transfer_money(from_user_id, to_user_id, amount, description)
- transfer_money_by_discord_id(sender_discord_id, receiver_discord_id, amount)
```

#### **Sistema de Recompensas y Transacciones:**
```python
- add_daily_reward(user_id, amount)
- get_last_daily_claim(user_id)
- get_user_transactions(user_id, limit)
- get_user_count(guild_id)
```

#### **Gestión de Idiomas y Localización:**
```python
- update_user_language(user_id, language)
- get_user_language(user_id)
- get_user_language_by_discord_id(discord_id, guild_id)
- update_user_timezone(discord_id, guild_id, timezone)
```

### 🔗 **API de Compatibilidad:**
```python
# Funciones de compatibilidad (mantienen código existente funcionando)
from core.user_manager import get_user_by_discord_id, get_user_balance, add_money

# Uso directo del UserManager
from core.user_manager import user_manager
await user_manager.register_user(...)
```

### ⚙️ **Funciones de Sistema NO Migradas (Correctamente):**
```python
# Estas permanecen en taxi_database.py (funciones de sistema/configuración):
- load_all_channel_configs()      # Configuración de canales
- save_channel_config()           # Configuración de canales  
- get_system_stats()              # Estadísticas del sistema
- get_user_taxi_stats()           # Específicas del taxi
- get_reset_schedules()           # Específicas de bunkers
- get_users_for_reset_alert()     # Alertas de bunkers
```

---

## 🏦 Sistema Bancario

### 📍 Canal: General/Banking
**Archivo Principal:** `banking_system.py` ✅ **MIGRADO**

### Flujos:
- **Balance** (`/banco_balance`)
  - Verifica registro del usuario
  - Consulta balance en BD → ✅ **`core/user_manager.py:get_user_balance()`** 
  - Muestra embed con dinero disponible
  - 🔧 **Fix aplicado:** Manejo robusto de campos `joined_at`/`created_at`

- **Transferir** (`/banco_transferir`)
  - Validaciones: no auto-transferencia, cantidad válida
  - Verifica fondos suficientes
  - Ejecuta transacción → ✅ **`core/user_manager.py:transfer_money_by_discord_id()`**
  - Registra en historial automáticamente

- **Historial** (`/banco_historial`)
  - Obtiene transacciones → ✅ **`core/user_manager.py:get_user_transactions()`**
  - Muestra últimas N transacciones con paginación

**Conexiones:** ✅ **`core/user_manager.py`** (funciones de usuario), `taxi_database.py` (configuración), `rate_limiter.py`

---

## 🏢 Sistema de Bunkers

### 📍 Canal: Configurado por admin
**Archivo Principal:** `BunkerAdvice_V2.py` ✅ **NO REQUIERE MIGRACIÓN**

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
**Estado:** ✅ **Solo funciones de sistema - NO MIGRADO CORRECTAMENTE**

---

## 🔧 Sistema de Mecánico/Seguros

### 📍 Canal: Taller (configurado por admin)
**Archivo Principal:** `mechanic_system.py` ✅ **MIGRADO**

### Flujos:

#### 🛡️ Solicitar Seguro (`/seguro_solicitar`)
- Modal para datos del vehículo
- Verificación: usuario registrado → ✅ **`core/user_manager.py:get_user_by_discord_id()`**
- Verificación: vehículo no asegurado → `check_vehicle_insurance_status()`
- Selector de vehículos disponibles
- Pago desde balance → ✅ **`core/user_manager.py:subtract_money()`** (con registro automático de transacción)
- Creación de solicitud → `create_insurance_request()`
- Notificación a mecánicos

#### 🔍 Consultar Seguro (`/seguro_consultar`)
- Verifica usuario → ✅ **`core/user_manager.py:get_user_by_discord_id()`**
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

**Conexiones:** ✅ **`core/user_manager.py`** (funciones de usuario), `taxi_database.py` (específicas mecánico), `taxi_admin.py` (panel admin), `rate_limiter.py`

---

## 🚗 Sistema de Taxi

### 📍 Canal: Configurado por admin
**Archivo Principal:** `taxi_system.py`

### Flujos:

#### 🚕 Solicitar Taxi (`/taxi_solicitar`)
- Modal con origen/destino
- Verificación de usuario → **Candidato para migración** `get_user_by_discord_id()`
- Cálculo automático de tarifa → `calculate_fare()`
- Verificación de fondos → **Candidato para migración** `get_user_balance()`
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

**Administración:** `taxi_admin.py` ✅ **MIGRADO**
- Estadísticas, configuración de tarifas, renovación de licencias, etc.

**Conexiones:** `taxi_database.py`, ✅ **`taxi_admin.py` MIGRADO**, `rate_limiter.py`
**Estado:** ⚠️ **CANDIDATO PARA PRÓXIMA MIGRACIÓN** - Contiene funciones de usuario

---

## 👥 Sistema de Escuadrones

### 📍 Integrado en Mecánico
**Archivo Principal:** `mechanic_system.py` ✅ **MIGRADO** (sección Squadron)

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

**Conexiones:** ✅ **`core/user_manager.py`** (funciones de usuario), `taxi_database.py` (específicas escuadrón), `rate_limiter.py`

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
**Estado:** ⚠️ **CANDIDATO PARA ANÁLISIS** - Verificar si contiene funciones de usuario

---

## 🛒 Sistema de Tienda

### 📍 Canal: Configurado por admin
**Archivos:** `shop_config.py`, debug en `taxi_admin.py` ✅ **MIGRADO**

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
- **Compras de usuarios** → ✅ **Migrado en `taxi_admin.py`** para verificación de balance

**Conexiones:** ✅ **`core/user_manager.py`** (para compras), `taxi_database.py:get_all_shop_stock()`, ✅ **`taxi_admin.py` MIGRADO**

---

## ⚙️ Sistema de Administración

### 📍 Canal: Admin configurado
**Archivo Principal:** `taxi_admin.py` ✅ **MIGRADO**

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

#### 💰 Gestión Financiera Migrada
- **Transferencias** → ✅ **`core/user_manager.py:transfer_money()`**
- **Registro de usuarios** → ✅ **`core/user_manager.py:register_user()`**
- **Consulta de balances** → ✅ **`core/user_manager.py:get_user_balance()`**

**Conexiones:** ✅ **`core/user_manager.py`** (funciones de usuario), `taxi_database.py` (configuraciones), `mechanic_system.py`, `rate_limiter.py`

---

## 🎯 Patrones para Nuevos Módulos

### 🏗️ **Filosofía de Diseño Modular**

Al crear **nuevos módulos o funcionalidades**, seguir esta arquitectura:

#### 1️⃣ **Clasificar Funciones:**

**🧑‍💻 Funciones de Usuario (USAR UserManager):**
```python
# ✅ MIGRAR A core/user_manager.py o usar sus funciones
- Registro de usuarios
- Consulta de balances
- Transferencias de dinero
- Historial de transacciones
- Gestión de idiomas/timezone
- Recompensas y bonificaciones
```

**⚙️ Funciones de Sistema (NO migrar):**
```python
# ❌ MANTENER en archivos específicos
- Configuración de canales
- Estadísticas del sistema
- Lógica específica del módulo
- Configuraciones de servidor
- Operaciones de base de datos específicas
```

#### 2️⃣ **Patrón de Importación:**

**Para Módulos Nuevos:**
```python
# Importaciones estándar
import discord
from discord.ext import commands
from discord import app_commands

# Sistema modular - SIEMPRE incluir
from core.user_manager import user_manager, get_user_by_discord_id, get_user_balance
from taxi_database import taxi_db  # Solo para funciones de sistema
from rate_limiter import rate_limit, rate_limiter  # Rate limiting obligatorio

# Específicas del módulo
from mi_config import MI_CONFIG
```

#### 3️⃣ **Estructura de Comando Recomendada:**

```python
@app_commands.command(name="mi_comando", description="Descripción del comando")
@rate_limit("mi_comando")  # ✅ OBLIGATORIO - Rate limiting
async def mi_comando(interaction: discord.Interaction, parametro: str):
    """Mi nuevo comando siguiendo patrones modulares"""
    
    # 1. Verificar rate limiting
    if not await rate_limiter.check_and_record(interaction, "mi_comando"):
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # 2. Verificar usuario registrado (usar UserManager)
        user_data = await get_user_by_discord_id(
            str(interaction.user.id), 
            str(interaction.guild.id)
        )
        
        if not user_data:
            embed = discord.Embed(
                title="❌ Usuario No Registrado",
                description="Debes registrarte primero usando `/welcome`",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # 3. Lógica específica del módulo
        # Usar funciones de taxi_db solo para lógica de sistema
        
        # 4. Operaciones financieras (usar UserManager)
        if necesita_dinero:
            balance = await get_user_balance(user_data['user_id'])
            if balance < costo:
                # Manejar fondos insuficientes
                pass
            else:
                # Usar subtract_money del UserManager
                success = await user_manager.subtract_money(
                    user_data['user_id'], 
                    costo, 
                    f"Pago por {parametro}"
                )
        
        # 5. Respuesta exitosa
        embed = discord.Embed(
            title="✅ Operación Exitosa",
            description=f"Comando {parametro} ejecutado correctamente",
            color=0x00ff00
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error en mi_comando: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description="Ocurrió un error al procesar el comando",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
```

#### 4️⃣ **Patrón de UI Views (BaseView):**

```python
class BaseView(discord.ui.View):
    """Clase base para todas las vistas con manejo correcto de timeout"""
    
    async def on_timeout(self):
        """Manejar timeout de la vista de forma asíncrona"""
        for item in self.children:
            item.disabled = True

class MiNuevaView(BaseView):  # ✅ USAR BaseView, NO discord.ui.View
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.button(label="Mi Botón", style=discord.ButtonStyle.primary)
    async def mi_boton(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botón con patrón modular"""
        await interaction.response.defer(ephemeral=True)
        
        # Usar UserManager para operaciones de usuario
        user_data = await get_user_by_discord_id(
            str(interaction.user.id), 
            str(interaction.guild.id)
        )
        
        # Lógica del botón...
```

#### 5️⃣ **Testing Pattern:**

Para cada módulo nuevo, crear test:

```python
# test_mi_modulo_migration.py
async def test_mi_modulo():
    """Test del nuevo módulo siguiendo patrones"""
    
    # 1. Crear usuario de prueba
    success, result = await user_manager.register_user(
        discord_id="test_id", 
        guild_id="test_guild",
        username="test_user"
    )
    
    # 2. Probar funciones migradas
    user_data = await get_user_by_discord_id("test_id", "test_guild")
    balance = await get_user_balance(result['user_id'])
    
    # 3. Probar lógica específica del módulo
    # ...
    
    # 4. Limpiar datos de prueba
    # ...
```

#### 6️⃣ **Build System Integration:**

Actualizar `build.bat` si se crean nuevos directorios:

```batch
:: Si creas nuevos módulos en /modules
copy "modules\*.py" "%BUILD_FULL_DIR%\modules\" >nul 2>&1
```

### 🚀 **Beneficios de Seguir Este Patrón:**

1. **✅ Consistencia** - Todos los módulos siguen la misma arquitectura
2. **✅ Mantenibilidad** - Fácil debugging y extensión
3. **✅ Reutilización** - UserManager disponible para todo
4. **✅ Testing** - Patrones probados y verificados
5. **✅ Escalabilidad** - Base sólida para crecimiento

### 📋 **Checklist para Nuevos Módulos:**

- [ ] ¿Importa `core.user_manager` para funciones de usuario?
- [ ] ¿Usa `BaseView` en lugar de `discord.ui.View`?
- [ ] ¿Implementa rate limiting en todos los comandos?
- [ ] ¿Verifica registro de usuario al inicio?
- [ ] ¿Usa `user_manager` para operaciones financieras?
- [ ] ¿Mantiene funciones de sistema en archivos específicos?
- [ ] ¿Tiene test de verificación creado?
- [ ] ¿Maneja errores de manera robusta?

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
├── core/                           ⭐ NUEVO MÓDULO CENTRALIZADO
│   ├── __init__.py                 # Configuración del módulo
│   └── user_manager.py             # Sistema de usuarios (695+ líneas)
│
├── BunkerAdvice_V2.py              # Comandos principales de bunkers ✅ NO MIGRADO
├── banking_system.py               # Sistema bancario completo ✅ MIGRADO
├── mechanic_system.py              # Mecánico, seguros y escuadrones ✅ MIGRADO
├── taxi_system.py                  # Sistema de taxi usuario ⚠️ CANDIDATO
├── taxi_admin.py                   # Administración y panel admin ✅ MIGRADO
├── welcome_system.py               # Sistema de bienvenida ✅ MIGRADO
├── premium_commands.py             # Comandos premium básicos ⚠️ ANALIZAR
├── premium_exclusive_commands.py   # Funciones premium exclusivas ⚠️ ANALIZAR
├── shop_config.py                  # Configuración de tienda
├── rate_limiter.py                 # Sistema de rate limiting
├── taxi_database.py                # Base de datos principal (funciones sistema)
├── database_v2.py                  # Base de datos bunkers
└── premium_utils.py                # Utilidades premium
```

**Leyenda:**
- ✅ **MIGRADO** - Funciones de usuario movidas a UserManager
- ⚠️ **CANDIDATO** - Contiene funciones de usuario para migrar
- ⚠️ **ANALIZAR** - Verificar si contiene funciones de usuario
- ➖ **NO MIGRAR** - Solo funciones de sistema

---

## 🔍 Búsqueda Rápida

**Para encontrar:**
- **Comando específico** → Buscar `@app_commands.command(name="comando")`
- **Función de Usuario** → Buscar en `core/user_manager.py` ✅ **NUEVO**
- **Función de Sistema** → Buscar en `taxi_database.py` o `database_v2.py`
- **Rate limiting** → Todos los archivos tienen `rate_limiter.check_and_record`
- **Configuración admin** → `taxi_admin.py` sección específica ✅ **MIGRADO**
- **Embedds y UI** → Buscar `discord.Embed` o `discord.ui.View`
- **Notificaciones** → Buscar `send_` o `notification`
- **BaseView implementation** → Buscar `class BaseView` en archivos con Views
- **Views con timeout** → Buscar `class.*BaseView` para vistas migradas
- **Error de timeout** → Usar `BaseView` en lugar de `discord.ui.View`
- **Funciones migradas** → Importar desde `core.user_manager` ✅ **NUEVO**
- **Patrones modulares** → Seguir sección "Patrones para Nuevos Módulos" ✅ **NUEVO**

### 🎯 **Guía de Migración para Futuros Módulos:**

1. **Identificar funciones de usuario** → Migrar a UserManager
2. **Mantener funciones de sistema** → Dejar en archivos específicos
3. **Actualizar importaciones** → Usar `core.user_manager`
4. **Crear tests** → Verificar funcionalidad
5. **Seguir patrones** → Usar BaseView, rate limiting, manejo de errores

Esta guía te permite navegar rápidamente a cualquier funcionalidad del sistema y **implementar nuevos módulos siguiendo la arquitectura modular establecida**. 🚀