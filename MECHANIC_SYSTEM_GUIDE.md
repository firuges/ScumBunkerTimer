# 🔧 Sistema de Mecánico - Guía Completa

## 📋 Resumen del Sistema

El Sistema de Mecánico permite a los jugadores solicitar seguros para sus vehículos en SCUM y a los mecánicos gestionar estas solicitudes.

## 🚗 Tipos de Vehículos Soportados

### Vehículos SCUM Oficiales
- **Ranger**: $1,200
- **Laika**: $1,500  
- **WW (Willys Wagon)**: $900
- **Moto**: $500
- **Avion**: $3,500

### Modificador de Zona
- **Zona PVE**: Precio normal
- **Zona PVP**: +25% de recargo (configurable por administradores)

## 👥 Roles y Permisos

### 👤 Usuarios Regulares
**Requisitos:**
- Estar registrado en el sistema (`/welcome_registro`)
- Tener nombre InGame configurado

**Pueden usar:**
- `/seguro_solicitar` - Solicitar seguro para vehículo
- `/seguro_consultar` - Ver seguros activos
- Botones del panel interactivo

### 🔧 Mecánicos Registrados
**Cómo convertirse en mecánico:**
- Solo administradores pueden registrar mecánicos usando `/mechanic_admin_register @usuario`

**Permisos adicionales:**
- `/mechanic_notifications true/false` - **SOLO mecánicos** pueden configurar sus notificaciones DM
- Botón "Panel Mecánico" - Ver todos los seguros del servidor
- Recibir notificaciones DM cuando se solicitan seguros

### 👑 Administradores
**Comandos exclusivos:**
- `/mechanic_admin_register @usuario` - Registrar mecánico
- `/mechanic_admin_remove @usuario` - Eliminar mecánico  
- `/mechanic_admin_list` - Listar todos los mecánicos
- `/mechanic_admin_config_pvp 25` - Configurar recargo PVP (0-100%)

## 🔔 Sistema de Notificaciones

### Mecánicos
- **Por defecto**: Reciben notificaciones DM de nuevos seguros
- **Configuración**: `/mechanic_notifications true/false` (solo mecánicos)
- **Contenido**: Información completa del cliente, vehículo, ubicación y método de pago

### Clientes  
- Confirmación inmediata al solicitar seguro
- Información del seguro creado
- Estado del pago (Discord o InGame)

## 💰 Métodos de Pago

### Discord
- **Descuento inmediato** del balance del usuario
- **Seguro activo** inmediatamente
- **Transacción bancaria** registrada automáticamente

### InGame
- **Seguro pendiente** hasta confirmación
- **Mecánico debe coordinar** el pago en el juego
- **Estado**: "Pendiente de pago"

## 🗺️ Zonas y Precios

### Configuración PVP
- **Comando**: `/mechanic_admin_config_pvp 25` (solo admin)
- **Efecto**: Aumenta precio base por el porcentaje especificado
- **Ejemplo**: Moto en PVP = $500 + 25% = $625

### Selección de Zona
- **PVE**: Precio normal de seguros
- **PVP**: Precio con recargo configurado

## 📊 Funcionalidades del Sistema

### Modal Interactivo
1. **ID Vehículo**: Campo de texto (mínimo 3 caracteres)
2. **Tipo de Vehículo**: Selector (Ranger, Laika, WW, Avion, Moto)
3. **Zona**: Selector PVE/PVP con indicador de precio
4. **Método de Pago**: Selector Discord/InGame
5. **Descripción**: Campo opcional para detalles adicionales

### Validaciones
- ✅ Usuario registrado en el sistema
- ✅ Nombre InGame configurado
- ✅ ID único por vehículo (no duplicados)
- ✅ Fondos suficientes (para pago Discord)
- ✅ Todas las selecciones completadas

### Base de Datos
- **vehicle_insurance**: Seguros de vehículos
- **registered_mechanics**: Mecánicos registrados
- **mechanic_preferences**: Configuración de notificaciones
- **insurance_history**: Historial de acciones
- **server_config**: Configuración del servidor (recargo PVP)

## 🚀 Comandos Disponibles

### Usuarios
```
/seguro_solicitar - Solicitar seguro para vehículo
/seguro_consultar - Ver seguros activos
```

### Mecánicos
```
/mechanic_notifications true/false - Configurar notificaciones DM
```

### Administradores
```
/mechanic_admin_register @usuario - Registrar mecánico
/mechanic_admin_remove @usuario - Eliminar mecánico
/mechanic_admin_list - Listar mecánicos
/mechanic_admin_config_pvp 25 - Configurar recargo PVP
```

## ⚙️ Configuración del Canal

1. Use `/mechanic_admin_setup #canal` para configurar el sistema
2. Se creará un panel interactivo con botones
3. Los usuarios pueden solicitar seguros directamente desde el panel
4. Los mecánicos pueden acceder al panel de administración

## 🔧 Resolución de Problemas

### Usuario no puede solicitar seguro
- ✅ Verificar registro en sistema
- ✅ Verificar nombre InGame configurado
- ✅ Verificar fondos suficientes (pago Discord)

### Mecánico no recibe notificaciones
- ✅ Verificar registro como mecánico
- ✅ Usar `/mechanic_notifications true`
- ✅ Verificar DMs abiertos

### Precios incorrectos en PVP
- ✅ Usar `/mechanic_admin_config_pvp X` para ajustar porcentaje
- ✅ Verificar que se seleccionó zona PVP correctamente

## 📈 Estadísticas y Logs

El sistema registra automáticamente:
- Seguros creados y su información
- Cambios en configuración de mecánicos
- Errores de notificaciones
- Transacciones bancarias (pago Discord)
- Historial de acciones por seguro

---
*Sistema desarrollado para servidores SCUM Discord - Versión con selectores interactivos*