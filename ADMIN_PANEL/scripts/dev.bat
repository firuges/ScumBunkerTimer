@echo off
REM 🚀 SCUM Admin Panel - Development Setup Script (Windows)

echo 🤖 SCUM Bot Admin Panel - Development Mode
echo ==========================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Build and start services
echo 🐳 Building Docker containers...
docker-compose -f docker-compose.dev.yml build

echo 🚀 Starting development servers...
docker-compose -f docker-compose.dev.yml up -d

echo.
echo ✅ Services started successfully!
echo.
echo 🌐 Access URLs:
echo    Frontend (React): http://localhost:3002
echo    Backend (API):    http://localhost:8000
echo    API Docs:         http://localhost:8000/docs
echo    Health Check:     http://localhost:8000/health
echo.
echo 📊 Check status: docker-compose -f docker-compose.dev.yml ps
echo 📋 View logs:    docker-compose -f docker-compose.dev.yml logs -f
echo 🛑 Stop:         docker-compose -f docker-compose.dev.yml down
echo.
echo 🔥 Happy coding! 🚀
pause