# 🔐 Permisos Necesarios para el Sistema de Tickets

## ⚠️ **Permisos Críticos del Bot**

Para que el sistema de tickets funcione correctamente, el bot **DEBE** tener estos permisos en el servidor:

### 📋 **Permisos Requeridos:**

1. **Manage Channels** (Administrar canales)
   - Para crear canales de tickets
   - Para crear categorías de tickets
   - Para eliminar canales al cerrar tickets

2. **Manage Permissions** (Administrar permisos)  
   - Para configurar permisos privados en canales de tickets
   - Para que solo el usuario y admins puedan ver su ticket

3. **Send Messages** (Enviar mensajes)
   - Para enviar el panel de tickets
   - Para enviar mensajes en canales de tickets

4. **View Channel** (Ver canal)
   - Para acceder a los canales donde está configurado

5. **Read Message History** (Leer historial)
   - Para funciones básicas del bot

6. **Embed Links** (Insertar enlaces)
   - Para mostrar embeds informativos

## 🚨 **Error 403 - Missing Permissions**

Si ves este error:
```
403 Forbidden (error code: 50013): Missing Permissions
```

**Soluciones:**

### ✅ **Opción 1: Permisos de Administrador (Recomendado)**
Dar al bot **permisos de administrador** en el servidor.

### ✅ **Opción 2: Permisos Específicos**  
Asegurar que el bot tenga estos permisos específicos:
- ☑️ Manage Channels
- ☑️ Manage Permissions  
- ☑️ Send Messages
- ☑️ View Channel
- ☑️ Read Message History
- ☑️ Embed Links

### ✅ **Opción 3: Verificar Jerarquía de Roles**
- El rol del bot debe estar **por encima** de los roles que quiere gestionar
- Si hay roles de moderador, el bot debe estar por encima

## 🛠️ **Cómo Configurar Permisos**

### **En Discord:**
1. Ve a **Configuración del servidor** → **Roles**
2. Encuentra el rol del bot (normalmente tiene el mismo nombre)
3. Activa los permisos necesarios:
   ```
   ☑️ Administrar canales
   ☑️ Administrar permisos  
   ☑️ Enviar mensajes
   ☑️ Ver canal
   ☑️ Leer el historial de mensajes
   ☑️ Insertar enlaces
   ```

### **Verificación Rápida:**
Ejecuta `/ticket_setup` en un canal de prueba:
- ✅ Si funciona: Permisos OK
- ❌ Si falla: Revisa permisos

## 🎯 **Categorías de Tickets**

El bot creará automáticamente:
- **Categoría:** "🎫 Tickets"
- **Canales:** ticket-0001, ticket-0002, etc.
- **Permisos:** Solo usuario + admins pueden ver cada ticket

## 📞 **Soporte**

Si los permisos están configurados correctamente y sigue fallando:
1. Reinicia Discord
2. Remueve y vuelve a invitar el bot
3. Verifica que no haya conflictos con otros bots
4. Contacta soporte técnico

---

**💡 Tip:** La forma más fácil es dar **permisos de administrador** al bot temporalmente, configurar todo, y luego ajustar permisos específicos si es necesario.