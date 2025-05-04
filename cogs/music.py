import discord
from discord.ext import commands
import asyncio
import logging
import yt_dlp  # Cambiado de youtube_dl a yt_dlp
import re
import os
import sys
import random
from urllib.parse import parse_qs, urlparse
from discord.ui import Button, View
from async_timeout import timeout
import time
import aiohttp
from datetime import datetime

# Configuración de logger para este módulo
logger = logging.getLogger('MIKUNE 2')

# Importación directa de PyNaCl y configuración de la variable PATH para que encuentre las DLLs necesarias
try:
    # Importar directamente las librerías de nacl primero para verificar que están instaladas
    import nacl
    from nacl.secret import SecretBox  # Importamos clases específicas para forzar la carga
    
    # Configurar variable de entorno para señalar donde buscar las DLLs
    python_path = os.path.dirname(sys.executable)
    if python_path not in os.environ.get('PATH', ''):
        os.environ['PATH'] = f"{python_path};{os.environ.get('PATH', '')}"
        
    # Si llegamos aquí, PyNaCl está instalado y configurado
    VOICE_ENABLED = True
    logger.info("PyNaCl encontrado y configurado correctamente")
except (ImportError, AttributeError) as e:
    logger.error(f"Error al cargar PyNaCl: {e}")
    VOICE_ENABLED = False
    logger.warning("ADVERTENCIA: Funcionalidad de voz deshabilitada porque PyNaCl no está instalado correctamente")

# Encontrar ruta de ffmpeg
FFMPEG_PATH = None
for path in ["bin/ffmpeg.exe", "bin/ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
    if os.path.exists(path):
        FFMPEG_PATH = path
        logger.info(f"ffmpeg encontrado en: {FFMPEG_PATH}")
        break
if not FFMPEG_PATH:
    logger.warning("ADVERTENCIA: ffmpeg no fue encontrado. La reproducción de música no funcionará.")

# Ruta al archivo de cookies
COOKIES_FILE = 'cookies.txt'
# Variable para controlar si se usan cookies
USE_COOKIES = os.path.exists(COOKIES_FILE)

# User agents aleatorios para simular un navegador real
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

# Configuración mejorada para yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,  # Permitimos listas de reproducción
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch', # Siempre usar búsqueda de YouTube
    'source_address': '0.0.0.0',
    # Opciones generales
    'extract_flat': True,
    'skip_download': True,
    'cachedir': False,
    # Opciones anti-throttling
    'audioquality': '192',
    'retries': 10,
    'fragment_retries': 10,
    'extractor_retries': 5,
    'file_access_retries': 5,
    'retry_sleep_functions': {'http': lambda x: 5 * (2 ** (x - 1))},
    # Encabezados para reducir restricciones y parecer humano
    'http_headers': {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Referer': 'https://www.youtube.com/',
        'Origin': 'https://www.youtube.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Connection': 'keep-alive',
    }
}

# Mejorar opciones de ffmpeg para mayor estabilidad y calidad
ffmpeg_options = {
    'options': '-vn -af "loudnorm=I=-16:TP=-1:LRA=13"', # Normalización de volumen
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -analyzeduration 2147483647 -probesize 2147483647'
}

# Instancia de yt-dlp que se rotará periódicamente
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
YTDL_LAST_REFRESH = time.time()

# Función para refrescar la instancia de yt-dlp con nuevos valores
def refresh_ytdl_instance():
    global ytdl, YTDL_LAST_REFRESH
    # Actualizar User-Agent y otras configuraciones aleatorias para parecer humano
    current_options = dict(ytdl_format_options)
    current_options['http_headers']['User-Agent'] = random.choice(USER_AGENTS)
    
    # Agregar timestamp para evitar cacheo
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    current_options['http_headers']['Cache-Control'] = f'max-age=0, no-cache, no-store, must-revalidate, t={current_time}'
    current_options['http_headers']['Pragma'] = 'no-cache'
    current_options['http_headers']['Expires'] = '0'
    
    # Agregar soporte de cookies si está habilitado y el archivo existe
    if USE_COOKIES and os.path.exists(COOKIES_FILE):
        current_options['cookiefile'] = COOKIES_FILE
        logger.info(f"Usando cookies del archivo: {COOKIES_FILE}")
    
    # Recrear la instancia
    ytdl = yt_dlp.YoutubeDL(current_options)
    YTDL_LAST_REFRESH = time.time()
    logger.info("Instancia de yt-dlp refrescada con nuevos headers")
    
# Verificar si es necesario refrescar la instancia de yt-dlp
def check_ytdl_refresh():
    # Refrescar cada 15 minutos o aproximadamente
    if time.time() - YTDL_LAST_REFRESH > 900:  # 15 minutos
        refresh_ytdl_instance()

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Título desconocido')
        self.url = data.get('url', data.get('webpage_url', ''))
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.webpage_url = data.get('webpage_url', '')
        # Información extra de YouTube para enriquecer la experiencia
        self.channel = data.get('channel', data.get('uploader', 'Canal desconocido'))
        self.views = data.get('view_count', 0)
        self.upload_date = data.get('upload_date', '')
        self.original_url = self.url  # Guardar URL original para reconexiones

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        
        # Verificar y refrescar yt-dlp si es necesario
        check_ytdl_refresh()
            
        # Verificar si ffmpeg está disponible
        if not FFMPEG_PATH:
            raise RuntimeError("ffmpeg no fue encontrado. Por favor instala ffmpeg para poder reproducir música.")
            
        # Extraer información del video
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            
            if 'entries' in data:
                # Toma el primer elemento de una playlist
                data = data['entries'][0]
            
            # Obtener la URL de audio con errores específicos
            if stream:
                if 'url' not in data:
                    error_msg = "No se pudo obtener la URL de streaming del video."
                    if 'is_live' in data and data['is_live']:
                        error_msg += " Es posible que se trate de un stream en vivo, que no es compatible."
                    elif 'age_limit' in data and data['age_limit'] > 0:
                        error_msg += " El video tiene restricción de edad y requiere verificación."
                    elif 'webpage_url' in data and "consent" in data['webpage_url']:
                        error_msg += " YouTube está pidiendo consentimiento para cookies."
                    raise RuntimeError(error_msg)
                
                url = data['url']
                # Modificaciones temporales a ffmpeg_options para este audio específico
                current_ffmpeg_options = dict(ffmpeg_options)
                
                # Si es un video largo, ajustar parámetros
                if data.get('duration', 0) > 1800:  # 30 minutos
                    logger.info(f"Video largo detectado ({data.get('duration')/60:.1f} min), ajustando parámetros...")
                    current_ffmpeg_options['before_options'] += ' -http_persistent 0'
                
                audio_source = discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH, **current_ffmpeg_options)
                return cls(audio_source, data=data)
            else:
                # Descargar el archivo - pero generalmente usamos streaming
                filename = ytdl.prepare_filename(data)
                audio_source = discord.FFmpegPCMAudio(filename, executable=FFMPEG_PATH, **ffmpeg_options)
                return cls(audio_source, data=data)
        except Exception as e:
            logger.error(f"Error en YTDLSource.from_url: {str(e)}")
            # Enriquecer mensaje de error para mayor claridad
            error_msg = str(e)
            if "429" in error_msg:
                error_msg = "YouTube está limitando las solicitudes (error 429). Intenta más tarde."
            elif "403" in error_msg:
                error_msg = "Acceso prohibido por YouTube (error 403). Puede ser una restricción geográfica."
            raise RuntimeError(f"Error obteniendo audio: {error_msg}")
    
    @classmethod
    async def reconnect(cls, original_source, *, loop=None):
        """Intenta reconectar un source que ha fallado"""
        loop = loop or asyncio.get_event_loop()
        
        # Refrescar yt-dlp para evitar restricciones
        refresh_ytdl_instance()
        
        try:
            # Obtener la URL original o la URL de la página
            url = getattr(original_source, 'original_url', None) or getattr(original_source, 'webpage_url', None)
            if not url:
                # Fallback a la URL de la data si existe
                url = original_source.data.get('webpage_url', '')
            
            if not url:
                raise ValueError("No se encontró una URL válida para reconectar")
                
            logger.info(f"Intentando reconectar a: {url}")
            
            # Obtener nuevos datos
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                data = data['entries'][0]
                
            # Crear un nuevo source con los datos actualizados
            if 'url' not in data:
                raise ValueError("No se pudo obtener la URL de streaming en la reconexión")
                
            new_url = data['url']
            # Opciones especiales para la reconexión
            reconnect_ffmpeg_options = dict(ffmpeg_options)
            reconnect_ffmpeg_options['before_options'] += ' -http_persistent 0'
            
            audio_source = discord.FFmpegPCMAudio(new_url, executable=FFMPEG_PATH, **reconnect_ffmpeg_options)
            
            # Crear nuevo source pero preservar metadatos originales
            source = cls(audio_source, data=data)
            source.original_url = url  # Guardar la URL original
            
            return source
        except Exception as e:
            logger.error(f"Error en reconexión: {str(e)}")
            raise

class MusicPlayer:
    """Una clase para manejar la reproducción de música en un servidor"""
    
    def __init__(self, ctx):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.cog = ctx.cog
        
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        
        self.current = None
        self.volume = 0.5
        self.now_playing_message = None
        self.retry_count = 0
        self.last_error_time = 0
        
        ctx.bot.loop.create_task(self.player_loop())
        
    async def player_loop(self):
        """El buclo principal para manejar la reproducción de canciones"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            self.next.clear()
            
            try:
                async with timeout(300):  # 5 minutos
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                # Si no hay canciones durante 5 minutos, el reproductor se destruye
                return self.destroy(self.guild)
            
            try:
                # Reproducción de la canción
                self.current = source
                logger.info(f"Intentando reproducir: {source.title}")
                
                # Registro de información detallada para depuración
                logger.debug(f"URL de audio: {source.url}")
                logger.debug(f"FFmpeg path: {FFMPEG_PATH}")
                
                # Iniciar la reproducción con manejo de errores mejorado
                if not hasattr(source, '_source'):
                    # Verificar si ya tiene un _source interno para evitar doble wrap
                    try:
                        # Intentar recrear el audio source si es necesario
                        if not hasattr(source, 'original_url') and hasattr(source.data, 'url'):
                            source.original_url = source.data['url']
                            
                        audio_url = getattr(source, 'original_url', source.url)
                        logger.debug(f"Usando URL de audio: {audio_url}")
                        
                        # Crear un nuevo PCM con las opciones actualizadas
                        new_ffmpeg_options = dict(ffmpeg_options)
                        new_ffmpeg_options['before_options'] = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -analyzeduration 2147483647 -probesize 2147483647'
                        
                        audio_source = discord.FFmpegPCMAudio(
                            audio_url, 
                            executable=FFMPEG_PATH,
                            **new_ffmpeg_options
                        )
                        source._source = audio_source
                    except Exception as e:
                        logger.error(f"Error recreando audio source: {e}")
                        raise
                
                # Intentar reproducir la canción
                try:
                    self.guild.voice_client.play(
                        source, 
                        after=lambda e: self.bot.loop.call_soon_threadsafe(
                            lambda: self._handle_playback_completion(e)
                        )
                    )
                    
                    # Resetear contador de reintentos al reproducir exitosamente
                    self.retry_count = 0
                except Exception as e:
                    logger.error(f"Error al iniciar reproducción: {e}")
                    # Intentar un fallback si es un error de formato
                    if "Error during playback" in str(e) or "ffmpeg exited with non-zero status" in str(e):
                        logger.warning("Intentando recuperación con formato alternativo...")
                        raise RuntimeError("Error de formato, intentando recuperación...")
                    else:
                        raise
                
                # Crear un mensaje con botones de control
                embed = discord.Embed(
                    title="🎵 Reproduciendo ahora",
                    description=f"[{source.title}]({source.data.get('webpage_url', '')})",
                    color=discord.Color.green()
                )
                
                if source.thumbnail:
                    embed.set_thumbnail(url=source.thumbnail)
                
                # Añadir información enriquecida
                duration = self.format_duration(source.duration) if source.duration else "Desconocido"
                embed.add_field(name="⏱️ Duración", value=duration, inline=True)
                
                # Mostrar canal de YouTube si está disponible
                if hasattr(source, 'channel') and source.channel:
                    embed.add_field(name="📺 Canal", value=source.channel, inline=True)
                
                # Mostrar vistas si están disponibles
                if hasattr(source, 'views') and source.views:
                    views_formatted = "{:,}".format(source.views).replace(",", ".")
                    embed.add_field(name="👁️ Vistas", value=views_formatted, inline=True)
                
                # Añadir fecha de subida formateada si está disponible
                if hasattr(source, 'upload_date') and source.upload_date:
                    # Formatear fecha YYYYMMDD a DD/MM/YYYY
                    if len(source.upload_date) == 8:
                        try:
                            year = source.upload_date[0:4]
                            month = source.upload_date[4:6]
                            day = source.upload_date[6:8]
                            formatted_date = f"{day}/{month}/{year}"
                            embed.add_field(name="📅 Subido", value=formatted_date, inline=True)
                        except:
                            pass
                
                # Añadir nota sobre calidad
                embed.set_footer(text="Reproduciendo desde YouTube | Mejor calidad disponible")
                
                view = MusicControlView(self)
                self.now_playing_message = await self.channel.send(embed=embed, view=view)
                
                # Esperar hasta que la canción termine
                await self.next.wait()
                
            except asyncio.CancelledError:
                # Si la tarea fue cancelada, salir limpiamente
                break
            except Exception as e:
                # Capturar errores durante la reproducción
                logger.error(f"Error durante la reproducción: {str(e)}")
                
                # Limitar reintentos automáticos para evitar spam en caso de errores persistentes
                current_time = time.time()
                if current_time - self.last_error_time > 60:  # Resetear conteo después de 1 minuto sin errores
                    self.retry_count = 0
                self.last_error_time = current_time
                
                if self.retry_count < 3:  # Limitar a 3 reintentos consecutivos
                    self.retry_count += 1
                    
                    # Intentar reconectar el source si es posible
                    try:
                        if source and hasattr(source, 'data'):
                            await self.channel.send("⚠️ Error durante la reproducción. Intentando reconectar...")
                            
                            # Detener la reproducción actual si hay alguna
                            if self.guild.voice_client and (self.guild.voice_client.is_playing() or self.guild.voice_client.is_paused()):
                                self.guild.voice_client.stop()
                                
                            # Intentar reconectar
                            new_source = await YTDLSource.reconnect(source, loop=self.bot.loop)
                            if new_source:
                                # Volver a poner en la cola
                                await self.queue.put(new_source)
                                await self.channel.send("✅ Reconexión exitosa. Intentando reproducir nuevamente...")
                                
                            # No señalar next aquí para permitir que se procese el nuevo source
                            continue
                    except Exception as reconnect_error:
                        logger.error(f"Error en reconexión: {str(reconnect_error)}")
                        await self.channel.send(f"❌ No se pudo reconectar: {str(reconnect_error)}")
                
                # Si llegamos aquí, no pudimos reconectar o superamos el límite de reintentos
                await self.channel.send(f"❌ Error reproduciendo: {str(e)}")
                
                # Detener la reproducción actual si hubo un error
                if self.guild.voice_client and (self.guild.voice_client.is_playing() or self.guild.voice_client.is_paused()):
                    self.guild.voice_client.stop()
                    
                # Esperar un poco antes de intentar la siguiente canción
                await asyncio.sleep(1)
                
                # Señalar que estamos listos para la siguiente canción
                self.next.set()
            finally:
                # Limpiar recursos
                if self.now_playing_message:
                    try:
                        await self.now_playing_message.delete()
                    except discord.HTTPException:
                        pass
                        
                if source:
                    try:
                        source.cleanup()
                    except Exception as e:
                        logger.error(f"Error en cleanup: {e}")
                self.current = None
    
    def _handle_playback_completion(self, error):
        """Maneja la finalización de la reproducción, con o sin error"""
        if error:
            logger.error(f"Error en la reproducción: {error}")
        
        # Señalar que la canción ha terminado
        self.next.set()
        
    def destroy(self, guild):
        """Limpia y destruye el reproductor de música"""
        return self.bot.loop.create_task(self.cog.cleanup(guild))
        
    @staticmethod
    def format_duration(duration):
        """Formatea segundos en formato mm:ss o hh:mm:ss"""
        if not duration:
            return "Desconocido"
            
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        else:
            return f"{int(minutes):02d}:{int(seconds):02d}"

class MusicControlView(View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player = player
        
        # Añadir botones con iconos más descriptivos
        self.add_item(Button(style=discord.ButtonStyle.primary, emoji="⏸️", custom_id="pause", label="Pausar"))
        self.add_item(Button(style=discord.ButtonStyle.success, emoji="▶️", custom_id="resume", label="Reanudar"))
        self.add_item(Button(style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="stop", label="Detener"))
        self.add_item(Button(style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="skip", label="Saltar"))
        self.add_item(Button(style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="reload", label="Reconectar"))
        
    async def interaction_check(self, interaction):
        if interaction.data["custom_id"] == "pause":
            if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
                interaction.guild.voice_client.pause()
                await interaction.response.send_message("⏸️ Reproducción pausada.", ephemeral=True)
        
        elif interaction.data["custom_id"] == "resume":
            if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
                interaction.guild.voice_client.resume()
                await interaction.response.send_message("▶️ Reproducción reanudada.", ephemeral=True)
                
        elif interaction.data["custom_id"] == "stop":
            if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
                interaction.guild.voice_client.stop()
                await interaction.response.send_message("⏹️ Reproducción detenida.", ephemeral=True)
                
        elif interaction.data["custom_id"] == "skip":
            if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
                interaction.guild.voice_client.stop()
                await interaction.response.send_message("⏭️ Canción saltada.", ephemeral=True)
                
        elif interaction.data["custom_id"] == "reload":
            if interaction.guild.voice_client:
                # Obtener el source actual
                source = self.player.current
                if source:
                    try:
                        # Informar al usuario
                        await interaction.response.send_message("🔄 Intentando reconectar...", ephemeral=True)
                        
                        # Detener reproducción actual
                        if interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused():
                            interaction.guild.voice_client.stop()
                            
                        # Intentar reconectar
                        new_source = await YTDLSource.reconnect(source, loop=self.player.bot.loop)
                        if new_source:
                            # Volver a poner en la cola
                            await self.player.queue.put(new_source)
                            self.player.next.set()  # Forzar avance al siguiente elemento (que es el reconectado)
                            
                            # Enviar mensaje de éxito
                            await interaction.followup.send("✅ Reconexión exitosa. Reproduciendo de nuevo...", ephemeral=True)
                    except Exception as e:
                        logger.error(f"Error al reconectar desde interacción: {e}")
                        await interaction.followup.send(f"❌ No se pudo reconectar: {str(e)}", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ No hay música reproduciéndose actualmente.", ephemeral=True)
                
        return True

class SearchView(View):
    def __init__(self, options, timeout=60):
        super().__init__(timeout=timeout)
        self.selected_option = None
        
        # Añadir hasta 5 resultados como botones
        for i, option in enumerate(options[:5], start=1):
            # Limitar el título para evitar que los botones sean demasiado grandes
            title = option['title'][:30] + "..." if len(option['title']) > 30 else option['title']
            
            button = Button(
                label=f"{i}. {title}",
                style=discord.ButtonStyle.primary,
                custom_id=f"search_{i}"
            )
            button.callback = self.make_callback(option['url'])
            self.add_item(button)
            
        # Botón para cancelar
        cancel_button = Button(
            label="Cancelar",
            style=discord.ButtonStyle.danger,
            custom_id="cancel"
        )
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)
        
    def make_callback(self, url):
        async def callback(interaction):
            self.selected_option = url
            await interaction.response.send_message(f"✅ Seleccionada: {url}", ephemeral=True)
            self.stop()
        return callback
    
    async def cancel_callback(self, interaction):
        await interaction.response.send_message("❌ Búsqueda cancelada.", ephemeral=True)
        self.stop()

class Music(commands.Cog):
    """Comandos para reproducir música en canales de voz"""

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        """Limpia los recursos y desconecta el bot del canal de voz"""
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass
            
        try:
            del self.players[guild.id]
        except KeyError:
            pass

    def get_player(self, ctx):
        """Recupera o crea un reproductor de música para el servidor"""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player
            
        return player

    async def direct_url_play(self, ctx, track_info):
        """Función especializada para reproducir una URL directamente"""
        try:
            # Verificar si ffmpeg está disponible
            if not FFMPEG_PATH:
                return await ctx.send("❌ No se pudo reproducir la música porque ffmpeg no fue encontrado.")
            
            # Verificar que tenemos una URL válida
            if 'url' not in track_info:
                logger.error(f"No hay URL en track_info: {track_info}")
                return await ctx.send("❌ No se pudo extraer la URL de audio.")
                
            # Registrar información detallada para depuración
            logger.debug(f"URL de audio a reproducir: {track_info['url']}")
            logger.debug(f"Formato: {track_info.get('format')}")
            logger.debug(f"Extensión: {track_info.get('ext')}")
            
            # Crear opciones específicas para este audio
            current_ffmpeg_options = dict(ffmpeg_options)
            
            # Crear source con manejo especial según el tipo de archivo
            try:
                # Usar FFmpegPCMAudio con opciones mejoradas
                audio_source = discord.FFmpegPCMAudio(
                    track_info['url'], 
                    executable=FFMPEG_PATH,
                    **current_ffmpeg_options
                )
                
                # Crear transformador de volumen
                source = discord.PCMVolumeTransformer(audio_source, volume=0.5)
                
                # Asignar metadatos
                title = track_info.get('title', 'Título desconocido')
                artist = track_info.get('artist', '')
                source.title = f"{title}{' - ' + artist if artist else ''}"
                source.url = track_info['url']
                source.data = track_info
                source.duration = track_info.get('duration')
                source.thumbnail = track_info.get('thumbnail')
                source.cleanup = lambda: None
                
                # Obtener reproductor y añadir a la cola
                player = self.get_player(ctx)
                await player.queue.put(source)
                
                return True, f"✅ Añadido a la cola: **{source.title}**"
            except Exception as e:
                logger.error(f"Error creando FFmpegPCMAudio: {str(e)}")
                return False, f"❌ Error al procesar el audio: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error en direct_url_play: {str(e)}")
            return False, f"❌ Error inesperado: {str(e)}"

    @commands.command()
    async def join(self, ctx):
        """Une el bot al canal de voz"""
        if not VOICE_ENABLED:
            return await ctx.send("La funcionalidad de voz está deshabilitada porque PyNaCl no está disponible.")
        
        if ctx.author.voice is None:
            return await ctx.send("Necesitas estar en un canal de voz para usar este comando.")
        
        voice_channel = ctx.author.voice.channel
        
        try:
            if ctx.voice_client is None:
                # Conectar sin silenciar ni ensordecer
                await voice_channel.connect()
            else:
                await ctx.voice_client.move_to(voice_channel)
            
            await ctx.send(f"Me he unido a {voice_channel.name}")
        except Exception as e:
            logger.error(f"Error al unirse al canal de voz: {str(e)}")
            await ctx.send(f"No se pudo unir al canal de voz: {str(e)}")

    @commands.command()
    async def leave(self, ctx):
        """Desconecta el bot del canal de voz"""
        if ctx.voice_client:
            await self.cleanup(ctx.guild)
            await ctx.send("Me he desconectado del canal de voz.")
        else:
            await ctx.send("No estoy conectado a ningún canal de voz.")

    @commands.command()
    async def play(self, ctx, *, query=None):
        """Reproduce música desde YouTube - puedes usar URLs o términos de búsqueda"""
        if not VOICE_ENABLED:
            return await ctx.send("La funcionalidad de voz está deshabilitada porque PyNaCl no está disponible.")
            
        if not ctx.voice_client:
            try:
                await ctx.invoke(self.join)
            except Exception as e:
                return await ctx.send(f"No se pudo unir al canal de voz: {str(e)}")
        
        if query is None:
            return await ctx.send("Por favor, proporciona una canción para reproducir.")
        
        async with ctx.typing():
            # Verificar si es una URL o un término de búsqueda
            is_url = re.match(r'https?://', query) is not None
            
            try:
                if is_url:
                    # Es una URL (YouTube, SoundCloud, etc.)
                    # Verificar y refrescar yt-dlp si es necesario
                    check_ytdl_refresh()
                    
                    info = await self.bot.loop.run_in_executor(
                        None, 
                        lambda: ytdl.extract_info(query, download=False)
                    )
                    
                    if 'entries' in info:
                        # Es una playlist
                        await ctx.send(f"📝 Esta URL contiene {len(info['entries'])} canciones. Añadiendo todas a la cola...")
                        
                        # Limitar el número de canciones para evitar abuso
                        max_songs = min(len(info['entries']), 50)
                        added_count = 0
                        
                        for i, entry in enumerate(info['entries'][:max_songs]):
                            try:
                                # Si no tiene URL, tenemos que obtener más información
                                if 'url' not in entry:
                                    detailed_info = await self.bot.loop.run_in_executor(
                                        None, 
                                        lambda: ytdl.extract_info(entry['url'] if 'url' in entry else entry['webpage_url'], download=False)
                                    )
                                    url = detailed_info['url']
                                    entry.update(detailed_info)
                                else:
                                    url = entry['url']
                                
                                audio_source = discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH, **ffmpeg_options)
                                source = discord.PCMVolumeTransformer(audio_source, volume=0.5)
                                source.title = entry.get('title', 'Título desconocido')
                                source.url = url
                                source.data = entry
                                source.duration = entry.get('duration')
                                source.thumbnail = entry.get('thumbnail')
                                source.original_url = entry.get('webpage_url', '')
                                source.cleanup = lambda: None
                                
                                player = self.get_player(ctx)
                                await player.queue.put(source)
                                added_count += 1
                                
                                # Solo mostrar notificación para las primeras 5 canciones para no saturar el chat
                                if i < 5:
                                    await ctx.send(f"➕ Añadido: **{source.title}**")
                            except Exception as e:
                                logger.error(f"Error procesando pista {i+1} de la playlist: {str(e)}")
                                # Sólo mostrar error para las primeras canciones
                                if i < 2:
                                    await ctx.send(f"⚠️ Error procesando una pista de la playlist: {str(e)}")
                        
                        # Mensaje final de resumen
                        await ctx.send(f"✅ Se agregaron {added_count} canciones a la cola.")
                    else:
                        # Es una pista individual
                        url = info['url']
                        audio_source = discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH, **ffmpeg_options)
                        source = discord.PCMVolumeTransformer(audio_source, volume=0.5)
                        source.title = info.get('title', 'Título desconocido')
                        source.url = url
                        source.data = info
                        source.duration = info.get('duration')
                        source.thumbnail = info.get('thumbnail')
                        source.webpage_url = info.get('webpage_url', '')
                        source.original_url = url
                        source.cleanup = lambda: None
                        
                        player = self.get_player(ctx)
                        await player.queue.put(source)
                        await ctx.send(f"✅ Añadido a la cola: **{source.title}**")
                else:
                    # Es un término de búsqueda
                    await ctx.send(f"🔍 Buscando en YouTube: `{query}`")
                    
                    # Búsqueda en YouTube
                    search_query = f"ytsearch5:{query}"
                    
                    # Verificar y refrescar yt-dlp si es necesario
                    check_ytdl_refresh()
                    
                    info = await self.bot.loop.run_in_executor(
                        None, 
                        lambda: ytdl.extract_info(search_query, download=False)
                    )
                    
                    if 'entries' not in info or not info['entries']:
                        return await ctx.send("❌ No se encontraron resultados.")
                        
                    results = info['entries']
                    
                    # Crear la vista con botones para seleccionar
                    view = SearchView(results)
                    
                    # Crear un mensaje con los resultados
                    result_text = "**🔍 Resultados de YouTube:**\n"
                    for i, entry in enumerate(results[:5], start=1):
                        duration = self.format_duration(entry.get('duration', 0))
                        title = entry.get('title', 'Título desconocido')
                        uploader = entry.get('uploader', 'Canal desconocido')
                        result_text += f"{i}. **{title}** ({duration}) - *{uploader}*\n"
                    
                    message = await ctx.send(result_text, view=view)
                    
                    # Esperar la selección
                    await view.wait()
                    
                    # Procesar la selección
                    if view.selected_option:
                        try:
                            # Extraer información del video seleccionado
                            video_url = view.selected_option
                            video_info = await self.bot.loop.run_in_executor(
                                None, 
                                lambda: ytdl.extract_info(video_url, download=False)
                            )
                            
                            # Verificar si ffmpeg está disponible
                            if not FFMPEG_PATH:
                                await ctx.send("❌ No se pudo reproducir la música porque ffmpeg no fue encontrado.")
                                return
                                
                            url = video_info['url']
                            audio_source = discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH, **ffmpeg_options)
                            source = discord.PCMVolumeTransformer(audio_source, volume=0.5)
                            source.title = video_info.get('title', 'Título desconocido')
                            source.url = url
                            source.data = video_info
                            source.duration = video_info.get('duration')
                            source.thumbnail = video_info.get('thumbnail')
                            source.webpage_url = video_info.get('webpage_url', '')
                            source.original_url = url
                            
                            # Método de limpieza para el source
                            source.cleanup = lambda: None
                            
                            player = self.get_player(ctx)
                            await player.queue.put(source)
                            await ctx.send(f"✅ Añadido a la cola: **{source.title}**")
                        except Exception as e:
                            logger.error(f"Error procesando selección: {str(e)}")
                            await ctx.send(f"❌ Error al procesar la canción seleccionada: {str(e)}")
                    else:
                        await ctx.send("❌ No se seleccionó ninguna canción o se agotó el tiempo.")
                        
                    # Limpiar el mensaje de resultados
                    try:
                        await message.delete()
                    except:
                        pass
                        
            except Exception as e:
                logger.error(f"Error en reproducción: {str(e)}")
                error_msg = str(e)
                
                # Mensajes de error más amigables para problemas comunes
                if "429" in error_msg:
                    error_msg = "YouTube está limitando las solicitudes. Intenta más tarde (error 429)."
                elif "403" in error_msg:
                    error_msg = "YouTube ha bloqueado la solicitud. Puede ser una restricción regional (error 403)."
                elif "This video is unavailable" in error_msg:
                    error_msg = "Este video no está disponible para reproducción en Discord."
                
                await ctx.send(f"❌ Ha ocurrido un error: {error_msg}")
                
                # Sugerir reproducción alternativa si es un error de video específico
                if "video" in error_msg.lower() and "unavailable" in error_msg.lower():
                    await ctx.send("💡 Intenta con otra canción o con una búsqueda por el título en lugar de la URL.")

    @commands.command()
    async def stop(self, ctx):
        """Detiene la reproducción actual y limpia la cola"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            # También limpiar la cola
            player = self.get_player(ctx)
            # Vaciar la cola existente
            while not player.queue.empty():
                try:
                    player.queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            await ctx.send("⏹️ Reproducción detenida y cola limpiada.")
        else:
            await ctx.send("No hay nada reproduciéndose actualmente.")

    @commands.command()
    async def pause(self, ctx):
        """Pausa la reproducción actual"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Reproducción pausada.")
        else:
            await ctx.send("No hay nada reproduciéndose actualmente.")

    @commands.command()
    async def resume(self, ctx):
        """Reanuda la reproducción pausada"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Reproducción reanudada.")
        else:
            await ctx.send("No hay nada pausado actualmente.")

    @commands.command()
    async def skip(self, ctx):
        """Salta a la siguiente canción en la cola"""
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("⏭️ Saltando a la siguiente canción...")
        else:
            await ctx.send("No hay nada reproduciéndose actualmente.")

    @commands.command()
    async def queue(self, ctx):
        """Muestra la cola de reproducción actual"""
        player = self.get_player(ctx)
        
        if player.queue.empty() and not player.current:
            return await ctx.send("La cola está vacía.")
            
        # Crear un embed para la cola
        embed = discord.Embed(
            title="🎵 Cola de reproducción",
            color=discord.Color.blue()
        )
        
        # Canción actual
        if player.current:
            current_title = player.current.title
            current_url = player.current.data.get('webpage_url', '')
            current_duration = self.format_duration(player.current.duration)
            
            embed.add_field(
                name="▶️ Reproduciendo ahora:",
                value=f"[{current_title}]({current_url}) | `{current_duration}`",
                inline=False
            )
            
            # Añadir thumbnail si está disponible
            if player.current.thumbnail:
                embed.set_thumbnail(url=player.current.thumbnail)
        
        # Próximas canciones
        queue_list = []
        position = 1
        
        if not player.queue.empty():
            # Esto es complicado porque Queue no admite iteración no destructiva
            # Solución: copiar la cola, listar elementos y reconstruir
            temp_queue = []
            
            # Vaciar la cola temporalmente para listar
            while not player.queue.empty():
                item = player.queue.get_nowait()
                temp_queue.append(item)
                
                # Obtener duración formateada
                duration = self.format_duration(item.duration) if item.duration else "??:??"
                
                # Añadir a la lista formateada
                queue_list.append(f"{position}. [{item.title}]({item.data.get('webpage_url', '')}) | `{duration}`")
                position += 1
                
            # Reconstruir la cola
            for item in temp_queue:
                player.queue.put_nowait(item)
            
            embed.add_field(
                name="📋 Próximas canciones:",
                value="\n".join(queue_list) if queue_list else "No hay canciones en cola",
                inline=False
            )
        else:
            embed.add_field(
                name="📋 Próximas canciones:",
                value="No hay canciones en cola",
                inline=False
            )
            
        # Añadir información del servidor
        embed.set_footer(text=f"Servidor: {ctx.guild.name} | Reproduciendo con YouTube", 
                        icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            
        await ctx.send(embed=embed)

    @commands.command(name="msearch", aliases=["ytbuscar", "mbuscar"])
    async def music_search(self, ctx, *, query=None):
        """Busca canciones en YouTube sin reproducirlas inmediatamente"""
        if query is None:
            return await ctx.send("Por favor, proporciona un término de búsqueda.")
            
        async with ctx.typing():
            try:
                # Buscar en YouTube
                await ctx.send(f"🔍 Buscando en YouTube: `{query}`")
                
                # Verificar y refrescar yt-dlp si es necesario
                check_ytdl_refresh()
                
                # Aumentar número de resultados para búsquedas específicas
                search_query = f"ytsearch8:{query}"
                
                info = await self.bot.loop.run_in_executor(
                    None, 
                    lambda: ytdl.extract_info(search_query, download=False)
                )
                
                if 'entries' not in info or not info['entries']:
                    return await ctx.send("❌ No se encontraron resultados.")
                    
                results = info['entries']
                
                # Crear un embed con los resultados
                embed = discord.Embed(
                    title=f"🔍 Resultados de búsqueda: '{query}'",
                    color=discord.Color.blue(),
                    description="Usa `.play [número]` o `.play [URL]` para reproducir una canción"
                )
                
                for i, entry in enumerate(results[:8], start=1):
                    duration = self.format_duration(entry.get('duration', 0))
                    title = entry.get('title', 'Título desconocido')
                    url = entry.get('webpage_url', '')
                    uploader = entry.get('uploader', 'Canal desconocido')
                    views = entry.get('view_count', 0)
                    views_fmt = "{:,}".format(views).replace(",", ".") if views else "Desconocido"
                    
                    value = f"⏱️ `{duration}` | 👁️ `{views_fmt} vistas`\n📺 {uploader}\n[Ver en YouTube]({url})"
                    embed.add_field(name=f"{i}. {title}", value=value, inline=False)
                
                # Añadir thumbnail del primer resultado
                if results and results[0].get('thumbnail'):
                    embed.set_thumbnail(url=results[0]['thumbnail'])
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error en búsqueda: {str(e)}")
                await ctx.send(f"❌ Error durante la búsqueda: {str(e)}")

    @commands.command(name="cookies")
    @commands.has_permissions(administrator=True)
    async def toggle_cookies(self, ctx, action=None):
        """Gestiona el uso de cookies para la reproducción de música
        
        Uso:
        >>cookies status - Muestra el estado actual
        >>cookies enable - Activa el uso de cookies
        >>cookies disable - Desactiva el uso de cookies
        
        Las cookies son útiles para acceder a contenido restringido o que requiere inicio de sesión.
        """
        global USE_COOKIES
        
        if action is None or action.lower() == "status":
            # Mostrar el estado actual
            cookie_status = "✅ **Habilitadas**" if USE_COOKIES else "❌ **Deshabilitadas**"
            cookie_file = "✅ **Encontrado**" if os.path.exists(COOKIES_FILE) else "❌ **No encontrado**"
            
            embed = discord.Embed(
                title="🍪 Estado de Cookies para YouTube",
                description="Las cookies permiten acceder a contenido que normalmente requiere inicio de sesión.",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Estado actual", value=cookie_status, inline=True)
            embed.add_field(name="Archivo de cookies", value=cookie_file, inline=True)
            
            # Información adicional
            info_text = (
                "Para usar cookies:\n"
                "1. Coloca un archivo `cookies.txt` en el directorio raíz del bot\n"
                "2. El archivo debe estar en formato Netscape/Mozilla\n"
                "3. Usa el comando `>>cookies enable` para activar el uso de cookies"
            )
            
            embed.add_field(name="ℹ️ Información", value=info_text, inline=False)
            
            # Consejos sobre cómo obtener cookies
            tips_text = (
                "Para extraer cookies de tu navegador:\n"
                "1. Instala una extensión como 'Get cookies.txt LOCALLY' (Chrome) o 'cookies.txt' (Firefox)\n"
                "2. Inicia sesión en YouTube en tu navegador\n"
                "3. Usa la extensión para exportar las cookies\n"
                "4. Guarda el archivo como `cookies.txt` en la carpeta del bot\n\n"
                "**⚠️ Advertencia:** Mantén tus cookies seguras, contienen información de tu sesión."
            )
            
            embed.add_field(name="📝 Obtener cookies", value=tips_text, inline=False)
            
            await ctx.send(embed=embed)
            
        elif action.lower() == "enable":
            # Verificar si existe el archivo de cookies
            if not os.path.exists(COOKIES_FILE):
                return await ctx.send("❌ No se encontró el archivo `cookies.txt`. Por favor, colócalo en el directorio raíz del bot.")
            
            # Activar cookies
            USE_COOKIES = True
            
            # Refrescar instancia de yt-dlp para aplicar los cambios
            refresh_ytdl_instance()
            
            await ctx.send("✅ Cookies habilitadas. Se utilizarán para las próximas reproducciones.")
            
        elif action.lower() == "disable":
            # Desactivar cookies
            USE_COOKIES = False
            
            # Refrescar instancia de yt-dlp para aplicar los cambios
            refresh_ytdl_instance()
            
            await ctx.send("🔒 Cookies deshabilitadas. Ya no se utilizarán para las reproducciones.")
            
        else:
            # Instrucciones si se proporciona un parámetro no válido
            await ctx.send("❓ Opción no válida. Usa `status`, `enable` o `disable`.")
            
    @commands.command(name="extract_cookies")
    @commands.has_permissions(administrator=True)
    async def extract_cookies(self, ctx, browser="chrome"):
        """Extrae cookies de un navegador instalado localmente
        
        Uso:
        >>extract_cookies chrome - Extrae cookies de Chrome
        >>extract_cookies firefox - Extrae cookies de Firefox
        >>extract_cookies edge - Extrae cookies de Edge
        
        Este comando extrae cookies directamente del navegador y las guarda en cookies.txt
        """
        browser = browser.lower()
        
        # Verificar que el navegador sea válido
        valid_browsers = ["chrome", "firefox", "edge", "safari", "opera"]
        if browser not in valid_browsers:
            return await ctx.send(f"❌ Navegador no válido. Opciones disponibles: {', '.join(valid_browsers)}")
        
        # Mensaje inicial
        message = await ctx.send(f"🔄 Extrayendo cookies de {browser}. Esto puede tomar un momento...")
        
        try:
            # Intenta instalar yt-dlp si no está instalado (necesario para extraer cookies)
            try:
                import yt_dlp
            except ImportError:
                await message.edit(content="yt-dlp no está instalado. Intentando instalarlo...")
                import subprocess
                import sys
                
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
                
                # Reimportar después de instalar
                import yt_dlp
                
            # Usar yt-dlp para extraer cookies del navegador
            import subprocess
            
            # Construir comando
            cmd = [
                sys.executable, "-m", "yt_dlp", 
                "--cookies-from-browser", browser,
                "--cookies", COOKIES_FILE,
                "-f", "bestaudio", 
                "--dump-user-agent",  # Solo para obtener user-agent, no descarga nada
                "--skip-download"
            ]
            
            # Ejecutar y capturar la salida
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            # Verificar si se creó el archivo de cookies
            if os.path.exists(COOKIES_FILE):
                # Activar cookies
                global USE_COOKIES
                USE_COOKIES = True
                
                # Refrescar instancia de yt-dlp para aplicar los cambios
                refresh_ytdl_instance()
                
                await message.edit(content=f"✅ Cookies extraídas exitosamente de {browser} y guardadas en `cookies.txt`.\n"
                                           f"📝 Se habilitó el uso de cookies automáticamente.")
            else:
                error_msg = stderr if stderr else "No se pudo extraer las cookies."
                await message.edit(content=f"❌ Error: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error extrayendo cookies: {e}")
            await message.edit(content=f"❌ Error al extraer cookies: {str(e)}")
            
            # Sugerencia en caso de error
            suggestion = (
                "\n💡 Sugerencia: Intenta extraer las cookies manualmente con una extensión del navegador "
                "como 'Get cookies.txt LOCALLY' y coloca el archivo en la carpeta del bot."
            )
            
            await ctx.send(suggestion)

    @staticmethod
    def format_duration(duration):
        """Formatea segundos en formato mm:ss o hh:mm:ss"""
        if not duration:
            return "??:??"
            
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        else:
            return f"{int(minutes):02d}:{int(seconds):02d}"

async def setup(bot):
    await bot.add_cog(Music(bot))
