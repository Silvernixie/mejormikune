#!/usr/bin/env python3
"""
Script para eliminar completamente cualquier rastro de Nixpacks del proyecto.
"""
import os
import shutil
import sys

def eliminar_directorio_nixpacks():
    """Busca y elimina cualquier directorio .nixpacks en el proyecto."""
    print("Buscando directorios .nixpacks...")
    contador = 0
    
    # Buscar en la raíz y subcarpetas
    for raiz, dirs, _ in os.walk('.'):
        if '.nixpacks' in dirs:
            nixpacks_path = os.path.join(raiz, '.nixpacks')
            print(f"Encontrado directorio: {nixpacks_path}")
            try:
                shutil.rmtree(nixpacks_path)
                contador += 1
                print(f"✓ Eliminado directorio: {nixpacks_path}")
            except Exception as e:
                print(f"✗ Error al eliminar {nixpacks_path}: {e}")
    
    return contador

def eliminar_archivos_nixpacks():
    """Busca y elimina cualquier archivo relacionado con Nixpacks."""
    print("Buscando archivos relacionados con Nixpacks...")
    contador = 0
    
    archivos_nixpacks = [
        '.nixpacks/nixpkgs-bc8f8d1be58e8c8383e683a06e1e1e57893fff87.nix',
        'nixpacks.toml',
        '.nixpacksignore'
    ]
    
    for archivo in archivos_nixpacks:
        if os.path.exists(archivo):
            try:
                os.remove(archivo)
                contador += 1
                print(f"✓ Eliminado archivo: {archivo}")
            except Exception as e:
                print(f"✗ Error al eliminar {archivo}: {e}")
    
    return contador

def crear_dockerignore():
    """Crea un archivo .dockerignore específico para evitar Nixpacks."""
    contenido = """# Excluir directorios de Nixpacks
.nixpacks/
**/.nixpacks/

# Python cache
**/__pycache__/
**/*.py[cod]
**/*$py.class

# Otros archivos temporales
**/*.log
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
    print("=== ELIMINACIÓN DE NIXPACKS ===")

    total = 0
    total += eliminar_directorio_nixpacks()
    total += eliminar_archivos_nixpacks()
    crear_dockerignore()
    
    print(f"\n=== Operación completada. {total} elementos relacionados con Nixpacks eliminados ===")
    print("\nRecuerda ejecutar este script justo antes de hacer deploy a Easypanel.")
    return 0

if __name__ == "__main__":
    sys.exit(main())