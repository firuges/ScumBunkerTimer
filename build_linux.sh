#!/bin/bash

# SCUM Bunker Timer V2 - Build Generator (Linux/macOS)
# Genera una carpeta portable para despliegue

echo "========================================"
echo "  SCUM Bunker Timer V2 - Build Generator"
echo "========================================"
echo ""
echo "  Genera una carpeta portable para despliegue"
echo "  Lista para llevar a cualquier servidor"
echo ""
echo "========================================"

# Cambiar al directorio del script
cd "$(dirname "$0")"

# Verificar que los archivos fuente existen
echo ""
echo "📄 Verificando archivos fuente..."

if [ ! -f "BunkerAdvice_V2.py" ]; then
    echo "❌ ERROR: No se encuentra BunkerAdvice_V2.py"
    echo ""
    echo "   Asegúrate de ejecutar este script desde la carpeta"
    echo "   que contiene todos los archivos del bot."
    echo ""
    exit 1
fi

echo "✅ Archivos fuente verificados"

# Definir directorio de build
BUILD_DIR="build"
BUILD_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BUILD_FULL_DIR="$BUILD_DIR/ScumBunkerTimer_$BUILD_TIMESTAMP"

# Crear directorio de build
echo ""
echo "📁 Creando directorio de build..."

if [ -d "$BUILD_DIR" ]; then
    echo "   Limpiando build anterior..."
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$BUILD_FULL_DIR"
mkdir -p "$BUILD_FULL_DIR/logs"
mkdir -p "$BUILD_FULL_DIR/backup"
mkdir -p "$BUILD_FULL_DIR/config"
mkdir -p "$BUILD_FULL_DIR/installers"

echo "✅ Directorio creado: $BUILD_FULL_DIR"

# Copiar archivos principales del bot
echo ""
echo "📄 Copiando archivos del bot..."

cp "BunkerAdvice_V2.py" "$BUILD_FULL_DIR/"
cp "database_v2.py" "$BUILD_FULL_DIR/"
cp premium_*.py "$BUILD_FULL_DIR/" 2>/dev/null || true
cp "subscription_manager.py" "$BUILD_FULL_DIR/"
cp "bot_starter.py" "$BUILD_FULL_DIR/"
cp "requirements.txt" "$BUILD_FULL_DIR/"

echo "✅ Archivos principales copiados"

# Leer token del .env
echo ""
echo "⚙️ Leyendo configuración del .env..."

DISCORD_TOKEN_VALUE=""
if [ -f ".env" ]; then
    DISCORD_TOKEN_VALUE=$(grep "^DISCORD_TOKEN=" .env | cut -d'=' -f2)
fi

# Crear config.py con el token
echo ""
echo "⚙️ Creando configuración..."

if [ -n "$DISCORD_TOKEN_VALUE" ]; then
    cat > "$BUILD_FULL_DIR/config.py" << EOF
# Configuración del bot Discord
DISCORD_TOKEN = '$DISCORD_TOKEN_VALUE'
PREFIX = '/'
DEBUG = True

# Base de datos
DATABASE_NAME = 'bunkers_v2.db'

# Configuración de logs
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/bot.log'
EOF
    echo "✅ Token configurado automáticamente desde .env"
else
    cat > "$BUILD_FULL_DIR/config.py" << EOF
# Configuración del bot Discord
DISCORD_TOKEN = 'TU_TOKEN_AQUI'
PREFIX = '/'
DEBUG = True

# Base de datos
DATABASE_NAME = 'bunkers_v2.db'

# Configuración de logs
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/bot.log'
EOF
    echo "⚠️ No se pudo leer el token del .env, usando placeholder"
fi

echo "✅ config.py creado"

# Mostrar resumen del build
echo ""
echo "==============================================="
echo "  🎉 BUILD GENERADO EXITOSAMENTE"
echo "==============================================="
echo ""
echo "📁 Ubicación: $BUILD_FULL_DIR"
echo "📊 Timestamp: $BUILD_TIMESTAMP"
echo ""

if [ -n "$DISCORD_TOKEN_VALUE" ]; then
    echo "🔑 Token: ✅ Configurado automáticamente"
else
    echo "🔑 Token: ⚠️ Requiere configuración manual"
fi

echo ""
echo "==============================================="
echo "  📦 LISTO PARA DESPLIEGUE"
echo "==============================================="
echo ""
