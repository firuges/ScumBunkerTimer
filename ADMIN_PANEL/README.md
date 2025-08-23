# 🤖 SCUM Bot - Admin Panel

Panel administrativo web para gestionar el bot de Discord SCUM con arquitectura híbrida Python FastAPI + React TypeScript.

## 🚀 Quick Start

### Desarrollo Local (Recomendado)
```bash
# Backend (Puerto 8000)
cd backend
python simple_main.py

# Frontend (Puerto 3002)  
cd frontend
npm start
```

### Docker Development
```bash
# Windows
scripts\dev.bat

# Linux/Mac
chmod +x scripts/dev.sh
./scripts/dev.sh
```

## 🌐 URLs

- **🎨 Frontend:** http://localhost:3002
- **🔥 API Backend:** http://localhost:8000  
- **📚 API Docs:** http://localhost:8000/docs
- **💚 Health:** http://localhost:8000/health

## ✅ Módulos Implementados

### 🏆 Fame Points ✅ COMPLETO
- ✅ CRUD completo (Create/Read/Update/Delete)
- ✅ Modal para crear/editar recompensas
- ✅ Estados activo/inactivo
- ✅ Validación de formularios
- ✅ API backend funcional

## 🔄 Próximos Módulos
- 🚕 Sistema Taxi
- 🏦 Banking Config  
- 🔧 Mechanics Services
- 📊 Analytics Dashboard

## 🏗️ Arquitectura

```
Backend (Python FastAPI) :8000 ↔ Frontend (React TS) :3002
                ↕
        scum_main.db (Shared)
                ↕  
        Discord Bot (Python)
```

## 📁 Estructura
```
ADMIN_PANEL/
├── backend/     # Python FastAPI
├── frontend/    # React TypeScript  
├── docker/      # Containerización
└── scripts/     # Utilidades
```

## 🎯 Estado Actual

**✅ MVP Funcional:** Fame Points CRUD completamente operativo  
**🔄 En desarrollo:** Docker setup, módulos adicionales  
**🎯 Próximo:** Sistema Taxi, Banking, Mechanics

---

**🚀 Desarrollado para optimizar la administración del bot SCUM**