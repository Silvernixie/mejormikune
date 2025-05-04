#!/usr/bin/env python3
"""
Script para limpiar archivos innecesarios antes del deploy
Este script elimina todos los archivos __pycache__, archivos duplicados
y otros archivos innecesarios antes de hacer el deploy a Easypanel.
"""

import os
import shutil
import sys

def eliminar_pycache():
    """Elimina todos los directorios __pycache__ y archivos .pyc"""
    contador = 0
    
    # Buscar y eliminar directorios __pycache__
    for raiz, dirs, _ in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(raiz, '__pycache__')
            shutil.rmtree(pycache_path)
            contador += 1
            print(f"Eliminado: {pycache_path}")
    
    # Buscar y eliminar archivos .pyc
    for raiz, _, archivos in os.walk('.'):
        for archivo in archivos:
            if archivo.endswith(('.pyc', '.pyo', '.pyd')):
                file_path = os.path.join(raiz, archivo)
                os.remove(file_path)
                contador += 1
                print(f"Eliminado: {file_path}")
    
    return contador

def eliminar_duplicados_cogs():
    """Elimina archivos duplicados en la carpeta cogs"""
    contador = 0
    archivos_a_eliminar = [
        'cookies.txt', 'debug_build.sh', 'Dockerfile', 'easypanel.yml',
        'install_dependencies.bat', 'install_dependencies.py', 'install_dependencies.sh',
        'main.py', 'mikune.log', 'README.md', 'requirements.txt'
    ]
    
    for archivo in archivos_a_eliminar:
        ruta = os.path.join('cogs', archivo)
        if os.path.exists(ruta):
            os.remove(ruta)
            contador += 1
            print(f"Eliminado: {ruta}")
    
    # Eliminar carpeta cogs/cogs si existe
    ruta_cogs_anidada = os.path.join('cogs', 'cogs')
    if os.path.exists(ruta_cogs_anidada) and os.path.isdir(ruta_cogs_anidada):
        shutil.rmtree(ruta_cogs_anidada)
        contador += 1
        print(f"Eliminado directorio: {ruta_cogs_anidada}")
    
    return contador

def eliminar_logs():
    """Elimina archivos de log"""
    contador = 0
    
    for raiz, _, archivos in os.walk('.'):
        for archivo in archivos:
            if archivo.endswith('.log'):
                file_path = os.path.join(raiz, archivo)
                os.remove(file_path)
                contador += 1
                print(f"Eliminado log: {file_path}")
    
    return contador

def main():
    """Función principal"""
    print("=== Limpieza de archivos antes del deploy ===")
    
    total = 0
    
    # Ejecutar las funciones de limpieza
    print("\nEliminando directorios __pycache__ y archivos .pyc...")
    total += eliminar_pycache()
    
    print("\nEliminando archivos duplicados en carpeta cogs...")
    total += eliminar_duplicados_cogs()
    
    print("\nEliminando archivos de log...")
    total += eliminar_logs()
    
    print(f"\n=== Limpieza completada. {total} archivos eliminados ===")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())