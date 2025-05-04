#!/usr/bin/env python3
"""
Script de preparación para deploy a Easypanel
Este script elimina todos los archivos relacionados con Nixpacks 
y prepara el proyecto para un deploy limpio usando Dockerfile.
"""

import os
import shutil
import sys

def limpiar_nixpacks():
    """Elimina todos los archivos y carpetas relacionadas con Nixpacks"""
    elementos_borrados = 0
    
    # Borrar carpeta .nixpacks si existe
    if os.path.exists('.nixpacks') and os.path.isdir('.nixpacks'):
        shutil.rmtree('.nixpacks')
        elementos_borrados += 1
        print("✓ Eliminada carpeta .nixpacks")
    
    # Borrar archivos relacionados con Nixpacks
    archivos_nixpacks = [
        'nixpacks.toml',
        '.nixpacksignore'
    ]
    
    for archivo in archivos_nixpacks:
        if os.path.exists(archivo):
            os.remove(archivo)
            elementos_borrados += 1
            print(f"✓ Eliminado archivo: {archivo}")
    
    # Buscar recursivamente cualquier carpeta .nixpacks en subcarpetas
    for raiz, dirs, _ in os.walk('.'):
        if '.nixpacks' in dirs:
            ruta_nixpacks = os.path.join(raiz, '.nixpacks')
            shutil.rmtree(ruta_nixpacks)
            elementos_borrados += 1
            print(f"✓ Eliminada carpeta: {ruta_nixpacks}")
    
    return elementos_borrados

def limpiar_cache_y_temp():
    """Elimina archivos de caché y temporales"""
    elementos_borrados = 0
    
    # Eliminar directorio __pycache__
    for raiz, dirs, _ in os.walk('.'):
        if '__pycache__' in dirs:
            ruta_pycache = os.path.join(raiz, '__pycache__')
            shutil.rmtree(ruta_pycache)
            elementos_borrados += 1
            print(f"✓ Eliminada carpeta: {ruta_pycache}")
    
    # Eliminar archivos .pyc, .pyo
    for raiz, _, archivos in os.walk('.'):
        for archivo in archivos:
            if archivo.endswith(('.pyc', '.pyo', '.pyd')):
                ruta_archivo = os.path.join(raiz, archivo)
                os.remove(ruta_archivo)
                elementos_borrados += 1
                print(f"✓ Eliminado archivo: {ruta_archivo}")
    
    # Eliminar archivos de log
    for raiz, _, archivos in os.walk('.'):
        for archivo in archivos:
            if archivo.endswith('.log'):
                ruta_archivo = os.path.join(raiz, archivo)
                os.remove(ruta_archivo)
                elementos_borrados += 1
                print(f"✓ Eliminado archivo de log: {ruta_archivo}")
    
    return elementos_borrados

def crear_dockerignore():
    """Crea un archivo .dockerignore optimizado"""
    contenido = """# Directorios y archivos que no necesitamos en el contenedor
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Archivos de log
*.log
logs/

# Archivos de entorno local que no deberían ir al contenedor
.env
.env.local
.env.development

# Archivos de control de versiones y configuración
.git
.github
.gitignore
.vscode
.idea

# Scripts de mantenimiento que no necesitamos en producción
*.sh
*.bat
clean_for_deploy.py
remove_nixpacks.py
prepare_for_easypanel.py
install_dependencies.py

# Archivos específicos de Nix/Nixpacks
.nixpacks/
nixpacks.toml
"""
    
    try:
        with open('.dockerignore', 'w') as f:
            f.write(contenido)
        print("✓ Archivo .dockerignore creado correctamente")
        return True
    except Exception as e:
        print(f"✗ Error al crear .dockerignore: {e}")
        return False

def main():
    """Función principal"""
    print("=== PREPARACIÓN PARA DEPLOY A EASYPANEL ===")
    
    # Limpieza de Nixpacks
    print("\n[1/3] Eliminando archivos de Nixpacks...")
    total_nixpacks = limpiar_nixpacks()
    
    # Limpieza de caché y temporales
    print("\n[2/3] Eliminando archivos de caché y temporales...")
    total_cache = limpiar_cache_y_temp()
    
    # Crear .dockerignore
    print("\n[3/3] Creando archivo .dockerignore optimizado...")
    crear_dockerignore()
    
    # Resumen
    print(f"\n=== LIMPIEZA COMPLETADA ===")
    print(f"Se eliminaron {total_nixpacks} elementos relacionados con Nixpacks")
    print(f"Se eliminaron {total_cache} archivos de caché y temporales")
    print("\nAhora el proyecto está listo para ser desplegado en Easypanel usando Dockerfile.")
    print("Instrucciones de despliegue:")
    print("1. Sube tu código limpio a un repositorio Git")
    print("2. En Easypanel, crea una nueva aplicación usando ese repositorio")
    print("3. Asegúrate de que Easypanel use el Dockerfile que hemos configurado")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())