# Legacy Database Backups

Este directorio contiene bases de datos legacy que ya no se utilizan activamente:

## Archivos movidos (2025-08-22):

### scum_bank.db
- **Estado**: OBSOLETA - Datos migrados a scum_main.db  
- **Propósito original**: Sistema bancario independiente
- **Razón del backup**: Ya consolidada en el sistema unificado

### test_bunkers_missing.db
- **Estado**: OBSOLETA - Solo para testing
- **Propósito original**: Tests de bunkers
- **Razón del backup**: Base de pruebas no necesaria en producción

## ⚠️ Importante:
- **NO REMOVER** taxi_users de scum_main.db - Es fundamental para el sistema de taxis
- **MANTENER** taxi_system.db - Base secundaria del sistema de taxis
- **bunkers_v2.db** - BunkerAdvice_V2.py actualizado para usar scum_main.db (puede moverse cuando no esté en uso)

## Migración completada:
✅ Sistema bancario unificado en scum_main.db  
✅ Bases legacy organizadas como backups  
✅ Estructura optimizada para evitar confusiones futuras