# MIKUNE 2 - Bot Multifuncional de Discord

## Solución de Problemas con los Módulos

Se han detectado problemas con la carga de algunos módulos debido a dependencias faltantes. Para solucionarlos, se proporcionan las siguientes herramientas:

### Opción 1: Instalación Automática (Recomendada)

Ejecuta el script de instalación de dependencias:

```bash
python install_dependencies.py
```

Este script instalará todas las dependencias necesarias para que los módulos funcionen correctamente.

### Opción 2: Instalación Manual

Si prefieres instalar las dependencias manualmente, puedes usar pip:

```bash
pip install -r requirements.txt
```

O instala las dependencias individuales:

```bash
pip install animec beautifulsoup4 asyncdagpi google-search-python jishaku
```

## Conflicto con Comandos

Se ha detectado un conflicto con el comando `serverinfo` que estaba definido tanto en `main.py` como en `cogs/general.py`. Este problema ha sido solucionado en el código actualizado.

## Problemas con `economy.py`

Si encuentras errores relacionados con `economy.py`, puede ser debido a un problema de llamada asíncrona. Sigue estos pasos:

1. Abre el archivo `cogs/economy.py`
2. Busca la función `setup(bot)` al final del archivo
3. Reemplázala con:

```python
async def setup(bot):
    await bot.add_cog(Economy(bot))
```

## Solución Automática

El bot ahora incluye un sistema de solución automática de problemas con extensiones que intentará arreglar los problemas comunes durante la carga de módulos.

## Ayuda Adicional

Si continúas experimentando problemas, consulta la documentación de Discord.py en [https://discordpy.readthedocs.io/](https://discordpy.readthedocs.io/) o busca ayuda en el servidor oficial de Discord.py.

## Despliegue en Easypanel (Docker)

Si estás experimentando problemas al desplegar MIKUNE 2 en Easypanel, sigue estas soluciones:

### Solución para "No space left on device"

Este error ocurre porque el proceso de construcción necesita más espacio en disco del disponible.

#### Opción 1: Usar un Dockerfile optimizado

Reemplaza el archivo `Dockerfile` existente con el siguiente contenido:

```Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema (mínimas necesarias)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo los archivos necesarios primero
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comandos para ejecutar el bot
CMD ["python", "main.py"]
```

#### Opción 2: Limpiar espacio en disco en el servidor

Si tienes acceso SSH al servidor donde está instalado Easypanel:

```bash
# Limpiar imágenes y contenedores no utilizados
docker system prune -af

# Verificar espacio en disco
df -h
```

#### Opción 3: Modificar easypanel.yml

Actualiza tu archivo `easypanel.yml` para usar una imagen base más ligera:

```yaml
build:
  type: dockerfile
  config:
    dockerfile: Dockerfile
resources:
  cpu: 1
  memory: 1024
```

### Después del Despliegue

Una vez desplegado correctamente, monitoriza el uso de recursos para evitar futuros problemas de espacio en disco.
