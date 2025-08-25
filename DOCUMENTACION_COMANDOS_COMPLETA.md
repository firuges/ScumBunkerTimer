# 📋 Documentación Completa de Comandos - Bot SCUM Discord

> **Bot:** BunkerAdvice V2  
> **Descripción:** Sistema completo de gestión para servidores SCUM con múltiples módulos integrados  
> **Versión:** V2.0  
> **Última actualización:** 24 de Agosto, 2025

---

## 📑 Tabla de Contenidos

- [🎯 Comandos Principales (Bunkers)](#-comandos-principales-bunkers)
- [🚖 Sistema de Taxi](#-sistema-de-taxi)
- [🏦 Sistema Bancario](#-sistema-bancario)
- [🔧 Sistema de Mecánico](#-sistema-de-mecánico)
- [🎫 Sistema de Tickets](#-sistema-de-tickets)
- [🏆 Sistema de Fame Points](#-sistema-de-fame-points)
- [🎉 Sistema de Bienvenida](#-sistema-de-bienvenida)
- [🔔 Sistema de Alertas de Reinicio](#-sistema-de-alertas-de-reinicio)
- [💎 Comandos Premium](#-comandos-premium)
- [⚙️ Comandos de Administración](#️-comandos-de-administración)
- [🛠️ Comandos de Super Admin](#️-comandos-de-super-admin)
- [📊 Sistema de Rate Limiting](#-sistema-de-rate-limiting)

---

## 🎯 Comandos Principales (Bunkers)

### Comandos Públicos

#### `/ba_add_server`
- **Descripción:** Agregar un nuevo servidor SCUM para tracking de bunkers
- **Parámetros:**
  - `name` (obligatorio): Nombre del servidor
  - `description` (opcional): Descripción del servidor
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_add_server name:Mi-Servidor description:Servidor principal`

#### `/ba_register_bunker`
- **Descripción:** Registrar tiempo de expiración de un bunker
- **Parámetros:**
  - `sector` (obligatorio): Sector del bunker (D1, C4, A1, A3, etc.)
  - `hours` (obligatorio): Horas hasta la apertura
  - `server` (opcional): Servidor donde está el bunker
  - `coordinates` (opcional): Coordenadas del bunker
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_register_bunker sector:D1 hours:5`

#### `/ba_check_bunker`
- **Descripción:** Verificar estado de un bunker específico
- **Parámetros:**
  - `sector` (obligatorio): Sector del bunker
  - `server` (opcional): Servidor donde está el bunker
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_check_bunker sector:D1`

#### `/ba_status_all`
- **Descripción:** Ver estado de todos los bunkers
- **Parámetros:**
  - `server` (opcional): Servidor específico (default: "Default")
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_status_all server:Mi-Servidor`

#### `/ba_list_servers`
- **Descripción:** Listar todos los servidores disponibles
- **Parámetros:** Ninguno
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_list_servers`

#### `/ba_remove_server`
- **Descripción:** Eliminar un servidor y todos sus bunkers
- **Parámetros:**
  - `server` (obligatorio): Nombre del servidor a eliminar
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_remove_server server:Servidor-Viejo`

#### `/ba_help`
- **Descripción:** Guía básica del bot
- **Parámetros:** Ninguno
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_help`

#### `/ba_my_usage`
- **Descripción:** Ver tu uso diario de bunkers
- **Parámetros:** Ninguno
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_my_usage`

#### `/ba_bot_status`
- **Descripción:** Ver el estado del bot en este servidor
- **Parámetros:** Ninguno
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_bot_status`

#### `/ba_suscripcion`
- **Descripción:** Ver información sobre planes de suscripción
- **Parámetros:** Ninguno
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_suscripcion`

---

## 🚖 Sistema de Taxi

### Comandos para Usuarios

#### `/taxi_solicitar`
- **Descripción:** Solicitar un taxi
- **Parámetros:**
  - `destino` (obligatorio): Zona de destino
  - `vehiculo` (opcional): Tipo de vehículo preferido
- **Permisos:** Usuarios registrados
- **Rate limit:** Aplicado
- **Uso:** `/taxi_solicitar destino:Aeropuerto vehiculo:SUV`

#### `/taxi_status`
- **Descripción:** Ver estado de tu solicitud de taxi
- **Parámetros:** Ninguno
- **Permisos:** Usuarios registrados
- **Rate limit:** Aplicado
- **Uso:** `/taxi_status`

#### `/taxi_cancelar`
- **Descripción:** Cancelar tu solicitud de taxi
- **Parámetros:** Ninguno
- **Permisos:** Usuarios registrados
- **Rate limit:** Aplicado
- **Uso:** `/taxi_cancelar`

#### `/taxi_zonas`
- **Descripción:** Ver zonas disponibles para taxi
- **Parámetros:** Ninguno
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/taxi_zonas`

#### `/taxi_tarifas`
- **Descripción:** Ver tarifas del servicio de taxi
- **Parámetros:** Ninguno
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/taxi_tarifas`

### Comandos de Administración del Taxi

#### `/taxi_admin_stats`
- **Descripción:** Ver estadísticas completas del sistema
- **Parámetros:** Ninguno
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/taxi_admin_stats`

#### `/taxi_admin_tarifa`
- **Descripción:** Configurar tarifas del sistema de taxi
- **Parámetros:**
  - `zona` (obligatorio): Zona a configurar
  - `precio_base` (obligatorio): Precio base del viaje
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/taxi_admin_tarifa zona:Centro precio_base:500`

#### `/taxi_admin_refresh`
- **Descripción:** Recrear el panel de administración
- **Parámetros:** Ninguno
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/taxi_admin_refresh`

#### `/taxi_admin_expiration`
- **Descripción:** Configurar tiempo de expiración de solicitudes
- **Parámetros:**
  - `minutes` (obligatorio): Tiempo en minutos (1-120, default: 15)
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/taxi_admin_expiration minutes:20`

#### `/taxi_admin_leaderboard`
- **Descripción:** Ver clasificación de conductores por rendimiento
- **Parámetros:**
  - `limit` (opcional): Número de conductores a mostrar (1-20, default: 10)
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/taxi_admin_leaderboard limit:15`

#### `/pending_packages`
- **Descripción:** Ver paquetes pendientes de entrega
- **Parámetros:** Ninguno
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/pending_packages`

---

## 🏦 Sistema Bancario

### Comandos para Usuarios

#### `/banco_balance`
- **Descripción:** Ver tu balance actual
- **Parámetros:** Ninguno
- **Permisos:** Usuarios registrados
- **Rate limit:** Aplicado
- **Uso:** `/banco_balance`

#### `/banco_transferir`
- **Descripción:** Transferir dinero a otro usuario
- **Parámetros:**
  - `usuario` (obligatorio): Usuario destinatario
  - `cantidad` (obligatorio): Cantidad a transferir
  - `concepto` (opcional): Concepto de la transferencia
- **Permisos:** Usuarios registrados
- **Rate limit:** Aplicado
- **Límites:** Máximo $1,000,000 por transferencia
- **Uso:** `/banco_transferir usuario:@Usuario cantidad:1000 concepto:Préstamo`

#### `/banco_historial`
- **Descripción:** Ver historial de transacciones
- **Parámetros:**
  - `limite` (opcional): Número de transacciones (1-20, default: 10)
- **Permisos:** Usuarios registrados
- **Rate limit:** Aplicado
- **Uso:** `/banco_historial limite:15`

### Comandos de Administración Bancaria

#### `/banco_admin_setup`
- **Descripción:** Configurar canal del banco
- **Parámetros:**
  - `canal` (obligatorio): Canal donde configurar el sistema bancario
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/banco_admin_setup canal:#banco`

---

## 🔧 Sistema de Mecánico

### Comandos para Usuarios

#### `/seguro_solicitar`
- **Descripción:** Solicitar seguro para tu vehículo
- **Parámetros:** Se configura mediante interfaz interactiva
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/seguro_solicitar`

#### `/seguro_consultar`
- **Descripción:** Consultar seguros de tus vehículos
- **Parámetros:** Ninguno
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/seguro_consultar`

### Comandos para Mecánicos

#### `/mechanic_notifications`
- **Descripción:** Configurar notificaciones de mecánico
- **Parámetros:**
  - `enabled` (obligatorio): Recibir notificaciones por DM
- **Permisos:** Mecánicos registrados
- **Rate limit:** Aplicado
- **Uso:** `/mechanic_notifications enabled:true`

### Comandos de Administración del Mecánico

#### `/mechanic_admin_register`
- **Descripción:** Registrar un usuario como mecánico
- **Parámetros:**
  - `user` (obligatorio): Usuario a registrar como mecánico
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/mechanic_admin_register user:@Usuario`

#### `/mechanic_admin_remove`
- **Descripción:** Eliminar un mecánico registrado
- **Parámetros:**
  - `user` (obligatorio): Mecánico a eliminar del registro
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/mechanic_admin_remove user:@Mecanico`

#### `/mechanic_admin_list`
- **Descripción:** Listar todos los mecánicos registrados
- **Parámetros:** Ninguno
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/mechanic_admin_list`

#### `/mechanic_admin_config_pvp`
- **Descripción:** Configurar recargo PVP para seguros
- **Parámetros:**
  - `percentage` (obligatorio): Porcentaje de recargo para zonas PVP
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/mechanic_admin_config_pvp percentage:25`

#### `/mechanic_admin_set_price`
- **Descripción:** Establecer precio personalizado para un tipo de vehículo
- **Parámetros:**
  - `vehicle_type` (obligatorio): Tipo de vehículo (ranger, laika, ww, avion, moto)
  - `price` (obligatorio): Precio del seguro en dólares del juego
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/mechanic_admin_set_price vehicle_type:ranger price:5000`

#### `/mechanic_admin_list_prices`
- **Descripción:** Ver todos los precios personalizados
- **Parámetros:** Ninguno
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/mechanic_admin_list_prices`

#### `/mechanic_admin_set_limit`
- **Descripción:** Establecer límite de vehículos por miembro
- **Parámetros:**
  - `vehicle_type` (obligatorio): Tipo de vehículo
  - `limit_per_member` (obligatorio): Cantidad máxima por miembro
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/mechanic_admin_set_limit vehicle_type:moto limit_per_member:2`

#### `/mechanic_admin_list_limits`
- **Descripción:** Ver todos los límites de vehículos
- **Parámetros:** Ninguno
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/mechanic_admin_list_limits`

#### `/mechanic_admin_setup`
- **Descripción:** Configurar canal de mecánico
- **Parámetros:**
  - `mechanic_channel` (obligatorio): Canal para sistema de mecánico y seguros
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/mechanic_admin_setup mechanic_channel:#mecanico`

### Comandos de Escuadrones

#### `/squadron_admin_config_limits`
- **Descripción:** Configurar límites globales de vehículos por escuadrón
- **Parámetros:**
  - `vehicles_per_member` (opcional): Vehículos permitidos por miembro (default: 2)
  - `max_total_vehicles` (opcional): Límite máximo total por escuadrón (default: 50)
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/squadron_admin_config_limits vehicles_per_member:3 max_total_vehicles:75`

#### `/squadron_admin_view_config`
- **Descripción:** Ver configuración actual de límites de escuadrones
- **Parámetros:** Ninguno
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/squadron_admin_view_config`

#### `/squadron_admin_remove_member`
- **Descripción:** Remover un miembro de su escuadrón
- **Parámetros:**
  - `user` (obligatorio): Usuario a remover del escuadrón
  - `reason` (opcional): Razón de la remoción
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/squadron_admin_remove_member user:@Usuario reason:Inactividad`

#### `/squadron_admin_view_member`
- **Descripción:** Ver información detallada de un miembro de escuadrón
- **Parámetros:**
  - `user` (obligatorio): Usuario a consultar
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/squadron_admin_view_member user:@Usuario`

#### `/squadron_admin_cleanup`
- **Descripción:** Limpiar mensajes del bot en canales de escuadrones y mecánico
- **Parámetros:**
  - `channel_type` (opcional): Tipo de canal a limpiar
  - `limit` (opcional): Número máximo de mensajes (default: 50)
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/squadron_admin_cleanup limit:100`

---

## 🎫 Sistema de Tickets

### Comandos de Tickets

#### `/ticket_setup`
- **Descripción:** Configurar panel de tickets
- **Parámetros:**
  - `channel` (obligatorio): Canal donde se colocará el panel de tickets
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/ticket_setup channel:#tickets`

#### `/ticket_close`
- **Descripción:** Cerrar un ticket específico
- **Parámetros:**
  - `ticket_number` (obligatorio): Número del ticket a cerrar
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/ticket_close ticket_number:001`

#### `/ticket_list`
- **Descripción:** Listar tickets activos
- **Parámetros:** Ninguno
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/ticket_list`

#### `/ticket_debug_restore`
- **Descripción:** Forzar restauración de vistas de tickets
- **Parámetros:** Ninguno
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/ticket_debug_restore`

---

## 🏆 Sistema de Fame Points

### Comandos de Fame Points

#### `/fame_rewards_setup`
- **Descripción:** Configurar panel de Fame Point Rewards
- **Parámetros:**
  - `rewards_channel` (opcional): Canal para panel de rankings y reclamaciones
  - `notifications_channel` (opcional): Canal para notificaciones de admins
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/fame_rewards_setup rewards_channel:#fame-rewards notifications_channel:#admin-fame`

#### `/fame_config`
- **Descripción:** Configurar valores de fama disponibles
- **Parámetros:**
  - `values` (obligatorio): Valores separados por comas (ej: 100,500,1000,2000,5000,10000,15000)
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/fame_config values:100,500,1000,2000,5000,10000,15000`

---

## 🎉 Sistema de Bienvenida

### Comandos para Usuarios

#### `/welcome_registro`
- **Descripción:** Registrarse para recibir el welcome pack
- **Parámetros:** Se configura mediante interfaz interactiva
- **Permisos:** Todos los usuarios
- **Rate limit:** No especificado
- **Uso:** `/welcome_registro`

#### `/welcome_status`
- **Descripción:** Ver tu estado de registro
- **Parámetros:** Ninguno
- **Permisos:** Todos los usuarios
- **Rate limit:** No especificado
- **Uso:** `/welcome_status`

#### `/idioma_cambiar`
- **Descripción:** Cambiar tu idioma preferido del sistema
- **Parámetros:** Se configura mediante interfaz interactiva
- **Permisos:** Todos los usuarios
- **Rate limit:** No especificado
- **Uso:** `/idioma_cambiar`

### Comandos de Administración del Welcome

#### `/welcome_admin_setup`
- **Descripción:** Configurar sistema de bienvenida
- **Parámetros:**
  - `canal` (obligatorio): Canal donde configurar el sistema de bienvenida
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/welcome_admin_setup canal:#bienvenida`

---

## 🔔 Sistema de Alertas de Reinicio

### Comandos para Usuarios

#### `/ba_reset_alerts`
- **Descripción:** Gestionar alertas de reinicio de servidores
- **Parámetros:**
  - `action` (obligatorio): Acción a realizar
  - `server_name` (opcional): Nombre del servidor SCUM
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_reset_alerts action:subscribe server_name:Mi-Servidor`

### Comandos de Administración de Alertas

#### `/ba_admin_resethour_add`
- **Descripción:** Agregar horario de reinicio del servidor
- **Parámetros:**
  - `server_name` (obligatorio): Nombre del servidor SCUM
  - `reset_time` (obligatorio): Hora del reinicio (formato HH:MM)
  - `timezone` (opcional): Zona horaria
  - `days` (opcional): Días de la semana (1=Lun, 7=Dom)
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_resethour_add server_name:Mi-Servidor reset_time:14:30 timezone:America/Montevideo days:1,2,3,4,5,6,7`

#### `/ba_admin_resethour_remove`
- **Descripción:** Eliminar horario de reinicio
- **Parámetros:**
  - `server_name` (obligatorio): Nombre del servidor SCUM
  - `schedule_id` (obligatorio): ID del horario a eliminar
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_resethour_remove server_name:Mi-Servidor schedule_id:1`

#### `/ba_admin_resethour_info`
- **Descripción:** Ver horarios de reinicio configurados
- **Parámetros:**
  - `server_name` (opcional): Nombre del servidor (deja vacío para ver todos)
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_resethour_info server_name:Mi-Servidor`

#### `/ba_admin_test_reset_alert`
- **Descripción:** Enviar alerta de reset de prueba
- **Parámetros:**
  - `server_name` (obligatorio): Nombre del servidor SCUM
  - `minutes_before` (opcional): Minutos antes del reinicio (default: 15)
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_test_reset_alert server_name:Mi-Servidor minutes_before:30`

---

## 💎 Comandos Premium

### Comandos de Planes Premium

#### `/ba_plans`
- **Descripción:** Ver planes de suscripción disponibles
- **Parámetros:** Ninguno
- **Permisos:** Todos los usuarios
- **Rate limit:** Aplicado
- **Uso:** `/ba_plans`

### Comandos Exclusivos Premium

#### `/ba_stats`
- **Descripción:** Estadísticas avanzadas de bunkers
- **Parámetros:**
  - `server` (opcional): Servidor específico (default: "Default")
- **Permisos:** Usuarios premium
- **Rate limit:** Aplicado
- **Características:** Gráficos de actividad, análisis temporal
- **Uso:** `/ba_stats server:Mi-Servidor`

#### `/ba_notifications`
- **Descripción:** Configurar notificaciones avanzadas
- **Parámetros:**
  - `server` (opcional): Servidor donde está el bunker (default: "Default")
  - `bunker_sector` (opcional): Sector del bunker (default: "all_sectors")
  - `notification_type` (opcional): Tipo de notificación (default: "all")
  - `role_mention` (opcional): Rol a mencionar
  - `enabled` (opcional): Activar/desactivar notificaciones (default: true)
- **Permisos:** Usuarios premium
- **Rate limit:** Aplicado
- **Características:** DM personal, menciones de rol, alertas por sector
- **Uso:** `/ba_notifications server:Mi-Servidor bunker_sector:D1 notification_type:expiring role_mention:@Bunkers enabled:true`

#### `/ba_check_notifications`
- **Descripción:** Verificar estado del sistema de notificaciones
- **Parámetros:** Ninguno
- **Permisos:** Usuarios premium
- **Rate limit:** Aplicado
- **Uso:** `/ba_check_notifications`

#### `/ba_export`
- **Descripción:** Exportar datos de bunkers
- **Parámetros:**
  - `format_type` (opcional): Formato de exportación (default: "json")
  - `server` (opcional): Servidor específico (default: "Default")
- **Permisos:** Usuarios premium
- **Rate limit:** Aplicado
- **Formatos disponibles:** JSON (próximamente: CSV, Excel)
- **Uso:** `/ba_export format_type:json server:Mi-Servidor`

---

## ⚙️ Comandos de Administración

### Configuración de Canales

#### `/ba_admin_channels_setup`
- **Descripción:** Configurar todos los canales del sistema BunkerAdvice
- **Parámetros:**
  - `welcome_channel` (opcional): Canal para sistema de bienvenida
  - `bank_channel` (opcional): Canal para sistema bancario
  - `taxi_channel` (opcional): Canal para sistema de taxi
  - `mechanic_channel` (opcional): Canal para sistema de mecánico
  - `ticket_channel` (opcional): Canal para sistema de tickets
- **Permisos:** Administradores del servidor
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_channels_setup welcome_channel:#welcome bank_channel:#banco taxi_channel:#taxi`

### Gestión de Premium y Suscripciones

#### `/ba_admin_subs`
- **Descripción:** Gestionar suscripciones premium
- **Parámetros:**
  - `action` (obligatorio): Acción (cancel, upgrade, status, list)
  - `guild_id` (opcional): ID del servidor Discord
  - `plan` (opcional): Tipo de plan para upgrade (default: "premium")
- **Permisos:** Super admins del bot
- **Rate limit:** Aplicado
- **Uso:** `/ba_admin_subs action:upgrade guild_id:123456789 plan:premium`

### Rate Limiting y Diagnóstico

#### `/rate_limit_stats`
- **Descripción:** Ver estadísticas de rate limiting
- **Parámetros:**
  - `usuario` (opcional): Usuario específico para ver sus estadísticas
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/rate_limit_stats usuario:@Usuario`

#### `/rate_limit_reset`
- **Descripción:** Resetear límites de un usuario
- **Parámetros:**
  - `usuario` (obligatorio): Usuario cuyos límites resetear
  - `comando` (opcional): Comando específico a resetear
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/rate_limit_reset usuario:@Usuario comando:ba_register_bunker`

#### `/rate_limit_test`
- **Descripción:** Probar el sistema de rate limiting
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** Aplicado
- **Uso:** `/rate_limit_test`

---

## 🛠️ Comandos de Super Admin

### Gestión del Bot

#### `/mi_id`
- **Descripción:** Mostrar tu ID de Discord
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/mi_id`

#### `/ba_admin_status`
- **Descripción:** Ver estado de suscripción del servidor
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** Aplicado
- **Uso:** `/ba_admin_status`

#### `/ba_admin_upgrade`
- **Descripción:** Dar premium al servidor actual
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** Aplicado
- **Uso:** `/ba_admin_upgrade`

#### `/ba_admin_cancel`
- **Descripción:** Quitar premium del servidor actual
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** Aplicado
- **Uso:** `/ba_admin_cancel`

#### `/ba_admin_list`
- **Descripción:** Listar todas las suscripciones
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_list`

### Configuración del Bot

#### `/ba_admin_setup_status`
- **Descripción:** Configurar canal de estado del bot
- **Parámetros:**
  - `channel` (obligatorio): Canal para estado del bot
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_setup_status channel:#bot-status`

#### `/ba_admin_public_status`
- **Descripción:** Configurar canal de estado público simplificado
- **Parámetros:**
  - `channel` (obligatorio): Canal para estado público
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_public_status channel:#estado-publico`

#### `/ba_admin_resync`
- **Descripción:** Forzar resincronización de comandos
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** Aplicado
- **Uso:** `/ba_admin_resync`

### Diagnóstico y Debug

#### `/ba_admin_debug_servers`
- **Descripción:** Ver servidores en la base de datos
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_debug_servers`

#### `/ba_admin_debug_user_cache`
- **Descripción:** Diagnosticar cache del bot para un usuario
- **Parámetros:**
  - `user_id` (opcional): ID del usuario a verificar
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_debug_user_cache user_id:123456789`

#### `/ba_admin_debug_channels`
- **Descripción:** Diagnosticar configuración de canales
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_debug_channels`

#### `/ba_admin_fix_channels`
- **Descripción:** Corregir configuraciones de canales inconsistentes
- **Parámetros:**
  - `dry_run` (opcional): Solo mostrar cambios sin aplicarlos (default: true)
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_fix_channels dry_run:false`

### Migración y Mantenimiento

#### `/ba_admin_migrate_timezones`
- **Descripción:** Migrar timezones de usuarios existentes
- **Parámetros:**
  - `target_timezone` (opcional): Timezone a asignar (default: "America/Montevideo")
  - `dry_run` (opcional): Solo mostrar cambios (default: true)
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_migrate_timezones target_timezone:America/Montevideo dry_run:false`

### Control del Bot

#### `/ba_admin_shutdown`
- **Descripción:** Apagar el bot de forma segura
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** Aplicado
- **Características:** Envía notificaciones antes del apagado
- **Uso:** `/ba_admin_shutdown`

#### `/ba_admin_guide`
- **Descripción:** Obtener URL de la guía completa
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Uso:** `/ba_admin_guide`

#### `/bot_presentacion`
- **Descripción:** Ver presentación completa del bot
- **Parámetros:** Ninguno
- **Permisos:** Super admins del bot
- **Rate limit:** No especificado
- **Características:** Muestra toda la funcionalidad disponible
- **Uso:** `/bot_presentacion`

### Debug de Funcionalidades

#### `/debug_shop_stock`
- **Descripción:** Ver stock actual de la tienda
- **Parámetros:** Ninguno
- **Permisos:** Administradores del servidor
- **Rate limit:** Aplicado
- **Uso:** `/debug_shop_stock`

---

## 📊 Sistema de Rate Limiting

El bot implementa un sistema avanzado de rate limiting para prevenir spam y abuso:

### Características del Rate Limiting

- **Límites por Usuario:** Cada usuario tiene límites individuales por comando
- **Límites por Servidor:** Límites globales por servidor Discord
- **Cooldowns:** Tiempo de espera entre usos consecutivos
- **Configuración Dinámica:** Diferentes límites por comando

### Comandos Afectados

Comandos con rate limiting aplicado:
- Todos los comandos `ba_*` principales
- Comandos del sistema de taxi
- Comandos del sistema bancario
- Comandos del sistema de mecánico
- Comandos premium

### Bypass del Rate Limiting

- **Super Admins:** Pueden usar comandos administrativos sin límites
- **Premium:** Límites más generosos para usuarios premium
- **Reset Manual:** Los admins pueden resetear límites de usuarios específicos

---

## 🔒 Niveles de Permisos

### 👤 Usuarios Públicos
- Comandos básicos de bunkers
- Visualización de información
- Registro en sistemas

### 🎓 Usuarios Registrados
- Acceso completo al sistema bancario
- Solicitudes de taxi y seguros
- Historial personal

### 💎 Usuarios Premium
- Comandos exclusivos premium
- Estadísticas avanzadas
- Notificaciones personalizadas
- Exportación de datos

### 🛡️ Administradores del Servidor
- Configuración de sistemas
- Gestión de usuarios locales
- Estadísticas del servidor
- Configuración de canales

### 👑 Super Administradores del Bot
- Control total del bot
- Gestión de suscripciones
- Comandos de diagnóstico
- Migración de datos

---

## 📋 Resumen de Funcionalidades

### 🎯 Bunkers (Core)
- **15 comandos** para gestión completa de bunkers
- Soporte multi-servidor
- Sistema de coordenadas
- Rate limiting avanzado

### 🚖 Sistema de Taxi
- **11 comandos** (6 usuario + 5 admin)
- Sistema de solicitudes
- Gestión de conductores
- Tarifas configurables

### 🏦 Sistema Bancario
- **4 comandos** (3 usuario + 1 admin)
- Transferencias seguras
- Historial completo
- Canje diario $500

### 🔧 Sistema de Mecánico
- **20 comandos** para seguros de vehículos
- Gestión de mecánicos
- Límites por escuadrón
- Precios personalizables

### 🎫 Sistema de Tickets
- **4 comandos** para soporte
- Vistas persistentes
- Gestión automática

### 🏆 Sistema de Fame Points
- **2 comandos** para reclamación de premios
- Rankings automáticos
- Notificaciones a admins

### 🎉 Sistema de Bienvenida
- **4 comandos** para nuevos usuarios
- Registro interactivo
- Soporte multiidioma

### 🔔 Alertas de Reinicio
- **5 comandos** para notificaciones
- Múltiples zonas horarias
- Suscripciones personalizadas

### 💎 Funciones Premium
- **4 comandos exclusivos**
- Estadísticas avanzadas
- Exportación de datos

### ⚙️ Administración
- **50+ comandos administrativos**
- Configuración completa
- Diagnóstico avanzado
- Rate limiting

---

## 🚀 Total de Comandos Disponibles

**🎯 Total General: 100+ comandos únicos**

- **Comandos Públicos:** ~25
- **Comandos de Usuario:** ~30
- **Comandos Premium:** ~4
- **Comandos de Admin Servidor:** ~25
- **Comandos de Super Admin:** ~20
- **Comandos de Diagnóstico:** ~10

---

## 📞 Soporte y Contacto

Para soporte técnico o dudas sobre comandos específicos:

- **Discord:** Contacta a los administradores del servidor
- **Documentación:** `/ba_help` para guía básica
- **Estado del Bot:** `/ba_bot_status` para verificar funcionamiento
- **Guía Completa:** `/ba_admin_guide` (solo admins)

---

*Documentación generada automáticamente el 24 de Agosto, 2025*  
*Bot Version: BunkerAdvice V2.0*  
*Sistemas: Bunkers, Taxi, Bancario, Mecánico, Tickets, Fame Points, Premium*