# 🎯 AUTOCOMPLETADO Y COMANDOS - GUÍA VISUAL

## 📱 **Cómo Funciona el Autocompletado**

### **1. Comando Slash con Autocompletado**

Cuando el usuario empieza a escribir `/register_bunker`, Discord mostrará:

```
/register_bunker sector: [AUTOCOMPLETADO ACTIVADO]
```

Al escribir en el campo `sector`, aparecerán opciones:

```
┌─ Autocompletado Sector ─────────────────────┐
│ 🔹 D1 - Bunker Abandonado D1               │
│ 🔹 C4 - Bunker Abandonado C4               │
│ 🔹 A1 - Bunker Abandonado A1               │
│ 🔹 A3 - Bunker Abandonado A3               │
└─────────────────────────────────────────────┘
```

### **2. Filtrado Inteligente**

Si el usuario escribe "D":
```
┌─ Autocompletado Sector (filtrado) ─────────┐
│ 🔹 D1 - Bunker Abandonado D1               │
└─────────────────────────────────────────────┘
```

Si el usuario escribe "A":
```
┌─ Autocompletado Sector (filtrado) ─────────┐
│ 🔹 A1 - Bunker Abandonado A1               │
│ 🔹 A3 - Bunker Abandonado A3               │
└─────────────────────────────────────────────┘
```

## 🎮 **Lista Completa de Comandos**

### **Discord Slash Commands (Autocompletado)**

#### `/register_bunker`
**Descripción**: Registra el tiempo restante de un bunker
**Parámetros**:
- `sector`: [AUTOCOMPLETADO] D1, C4, A1, A3
- `hours`: Número (0-999)
- `minutes`: Número opcional (0-59)

**Ejemplo de uso**:
```
# Guía de Comandos - SCUM Bunker Bot V2

## 🆕 Versión 2.0 - Multi-Servidor

### Novedades
- ✅ Soporte para múltiples servidores SCUM
- ✅ Gestión independiente de bunkers por servidor
- ✅ Autocompletado mejorado para servidores y sectores
- ✅ Migración automática desde V1

## 📋 Comandos Disponibles

### 🖥️ Gestión de Servidores

#### `/ba_add_server`
Agregar un nuevo servidor para tracking de bunkers.

**Parámetros:**
- `name`: Nombre del servidor (único)
- `description`: Descripción opcional del servidor

**Ejemplo:**
```
/ba_add_server name:"Mi-Servidor-PVP" description:"Servidor principal de PVP"
```

#### `/ba_remove_server`
Eliminar un servidor y todos sus bunkers asociados.

**Parámetros:**
- `server`: Nombre del servidor - Con autocompletado

**Ejemplo:**
```
/ba_remove_server server:"Mi-Servidor-PVP"
```

**⚠️ Nota:** No se puede eliminar el servidor "Default"

#### `/ba_list_servers`
Listar todos los servidores registrados con su información.

**Ejemplo:**
```
/ba_list_servers
```

### 🏗️ Gestión de Bunkers (Mejorados)

#### `/ba_register_bunker`
Registra el tiempo de expiración de un bunker abandonado.

**Parámetros:**
- `sector`: Sector del bunker (D1, C4, A1, A3) - Con autocompletado
- `hours`: Horas hasta la expiración (0-72)
- `minutes`: Minutos adicionales (0-59) [Opcional]
- `server`: Servidor del bunker - Con autocompletado [Opcional, por defecto: "Default"]

**Ejemplos:**
```
/ba_register_bunker sector:D1 hours:5 minutes:30
/ba_register_bunker sector:C4 hours:2 server:"Mi-Servidor-EU"
```

#### `/ba_check_bunker`
Consulta el estado actual de un bunker específico.

**Parámetros:**
- `sector`: Sector del bunker (D1, C4, A1, A3) - Con autocompletado
- `server`: Servidor del bunker - Con autocompletado [Opcional, por defecto: "Default"]

**Ejemplos:**
```
/ba_check_bunker sector:D1
/ba_check_bunker sector:A3 server:"Mi-Servidor-US"
```

#### `/ba_status_all`
Muestra el estado de todos los bunkers de un servidor.

**Parámetros:**
- `server`: Servidor a consultar - Con autocompletado [Opcional, por defecto: "Default"]

**Ejemplos:**
```
/ba_status_all
/ba_status_all server:"Mi-Servidor-PVP"
```

## 📊 Estados de Bunkers

### 🔒 CERRADO
- El bunker está cerrado y no se puede acceder
- Muestra el tiempo restante hasta la apertura
- Color: Naranja

### 🟢 ACTIVO
- El bunker está abierto y accesible
- Muestra el tiempo restante antes del cierre permanente
- Ventana de 24 horas desde la apertura
- Color: Verde

### 🔴 EXPIRADO
- El bunker está cerrado permanentemente
- No se puede acceder hasta el próximo registro
- Color: Rojo

### ❓ SIN REGISTRO
- No hay información de tiempo registrada
- Color: Gris

## ⏰ Sistema de Tiempo

1. **Registro inicial**: Se establece el tiempo hasta la apertura
2. **Apertura**: Cuando el tiempo llega a 0, el bunker se abre
3. **Ventana activa**: 24 horas de acceso desde la apertura
4. **Cierre**: Después de 24 horas, el bunker se cierra permanentemente

## 🖥️ Gestión Multi-Servidor

### Concepto
Cada servidor tiene su propio conjunto independiente de bunkers:
- **Servidor Default**: Servidor por defecto (no se puede eliminar)
- **Servidores Personalizados**: Creados por los usuarios

### Flujo de Trabajo
1. **Crear servidor**: `/ba_add_server`
2. **Registrar bunkers**: `/ba_register_bunker` con parámetro `server`
3. **Consultar estado**: `/ba_check_bunker` o `/ba_status_all`
4. **Gestionar**: Modificar o eliminar servidores según necesidad

### Sectores por Servidor
Cada servidor incluye automáticamente los 4 sectores:
- **D1** - Bunker Abandonado D1
- **C4** - Bunker Abandonado C4  
- **A1** - Bunker Abandonado A1
- **A3** - Bunker Abandonado A3

## 🔧 Características Técnicas

### Autocompletado Inteligente
- **Sectores**: D1, C4, A1, A3 con filtrado por texto
- **Servidores**: Lista dinámica de servidores registrados

### Validaciones
- Parámetros de tiempo validados (0-72h, 0-59m)
- Sectores válidos únicamente
- Protección del servidor "Default"

### Persistencia
- Base de datos SQLite con soporte async
- Migración automática desde versión anterior
- Backup automático de datos existentes

### Logging
- Registro completo de operaciones
- Archivo `bot.log` con información detallada
- Timestamps de todas las acciones

## 🔄 Migración desde V1

### Automática
El sistema detecta automáticamente si existe una instalación V1 y migra:
- ✅ Bunkers existentes → Servidor "Default"
- ✅ Notificaciones programadas → Servidor "Default"  
- ✅ Backup automático de base de datos original
- ✅ Preservación de todos los datos

### Manual
Si necesitas migrar manualmente:
```bash
python migrate_to_v2.py
```

## 🛠️ Comandos de Administración

### Verificar Estado
```bash
python status_check.py
```

### Probar Funcionalidad
```bash
python test_v2.py
```

### Ejecutar Bot V2
```bash
python BunkerAdvice_V2.py
```

## 💡 Consejos de Uso

### Para Comunidades Pequeñas
- Usar solo el servidor "Default"
- No es necesario crear servidores adicionales

### Para Comunidades Multi-Servidor
- Crear un servidor por cada instancia de SCUM
- Nomenclatura clara: "EU-PVP", "US-PVE", etc.
- Asignar responsables por servidor

### Para Administradores
- Revisar logs regularmente: `bot.log`
- Hacer backup periódico de `bunkers_v2.db`
- Monitorear uso de comandos por servidor

## 🐛 Solución de Problemas

### Bot no responde
1. Verificar token en variables de entorno
2. Revisar logs en `bot.log`
3. Ejecutar `python status_check.py`

### Comandos no aparecen
1. Verificar permisos del bot en Discord
2. Esperar sincronización automática
3. Reiniciar bot si es necesario

### Error de migración
1. Verificar permisos de archivos
2. Revisar logs de migración
3. Contactar soporte técnico

## 📈 Próximas Funciones

- [ ] Notificaciones personalizables por servidor
- [ ] Estadísticas de uso por servidor
- [ ] Panel web de administración
- [ ] Exportar/importar configuraciones
- [ ] API REST para integración externa
```

#### `/check_bunker`
**Descripción**: Consulta el estado de uno o todos los bunkers
**Parámetros**:
- `sector`: [AUTOCOMPLETADO OPCIONAL] D1, C4, A1, A3

**Ejemplos de uso**:
```
/check_bunker sector:D1        # Ver bunker específico
/check_bunker                  # Ver todos los bunkers
```

### **Discord Text Commands (Compatibilidad)**

#### `!ba` - Comando versátil
```
!ba                    # Ver todos los bunkers
!ba D1                 # Ver bunker D1
!ba D1 160h:40m        # Registrar tiempo en D1
!ba D1 160h            # Registrar solo horas
!ba D1 160:40          # Formato alternativo
```

### **In-Game Commands (RCON)**

#### Consulta de Estado
```
!BAD1                  # Consultar Bunker D1
!BAC4                  # Consultar Bunker C4
!BAA1                  # Consultar Bunker A1
!BAA3                  # Consultar Bunker A3
```

#### Registro de Tiempo
```
!BAD1 160h:40m         # Registrar 160h 40m en D1
!BAC4 72h              # Registrar 72h en C4
!BAA1 24:30            # Registrar 24h 30m en A1 (formato alternativo)
!BAA3 168h:0m          # Registrar 168h en A3
```

## 🔄 **Flujo de Trabajo Típico**

### **Escenario 1: Registro desde Discord**
1. Usuario escribe `/register_bunker`
2. Aparece autocompletado en campo `sector`
3. Usuario selecciona "D1 - Bunker Abandonado D1"
4. Usuario ingresa horas: `160`
5. Usuario ingresa minutos: `40`
6. Bot confirma registro y programa notificaciones

### **Escenario 2: Consulta desde el Juego**
1. Jugador escribe en chat: `!BAD1`
2. Bot detecta comando via RCON
3. Bot responde al jugador: "Bunker D1: 159h 23m restantes."

### **Escenario 3: Notificación Automática**
1. Sistema detecta que bunker expira en 2 horas
2. Bot envía embed a canal Discord:
   ```
   🟡 Bunker Próximo a Expirar
   Bunker Abandonado D1 expirará en aproximadamente 2 horas
   Sector: D1
   ```

## 📊 **Ejemplos de Respuestas**

### **Estados Posibles**

#### ✅ **Bunker Activo**
```discord
🟢 Bunker Abandonado D1
Tiempo Restante: 159h 23m
Sector: D1
Registrado por: @Usuario#1234
Expira: Lunes, 10 Agosto 2025 15:30
```

#### 🔴 **Bunker Expirado**
```discord
🔴 Bunker Abandonado D1
Tiempo Restante: ¡EXPIRADO!
Sector: D1
Registrado por: @Usuario#1234
Expirado desde: 2h 15m
```

#### ⚪ **Sin Registro**
```discord
⚪ Bunker Abandonado D1
Tiempo Restante: Sin registro
Sector: D1
```

### **Vista de Todos los Bunkers**
```discord
📊 Estado de Todos los Bunkers

🟢 Bunker Abandonado D1     🔴 Bunker Abandonado C4
159h 23m                    ¡EXPIRADO!
Registrado por: Usuario1    Expirado desde: 3h 45m

⚪ Bunker Abandonado A1     🟢 Bunker Abandonado A3
Sin registro                24h 12m
                           Registrado por: Usuario2
```

## ⚙️ **Configuración del Autocompletado**

El autocompletado funciona automáticamente cuando:

1. **Discord detecta** que el comando tiene `@discord.app_commands.autocomplete`
2. **Usuario empieza a escribir** en el campo con autocompletado
3. **Función se ejecuta** filtrando opciones según texto ingresado
4. **Discord muestra** hasta 25 opciones ordenadas

### **Personalización Avanzada**

Puedes modificar la función `sector_autocomplete()` para:
- Mostrar estado actual de cada bunker
- Filtrar solo bunkers disponibles
- Agregar iconos según estado
- Ordenar por tiempo restante

## 🚀 **Ventajas del Sistema**

### **Para Usuarios de Discord**
- ✅ **Autocompletado intuitivo** - No necesitan memorizar sectores
- ✅ **Validación automática** - Imposible ingresar sectores inválidos
- ✅ **Información visual** - Embeds ricos con iconos y colores
- ✅ **Notificaciones proactivas** - Alertas automáticas

### **Para Jugadores In-Game**
- ✅ **Comandos rápidos** - Sin salir del juego
- ✅ **Respuesta inmediata** - Mensajes privados al instante
- ✅ **Sintaxis flexible** - Múltiples formatos aceptados
- ✅ **Ayuda automática** - Bot explica comandos si hay error

### **Para Administradores**
- ✅ **Logs completos** - Registro de todas las acciones
- ✅ **Base de datos persistente** - Datos no se pierden
- ✅ **Configuración modular** - Habilitar/deshabilitar funciones
- ✅ **Escalabilidad** - Fácil agregar más bunkers

---

**¡El bot está listo para usar con autocompletado completo y soporte para los 4 bunkers de SCUM!**
