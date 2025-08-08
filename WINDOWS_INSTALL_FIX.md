# 🔧 Solución Rápida: Error de aiohttp en Python 3.13

## ❌ **Problema Identificado**

El error que experimentaste es común en **Python 3.13** con **aiohttp 3.9.1**:

```
error: Microsoft Visual C++ 14.0 or greater is required
ERROR: Failed building wheel for aiohttp
```

## ✅ **Solución Implementada**

### **1. Requirements.txt Actualizado**
```txt
# ANTES (problemático)
discord.py==2.5.2
aiohttp==3.9.1
stripe==8.5.0

# DESPUÉS (compatible)
discord.py==2.4.0
python-dotenv==1.0.1
aiosqlite==0.19.0
psutil==5.9.8
python-dateutil==2.9.0
```

### **2. Instalador Corregido**
- ✅ **`install_windows_fixed.bat`** - Maneja errores de compilación
- ✅ **Instalación por pasos** con verificación
- ✅ **Versiones compatibles** precompiladas
- ✅ **Fallback automático** si hay errores

## 🚀 **Instrucciones de Uso**

### **Opción A: Instalador Corregido (RECOMENDADO)**
```batch
# 1. Ejecutar como administrador
install_windows_fixed.bat

# 2. Seguir las instrucciones
# 3. ¡Listo!
```

### **Opción B: Manual (si el instalador falla)**
```batch
# 1. Crear directorio
mkdir C:\ScumBunkerTimer
cd C:\ScumBunkerTimer

# 2. Copiar archivos del bot
copy "BunkerAdvice_V2.py" .
copy "database_v2.py" .
copy "premium_*.py" .
copy "subscription_manager.py" .

# 3. Crear requirements.txt corregido
echo discord.py==2.4.0 > requirements.txt
echo python-dotenv==1.0.1 >> requirements.txt
echo aiosqlite==0.19.0 >> requirements.txt
echo psutil==5.9.8 >> requirements.txt
echo python-dateutil==2.9.0 >> requirements.txt

# 4. Instalar dependencias (debería funcionar)
python -m pip install -r requirements.txt

# 5. Configurar token
echo DISCORD_TOKEN=tu_token_real_aqui > config\bot_config.txt

# 6. Probar
python BunkerAdvice_V2.py
```

## 🎯 **¿Por qué funciona ahora?**

### **Discord.py 2.4.0 vs 2.5.2:**
- ✅ **2.4.0**: Wheels precompilados para Python 3.13
- ❌ **2.5.2**: Requiere compilación de aiohttp

### **Sin aiohttp explícito:**
- ✅ Discord.py incluye versión compatible automáticamente
- ✅ No necesita compilación manual

### **Dependencias mínimas:**
- ✅ Solo lo esencial para el bot
- ✅ Todas con wheels precompilados

## 🔍 **Verificación de Funcionamiento**

### **En el instalador verás:**
```
✅ Python encontrado: Python 3.13.6
✅ Dependencias instaladas correctamente
✅ discord.py 2.4.0 OK
✅ aiosqlite OK
✅ psutil OK
✅ Configuración válida
```

### **En Discord:**
- Bot aparece **Online**
- Comando `/ba_help` funciona
- 13 comandos disponibles

## 🛠️ **Si Sigue Fallando**

### **Alternativa 1: Usar Python 3.11**
```batch
# Descargar Python 3.11.x desde python.org
# Es la versión más estable para discord.py
```

### **Alternativa 2: Instalar Build Tools**
```batch
# Solo si quieres usar discord.py 2.5.2
# Descargar: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### **Alternativa 3: Usar conda**
```batch
conda create -n scumbot python=3.11
conda activate scumbot
pip install discord.py==2.4.0 aiosqlite psutil
```

## 📞 **Soporte**

Si tienes problemas con el **instalador corregido**:

1. **Ejecutar como administrador** ✓
2. **Tener Python en PATH** ✓
3. **Conexión a internet** ✓
4. **Ejecutar desde carpeta del proyecto** ✓

**¡El instalador corregido debería funcionar al 100%!** 🚀
