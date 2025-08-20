#!/usr/bin/env python3
"""
Validación del sistema de rate limiting completo
"""

import os
import re
from typing import List, Dict

def validate_rate_limiting_implementation() -> Dict[str, List[str]]:
    """Validar que todos los comandos con @rate_limit tienen implementación manual"""
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Excluir build directories
        if 'build' in root:
            continue
        for file in files:
            if file.endswith('.py') and not file.startswith('validate_'):
                python_files.append(os.path.join(root, file))
    
    results = {
        'completed': [],
        'missing': [],
        'errors': []
    }
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar decoradores @rate_limit
            rate_limit_matches = re.findall(r'@rate_limit\("([^"]+)"\)', content)
            
            if rate_limit_matches:
                # Verificar si tiene implementación manual
                has_manual_implementation = 'rate_limiter.check_and_record' in content
                
                if has_manual_implementation:
                    results['completed'].append(f"{file_path}: {', '.join(rate_limit_matches)}")
                else:
                    results['missing'].append(f"{file_path}: {', '.join(rate_limit_matches)}")
                    
        except Exception as e:
            results['errors'].append(f"{file_path}: Error - {str(e)}")
    
    return results

def main():
    print("=== VALIDACIÓN DEL SISTEMA DE RATE LIMITING ===\n")
    
    results = validate_rate_limiting_implementation()
    
    print(f"[OK] ARCHIVOS CON RATE LIMITING COMPLETO ({len(results['completed'])}):")
    for item in results['completed']:
        print(f"  * {item}")
    
    print(f"\n[ERROR] ARCHIVOS SIN IMPLEMENTACION MANUAL ({len(results['missing'])}):")
    for item in results['missing']:
        print(f"  * {item}")
    
    if results['errors']:
        print(f"\n[WARNING] ERRORES DURANTE LA VALIDACION ({len(results['errors'])}):")
        for item in results['errors']:
            print(f"  * {item}")
    
    # Resumen
    total_files = len(results['completed']) + len(results['missing'])
    if total_files > 0:
        completion_rate = (len(results['completed']) / total_files) * 100
        print(f"\n[SUMMARY] RESUMEN:")
        print(f"  Total de archivos con rate limiting: {total_files}")
        print(f"  Completados: {len(results['completed'])}")
        print(f"  Pendientes: {len(results['missing'])}")
        print(f"  Tasa de completitud: {completion_rate:.1f}%")
        
        if len(results['missing']) == 0:
            print("\n[SUCCESS] IMPLEMENTACION COMPLETA! Todos los comandos tienen rate limiting manual.")
        else:
            print(f"\n[WARNING] IMPLEMENTACION INCOMPLETA. Faltan {len(results['missing'])} archivos.")
    else:
        print("\n[INFO] No se encontraron archivos con decoradores @rate_limit.")

if __name__ == "__main__":
    main()