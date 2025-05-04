#!/usr/bin/env python3
"""
Script de preparación para deploy a Easypanel con Nixpacks
Este script prepara el proyecto Mikune para ser desplegado en Easypanel,
ejecutando automáticamente todas las tareas de limpieza necesarias.
"""

import os
import sys
import subprocess
import importlib.util

def importar_script(ruta_script):
    """Importa un script Python como módulo"""
    nombre_modulo = os.path.basename(ruta_script).replace('.py', '')
    spec = importlib.util.spec_from_file_location(nombre_modulo, ruta_script)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo

def crear_dockerignore():
    """Crea un archivo .dockerignore optimizado para Easypanel"""
    contenido = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
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

# Logs y datos temporales
*.log
logs/
*.tmp
.env.local
.env.development

# Desarrollo
.git
.github
.gitignore
.vscode
.idea

# Archivos específicos que no necesitamos en producción
debug_build.sh
install_dependencies.bat
install_dependencies.py
install_dependencies.sh
clean_for_deploy.py
remove_nixpacks.py
prepare_for_easypanel.py
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
    """Función principal que orquesta todas las operaciones de preparación"""
    print("=== PREPARACIÓN PARA DEPLOY A EASYPANEL ===")
    
    # 1. Ejecutar script de limpieza general
    print("\n[1/3] Ejecutando limpieza de archivos...")
    try:
        clean_script = importar_script('clean_for_deploy.py')
        clean_script.main()
    except Exception as e:
        print(f"Error durante la limpieza: {e}")
    
    # 2. Asegurar la eliminación de Nixpacks antiguo
    print("\n[2/3] Eliminando configuraciones antiguas de Nixpacks...")
    try:
        nixpacks_script = importar_script('remove_nixpacks.py')
        nixpacks_script.main()
    except Exception as e:
        print(f"Error durante la eliminación de Nixpacks: {e}")
    
    # 3. Crear archivos optimizados para Easypanel
    print("\n[3/3] Optimizando configuración para Easypanel...")
    crear_dockerignore()
    
    print("\n=== PREPARACIÓN COMPLETADA ===")
    print("Tu proyecto está listo para ser desplegado en Easypanel usando Nixpacks.")
    print("Instrucciones de despliegue:")
    print("1. Sube tu código a un repositorio Git")
    print("2. En Easypanel, crea una nueva aplicación usando ese repositorio")
    print("3. Asegúrate de que Easypanel detecte automáticamente la configuración de Nixpacks")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())