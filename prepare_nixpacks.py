#!/usr/bin/env python3
"""
Script de limpieza para preparar el proyecto para Nixpacks en Easypanel
Este script elimina archivos de Nixpacks antiguos y prepara el proyecto para un deploy limpio
"""

import os
import shutil
import sys

def eliminar_directorio_nixpacks():
    """Elimina los directorios .nixpacks si existen"""
    if os.path.exists(".nixpacks"):
        try:
            shutil.rmtree(".nixpacks")
            print("✓ Directorio .nixpacks eliminado")
            return True
        except Exception as e:
            print(f"✗ Error al eliminar directorio .nixpacks: {e}")
            return False
    return False

def eliminar_dockerfile():
    """Elimina el Dockerfile ya que usaremos Nixpacks"""
    if os.path.exists("Dockerfile"):
        try:
            os.remove("Dockerfile")
            print("✓ Dockerfile eliminado (se usará Nixpacks en su lugar)")
            return True
        except Exception as e:
            print(f"✗ Error al eliminar Dockerfile: {e}")
            return False
    return False

def crear_dockerignore():
    """Crea un archivo .dockerignore optimizado para Nixpacks"""
    contenido = """# Archivos que no necesitamos en el contenedor
__pycache__/
*.py[cod]
*$py.class
*.so
.git
.github
.gitignore
.vscode
.idea
*.log
logs/
*.tmp
.env
clean_for_deploy.py
clean_for_easypanel.py
remove_nixpacks.py
prepare_for_easypanel.py
install_dependencies.bat
install_dependencies.py
install_dependencies.sh
"""
    
    try:
        with open(".dockerignore", "w") as f:
            f.write(contenido)
        print("✓ Archivo .dockerignore creado para Nixpacks")
        return True
    except Exception as e:
        print(f"✗ Error al crear .dockerignore: {e}")
        return False

def main():
    """Función principal"""
    print("==== PREPARACIÓN PARA DEPLOY CON NIXPACKS EN EASYPANEL ====")
    
    # Eliminar directorio .nixpacks
    print("\n[1/3] Eliminando directorios .nixpacks antiguos...")
    eliminar_directorio_nixpacks()
    
    # Eliminar Dockerfile (ya que usaremos Nixpacks)
    print("\n[2/3] Eliminando Dockerfile (usaremos Nixpacks)...")
    eliminar_dockerfile()
    
    # Crear .dockerignore
    print("\n[3/3] Creando .dockerignore optimizado...")
    crear_dockerignore()
    
    print("\n==== PREPARACIÓN COMPLETADA ====")
    print("El proyecto está listo para ser desplegado con Nixpacks en Easypanel.")
    print("Instrucciones:")
    print("1. Sube estos cambios a tu repositorio Git")
    print("2. En Easypanel, configura tu aplicación para usar Nixpacks")
    print("3. Asegúrate de que Easypanel detecte el archivo nixpacks.toml")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())