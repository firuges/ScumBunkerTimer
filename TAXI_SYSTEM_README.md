# 🚖 Sistema Modular de Taxi + Banco + Welcome Pack

## ✨ **Características Principales**

### 🎁 **Welcome Pack**
- ✅ Registro automático al unirse al servidor
- ✅ Bono inicial de $5,000
- ✅ Cuenta bancaria automática
- ✅ Vouchers de taxi gratuitos
- ✅ Trial premium de 7 días

### 🏦 **Sistema Bancario**
- ✅ Transferencias entre jugadores
- ✅ Historial completo de transacciones
- ✅ Cuentas seguras con números únicos
- ✅ Integración total con el sistema de taxi

### 🚖 **Sistema de Taxi**
- ✅ **Restricciones de zona PVP/PVE**
- ✅ Tarifas dinámicas por tipo de vehículo
- ✅ Sistema de calificaciones
- ✅ Comisiones automáticas para conductores
- ✅ Respeta las zonas del mapa de SCUM

## 🗺️ **Restricciones de Zona (Basado en SCUM Map)**

### 🛡️ **Zonas Seguras** (Servicio Completo)
- 🏙️ Ciudad Central
- 🚢 Puertos Norte/Sur
- 🏠 Áreas Residenciales

### ⚔️ **Zonas de Combate** (Solo Recogida)
- 🏰 Bunker D1 (-2800, -2800)
- 🏰 Bunker C4 (-1000, 2000)
- 🏰 Bunker A1 (2800, -2800)
- 🏰 Bunker A3 (2800, 2800)

### 🚫 **Zonas Restringidas** (Sin Servicio)
- 🪖 Base Militar Central (0, 0) - Radio 2km

### 💼 **Zonas Especiales**
- ✈️ Aeropuerto (-1500, -1500) - Servicio prioritario
- 🏭 Zonas Industriales - Servicio disponible

## 🚀 **Instalación Rápida**

### 1️⃣ **Configuración Inicial**
```bash
# El sistema se integra automáticamente al iniciar el bot
# No requiere instalación adicional
```

### 2️⃣ **Configurar Canales** (Como Administrador)
```
/taxi_admin setup_all
  welcome_channel: #🎉┃welcome-center
  bank_channel: #🏦┃bank-service  
  taxi_channel: #🚖┃taxi-service
```

### 3️⃣ **Verificar Estado**
```
/taxi_admin stats
```

## ⚙️ **Comandos de Administración**

### 📊 **Estadísticas y Monitoreo**
```
/taxi_admin stats          - Estadísticas completas del sistema
/taxi_admin toggle         - Activar/desactivar componentes
/taxi_admin config         - Modificar configuración
```

### 🔧 **Configuración del Sistema**
```
/taxi_config              - Panel de configuración (botones)
```

### 👤 **Gestión de Usuarios**
```
/taxi_admin reset_user @usuario    - Resetear datos de usuario
```

## 💰 **Configuración Económica Predeterminada**

```yaml
Welcome Bonus: $5,000
Tarifa Base: $15.00
Por Kilómetro: $3.50
Comisión Conductor: 75%
Comisión Plataforma: 25%
```

## 🎯 **Flujo de Usuario**

### 🆕 **Nuevo Usuario**
1. Se une al servidor → Registro automático
2. Ve canal `#🎉┃welcome-center` → Reclama Welcome Pack
3. Recibe $5,000 + cuenta bancaria + vouchers
4. Puede usar `#🏦┃bank-service` y `#🚖┃taxi-service`

### 🚖 **Solicitar Taxi**
1. Va a `#🚖┃taxi-service`
2. Clic en "🚖 Solicitar Taxi"
3. Rellena coordenadas y destino
4. Sistema verifica zonas automáticamente
5. Conductores cercanos son notificados

### 👨‍✈️ **Ser Conductor**
1. Va a `#🚖┃taxi-service`
2. Clic en "👨‍✈️ Ser Conductor"
3. Selecciona tipo de vehículo
4. Recibe licencia automáticamente
5. Puede ponerse online/offline

### 💸 **Transferir Dinero**
1. Va a `#🏦┃bank-service`
2. Clic en "💸 Transferir"
3. Ingresa número de cuenta y monto
4. Confirmación automática

## 🔐 **Características de Seguridad**

- ✅ Validación de zonas en tiempo real
- ✅ Verificación de saldos antes de transacciones
- ✅ Historial completo de todas las operaciones
- ✅ Protección contra spam de solicitudes
- ✅ Sistema de ratings para conductores

## 🎮 **Compatible con**

- ✅ Servidores PVE
- ✅ Servidores PVP
- ✅ Servidores mixtos PVE/PVP
- ✅ Múltiples guilds de Discord
- ✅ Sistema de suscripciones existente

## 📈 **Sistema Modular**

El sistema está diseñado para ser **completamente modular**:

- 🔄 **Switch Master** - Activar/desactivar todo el sistema
- 🚖 **Switch Taxi** - Solo el servicio de taxi
- 🏦 **Switch Banco** - Solo el sistema bancario  
- 🎁 **Switch Welcome** - Solo el welcome pack

## 🔧 **Mantenimiento**

### 📊 **Monitoreo Diario**
- Revisar `/taxi_admin stats` para estadísticas
- Verificar que los canales funcionan correctamente
- Monitorear quejas de usuarios

### 🧹 **Limpieza Periódica**
- Usar `clean_taxi_users.py` para limpiar datos antiguos
- Resetear usuarios inactivos
- Mantener base de datos optimizada

## ⚠️ **Notas Importantes**

1. **Integración No Invasiva**: El sistema no modifica el código existente del bot de bunkers
2. **Base de Datos Separada**: Usa `taxi_system.db` independiente
3. **Configuración Persistente**: Toda la configuración se guarda en base de datos
4. **Escalabilidad**: Diseñado para manejar miles de usuarios
5. **Compatibilidad**: Funciona con el sistema de suscripciones existente

## 🚀 **Próximas Características**

- 🔄 Sistema de rutas predefinidas
- 📱 Integración con webhook de SCUM
- 🎯 Misiones diarias para conductores
- 🏆 Sistema de logros y recompensas
- 📊 Dashboard web para administradores

---

## 💡 **Soporte**

Para soporte técnico o consultas:
1. Revisa los logs en `logs/` 
2. Usa `/taxi_admin stats` para diagnóstico
3. Verifica que todos los toggles están activados
4. Contacta al desarrollador si persisten problemas
