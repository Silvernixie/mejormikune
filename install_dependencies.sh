#!/bin/bash

echo "Instalando dependencias necesarias para MIKUNE 2..."
echo

# Verificar si pip está instalado
if ! command -v pip &> /dev/null; then
    echo "ERROR: pip no está instalado."
    echo "Por favor, instala Python y pip correctamente."
    exit 1
fi

# Actualizar pip
echo "Actualizando pip..."
python3 -m pip install --upgrade pip

# Instalar/actualizar dependencias específicas primero
echo "Instalando PyNaCl (necesario para funciones de voz)..."
pip install "PyNaCl>=1.4.0"

echo "Instalando ffmpeg-python..."
pip install ffmpeg-python

# Comprobar la instalación de FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "ADVERTENCIA: FFmpeg no está instalado o no está en el PATH."
    echo "Necesitarás instalar FFmpeg para que la reproducción de audio funcione."
    echo "Para Ubuntu/Debian: sudo apt install ffmpeg"
    echo "Para Fedora: sudo dnf install ffmpeg"
    echo "Para macOS con Homebrew: brew install ffmpeg"
fi

# Instalar las demás dependencias desde requirements.txt
echo "Instalando dependencias restantes desde requirements.txt..."
pip install -r requirements.txt

echo
echo "Dependencias instaladas correctamente."
echo "Si encuentras algún error relacionado con FFmpeg, asegúrate de instalarlo según las instrucciones para tu sistema operativo."
