#!/bin/bash
# Script de build para Render
echo "Instalando dependencias..."
pip install --upgrade pip
pip install discord.py==2.5.2
pip install python-dotenv==1.0.1
pip install aiosqlite==0.19.0
echo "Dependencias instaladas correctamente"
