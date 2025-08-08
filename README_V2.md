# SCUM Bunker Bot V2 - Multi-Server Support

Bot de Discord para gestionar timers de bunkers abandonados en SCUM con soporte para múltiples servidores.

## 🆕 Novedades Versión 2

### Soporte Multi-Servidor
- Gestiona bunkers de múltiples servidores SCUM simultáneamente
- Cada servidor tiene su propio conjunto de bunkers independiente
- Sistema de autocompletado para selección de servidores

### Nuevos Comandos de Gestión
- **Agregar servidores**: `/ba_add_server`
- **Eliminar servidores**: `/ba_remove_server`
- **Listar servidores**: `/ba_list_servers`

### Comandos Mejorados
- Todos los comandos de bunkers ahora incluyen parámetro opcional de servidor
- Autocompletado inteligente para sectores y servidores
- Interfaz mejorada con mejor información visual

## 📋 Comandos Disponibles

### Gestión de Servidores
```
/ba_add_server name: [nombre] description: [descripción]
/ba_remove_server server: [servidor]
/ba_list_servers
```

### Gestión de Bunkers
```
/ba_register_bunker sector: [D1/C4/A1/A3] hours: [horas] minutes: [minutos] server: [servidor]
/ba_check_bunker sector: [D1/C4/A1/A3] server: [servidor]
/ba_status_all server: [servidor]
```

## 🔄 Estados de Bunkers

1. **🔒 CERRADO** - Bunker cerrado, esperando apertura
2. **🟢 ACTIVO** - Bunker abierto (ventana de 24 horas)
3. **🔴 EXPIRADO** - Bunker cerrado permanentemente

## 🚀 Inicio Rápido

### 1. Configuración Automática
El bot usa el archivo `.env` para la configuración:
```bash
# Ya está configurado con tu token
python BunkerAdvice_V2.py
```

### 2. Inicio con Archivo Batch
```bash
# Doble clic en el archivo
start.bat
```

### 3. Inicio Manual
```bash
python BunkerAdvice_V2.py
```

## 📁 Estructura del Proyecto

### Archivos Principales
```
📄 BunkerAdvice_V2.py      # Bot principal V2
📄 database_v2.py          # Base de datos mejorada  
📄 .env                    # Configuración (token)
📄 bunkers_v2.db           # Base de datos SQLite
📄 start.bat               # Inicio rápido
📄 requirements.txt        # Dependencias Python
```

### Archivos de Soporte
```
📄 migrate_to_v2.py        # Script de migración desde V1
📄 test_v2.py              # Pruebas de funcionalidad
📄 status_check.py         # Verificación del sistema
📄 run_v2.bat              # Launcher con opciones
```

### Documentación
```
📄 README_V2.md            # Esta documentación
📄 COMANDOS_GUIA.md        # Guía completa de comandos
📄 IMPLEMENTACION_COMPLETADA.md  # Resumen técnico
```

### Archivos Legacy
```
📁 legacy/                 # Archivos de versiones anteriores
💾 bunkers_backup_*.db     # Backups automáticos
```

## 🔧 Configuración

### Variables de Entorno
```bash
DISCORD_TOKEN=tu_token_aqui
```

### Dependencias
```bash
pip install discord.py aiosqlite
```

## 📖 Uso Básico

### 1. Agregar un Servidor
```
/ba_add_server name: "Mi-Servidor" description: "Servidor principal PVP"
```

### 2. Registrar Bunker
```
/ba_register_bunker sector: D1 hours: 5 minutes: 30 server: "Mi-Servidor"
```

### 3. Consultar Estado
```
/ba_check_bunker sector: D1 server: "Mi-Servidor"
```

### 4. Ver Todos los Bunkers
```
/ba_status_all server: "Mi-Servidor"
```

## 🔍 Características Técnicas

### Base de Datos
- **SQLite** con soporte async (aiosqlite)
- **Tablas**: servers, bunkers, notifications
- **Migración automática** desde V1
- **Backup automático** de datos antiguos

### Discord Integration
- **Slash Commands** con autocompletado
- **Embeds** con información visual mejorada
- **Defer mechanism** para prevenir timeouts
- **Timestamps** dinámicos de Discord

### Sistema de Notificaciones
- Notificaciones programadas automáticas
- Alertas antes de apertura y cierre
- Sistema de cola persistente

## 🛠️ Migración de Datos

El script `migrate_to_v2.py` maneja automáticamente:

1. **Detección** de base de datos V1 existente
2. **Creación** de nueva estructura V2
3. **Migración** de datos a servidor "Default"
4. **Backup** de base de datos original
5. **Verificación** de integridad

## ⚡ Mejoras de Rendimiento

- **Conexiones async** para mejor responsividad
- **Autocompletado optimizado** con límites de resultados
- **Indexación mejorada** en base de datos
- **Manejo de errores robusto**

## 🔒 Seguridad

- **Validación** de parámetros de entrada
- **Protección** del servidor "Default"
- **Logging** completo de operaciones
- **Manejo seguro** de tokens

## 📊 Monitoring

- **Logs detallados** en `bot.log`
- **Timestamps** de todas las operaciones
- **Estados de salud** del bot
- **Métricas** de uso de comandos

## 🐛 Troubleshooting

### Problemas Comunes

1. **Bot no responde**
   - Verificar token en variables de entorno
   - Revisar logs en `bot.log`

2. **Comandos no aparecen**
   - Verificar permisos del bot
   - Forzar sincronización con `/ba_list_servers`

3. **Error de migración**
   - Verificar permisos de archivos
   - Revisar logs de migración

### Logs Importantes
```bash
# Ver logs en tiempo real
tail -f bot.log

# Buscar errores
grep ERROR bot.log
```

## 🔄 Roadmap

### Próximas Funciones
- [ ] Panel web de administración
- [ ] Importar/exportar configuraciones de servidor
- [ ] Estadísticas detalladas por servidor
- [ ] Notificaciones personalizables por servidor
- [ ] API REST para integración externa

### Optimizaciones Planeadas
- [ ] Cache de consultas frecuentes
- [ ] Compresión de base de datos
- [ ] Sharding para servidores grandes
- [ ] Métricas de rendimiento

## 📞 Soporte

Para reportar bugs o solicitar funciones:
1. Revisar logs en `bot.log`
2. Ejecutar `python test_v2.py` para diagnóstico
3. Incluir información del error en el reporte

## 📝 Changelog

### V2.0.0
- ✅ Soporte multi-servidor
- ✅ Nuevos comandos de gestión
- ✅ Migración automática desde V1
- ✅ Autocompletado mejorado
- ✅ Base de datos reestructurada

### V1.0.0
- ✅ Funcionalidad básica de bunkers
- ✅ Sistema de notificaciones
- ✅ Comandos slash básicos
