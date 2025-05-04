#!/usr/bin/env python3
"""
Script para eliminar completamente todos los archivos relacionados con Nixpacks
y preparar el proyecto para despliegue en Easypanel usando Docker estándar.
"""

import os
import shutil
import sys

def eliminar_nixpacks():
    """Elimina todos los directorios y archivos de Nixpacks"""
    elementos_borrados = 0
    
    # Eliminar el directorio .nixpacks si existe
    if os.path.exists('.nixpacks'):
        try:
            shutil.rmtree('.nixpacks')
            elementos_borrados += 1
            print("✓ Eliminado directorio .nixpacks en la raíz")
        except Exception as e:
            print(f"✗ Error al eliminar .nixpacks: {e}")
    
    # Buscar recursivamente cualquier otro directorio .nixpacks
    for raiz, dirs, _ in os.walk('.'):
        if '.nixpacks' in dirs:
            ruta_nixpacks = os.path.join(raiz, '.nixpacks')
            try:
                shutil.rmtree(ruta_nixpacks)
                elementos_borrados += 1
                print(f"✓ Eliminado directorio: {ruta_nixpacks}")
            except Exception as e:
                print(f"✗ Error al eliminar {ruta_nixpacks}: {e}")
    
    # Eliminar archivos relacionados con Nixpacks
    archivos_nixpacks = [
        'nixpacks.toml',
        '.nixpacksignore'
    ]
    
    for archivo in archivos_nixpacks:
        if os.path.exists(archivo):
            try:
                os.remove(archivo)
                elementos_borrados += 1
                print(f"✓ Eliminado archivo: {archivo}")
            except Exception as e:
                print(f"✗ Error al eliminar {archivo}: {e}")
    
    # Buscar archivos .nix recursivamente
    for raiz, _, archivos in os.walk('.'):
        for archivo in archivos:
            if archivo.endswith('.nix') or 'nixpkgs' in archivo:
                ruta_archivo = os.path.join(raiz, archivo)
                try:
                    os.remove(ruta_archivo)
                    elementos_borrados += 1
                    print(f"✓ Eliminado archivo: {ruta_archivo}")
                except Exception as e:
                    print(f"✗ Error al eliminar {ruta_archivo}: {e}")
    
    return elementos_borrados

def verificar_dockerfile():
    """Verifica que el Dockerfile esté correctamente configurado"""
    if not os.path.exists('Dockerfile'):
        print("✗ No se encontró el archivo Dockerfile en la raíz del proyecto")
        return False
    
    print("✓ Dockerfile encontrado correctamente")
    return True

def verificar_easypanel_yml():
    """Verifica que el archivo easypanel.yml esté correctamente configurado"""
    if not os.path.exists('easypanel.yml'):
        print("✗ No se encontró el archivo easypanel.yml en la raíz del proyecto")
        return False
    
    print("✓ Archivo easypanel.yml encontrado correctamente")
    return True

def main():
    """Función principal"""
    print("==== LIMPIEZA FINAL PARA DESPLIEGUE EN EASYPANEL ====")
    print("\nEliminando archivos de Nixpacks...")
    total = eliminar_nixpacks()
    
    print("\nVerificando archivos necesarios para el despliegue...")
    dockerfile_ok = verificar_dockerfile()
    easypanel_ok = verificar_easypanel_yml()
    
    print("\n==== RESUMEN ====")
    print(f"Elementos de Nixpacks eliminados: {total}")
    print(f"Dockerfile verificado: {'✓' if dockerfile_ok else '✗'}")
    print(f"easypanel.yml verificado: {'✓' if easypanel_ok else '✗'}")
    
    if not dockerfile_ok or not easypanel_ok:
        print("\n⚠️ ADVERTENCIA: Se encontraron problemas que podrían afectar el despliegue.")
        print("Por favor, asegúrate de que los archivos Dockerfile y easypanel.yml estén")
        print("correctamente configurados antes de realizar el despliegue.")
        return 1
    
    print("\n✓ Todo listo para el despliegue!")
    print("\nInstrucciones para el despliegue:")
    print("1. Sube estos cambios a tu repositorio Git")
    print("2. En Easypanel, configura tu aplicación para usar el Dockerfile")
    print("3. Asegúrate de que la ruta al Dockerfile sea ./Dockerfile")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())