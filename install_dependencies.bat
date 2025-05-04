@echo off
echo Instalando dependencias necesarias para MIKUNE 2...
echo.

REM Verificar si pip está instalado
where pip >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip no está instalado o no está en el PATH.
    echo Por favor, instala Python correctamente desde https://www.python.org/downloads/
    echo Asegúrate de marcar la opción "Add Python to PATH" durante la instalación.
    pause
    exit /b 1
)

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip

REM Instalar/actualizar dependencias específicas primero
echo Instalando PyNaCl (necesario para funciones de voz)...
pip install PyNaCl>=1.4.0

echo Instalando ffmpeg-python...
pip install ffmpeg-python

REM Comprobar la instalación de FFmpeg
where ffmpeg >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ADVERTENCIA: FFmpeg no está instalado o no está en el PATH.
    echo Necesitarás instalar FFmpeg manualmente para que la reproducción de audio funcione.
    echo Puedes descargarlo desde: https://ffmpeg.org/download.html
    echo Después de instalar, asegúrate de añadir FFmpeg a las variables de entorno PATH.
)

REM Instalar las demás dependencias desde requirements.txt
echo Instalando dependencias restantes desde requirements.txt...
pip install -r requirements.txt

echo.
echo Dependencias instaladas correctamente.
echo Si encuentras algún error relacionado con FFmpeg, asegúrate de instalarlo manualmente.
pause
