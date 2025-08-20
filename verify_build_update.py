#!/usr/bin/env python3
"""
Script para verificar que el build.bat incluye todos los componentes de rate limiting
"""

import os
from typing import List, Tuple

def check_file_exists(filename: str) -> bool:
    """Verificar si un archivo existe"""
    return os.path.exists(filename)

def check_build_bat_content(required_files: List[str]) -> Tuple[bool, List[str]]:
    """Verificar que build.bat incluye todos los archivos requeridos"""
    missing_from_build = []
    
    if not os.path.exists("build.bat"):
        return False, ["build.bat not found"]
    
    try:
        with open("build.bat", "r", encoding="utf-8", errors="ignore") as f:
            build_content = f.read()
    except:
        # Intentar con encoding diferente
        with open("build.bat", "r", encoding="latin-1") as f:
            build_content = f.read()
    
    for file in required_files:
        if file not in build_content:
            missing_from_build.append(file)
    
    return len(missing_from_build) == 0, missing_from_build

def main():
    """Función principal"""
    print("[VERIFY] Verificando actualización del build.bat...")
    print("="*60)
    
    # Archivos nuevos que deben estar incluidos
    new_files = [
        "rate_limiter.py",
        "rate_limit_admin.py", 
        "database_pool.py",
        "test_rate_limiting.py",
        "test_bot_integration.py"
    ]
    
    # Términos que deben aparecer en build.bat
    required_terms = [
        "RATE LIMITING",
        "rate_limiter.py",
        "rate_limit_admin.py",
        "database_pool.py",
        "Sistema de rate limiting",
        "10 subsistemas",
        "60+ comandos"
    ]
    
    # Verificar que los archivos existen
    print("[CHECK] Verificando existencia de archivos nuevos...")
    missing_files = []
    for file in new_files:
        if check_file_exists(file):
            print(f"  [OK] {file}")
        else:
            print(f"  [ERROR] {file} - NO ENCONTRADO")
            missing_files.append(file)
    
    # Verificar que build.bat los incluye
    print("\n[CHECK] Verificando inclusión en build.bat...")
    build_ok, missing_from_build = check_build_bat_content(new_files)
    
    if build_ok:
        print("  [OK] Todos los archivos incluidos en build.bat")
    else:
        print("  [ERROR] Archivos faltantes en build.bat:")
        for file in missing_from_build:
            print(f"    - {file}")
    
    # Verificar términos clave
    print("\n[CHECK] Verificando términos clave...")
    try:
        with open("build.bat", "r", encoding="utf-8", errors="ignore") as f:
            build_content = f.read()
    except:
        with open("build.bat", "r", encoding="latin-1") as f:
            build_content = f.read()
    
    missing_terms = []
    for term in required_terms:
        if term in build_content:
            print(f"  [OK] {term}")
        else:
            print(f"  [ERROR] {term} - NO ENCONTRADO")
            missing_terms.append(term)
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE VERIFICACIÓN")
    print("="*60)
    
    total_issues = len(missing_files) + len(missing_from_build) + len(missing_terms)
    
    if total_issues == 0:
        print("[SUCCESS] VERIFICACIÓN EXITOSA")
        print("El build.bat está completamente actualizado con:")
        print("  - Sistema de rate limiting")
        print("  - Pool de conexiones de base de datos") 
        print("  - Scripts de prueba")
        print("  - Documentación actualizada")
        print("  - Contadores actualizados (10 sistemas, 60+ comandos)")
    else:
        print("[ERROR] PROBLEMAS ENCONTRADOS:")
        if missing_files:
            print(f"  - {len(missing_files)} archivos faltantes")
        if missing_from_build:
            print(f"  - {len(missing_from_build)} archivos no incluidos en build.bat")
        if missing_terms:
            print(f"  - {len(missing_terms)} términos faltantes en build.bat")
    
    print("\n[INFO] Para usar:")
    print("1. Ejecutar: build.bat (generar build completo)")
    print("2. En el build generado: INSTALL.bat")
    print("3. Configurar token en config.py")
    print("4. Ejecutar: start_bot.bat")
    
    return total_issues == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)