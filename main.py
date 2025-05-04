# -*- coding: utf-8 -*-
import os
import traceback
import asyncio
import logging
import sys
import random
import json
import time
import aiohttp
import platform
from datetime import datetime, timedelta
import pytz  # We'll use pytz instead of UTC attribute
from collections import Counter

import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks

from utils import bot
from utils.bot import Bot, HelpCommand

# Configuración de logging para mejor depuración
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mikune.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MIKUNE 2")

load_dotenv()

# Lista de todos los módulos que se cargarán
EXTENSIONS = [
    'anime', 'error_handler', 'funny', 'general',
    'owner', 'reddit', 'rol', 'utils', 'ai', 'games',
    'moderation', 'music', 'tickets', 'polls', 'statistics', 'economy',
    # Módulos adicionales que serán agregados cuando se desarrollen:
    # 'notifications', 'welcome', 'weather', 
    # 'translator', 'automod', 'starboard'
]

# Eliminar 'economy' o 'economia' si estuvieran en la lista, para evitar cargar ambos
if 'economia' in EXTENSIONS:
    EXTENSIONS.remove('economia')

# Lista de flags de intents necesarios para funciones avanzadas
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.presences = True
intents.reactions = True
intents.emojis_and_stickers = True
intents.integrations = True
intents.typing = True
intents.invites = True
intents.webhooks = True

# Configuración del bot con opciones avanzadas
bot = Bot(
    case_insensitive=True,
    command_attrs=dict(hidden=False),
    allowed_mentions=discord.AllowedMentions(
        roles=False, users=True, everyone=False, replied_user=True
    ),
    intents=intents,
    activity=discord.Activity(
        type=discord.ActivityType.listening,
        name=f'{os.environ.get("PREFIX", ";;")}help | v2.0.0 🚀'
    ),
    help_command=HelpCommand(),
    description="MIKUNE 2 - El bot multifuncional avanzado para tu servidor de Discord",
    strip_after_prefix=True,
    max_messages=10000,  # Mantiene más mensajes en cache para mejor contexto
)

# Variables para estadísticas y rendimiento
bot.launch_time = datetime.now(pytz.UTC)
bot.command_stats = {}  # Para seguimiento de comandos usados
bot.total_commands_used = 0
bot.session = None  # Sesión aiohttp para peticiones HTTP


@bot.event
async def on_ready():
    """Evento que se dispara cuando el bot está listo."""
    logger.info(f'MIKUNE 2 conectado como {bot.user} (ID: {bot.user.id})')
    
    # Crear sesión HTTP global
    if bot.session is None:
        bot.session = aiohttp.ClientSession()
    
    # Mostrar estadísticas de inicio
    guilds = len(bot.guilds)
    users = sum(guild.member_count for guild in bot.guilds)
    channels = sum(len(guild.channels) for guild in bot.guilds)
    
    logger.info(f"Bot está en {guilds} servidores con acceso a {users} usuarios y {channels} canales")
    logger.info(f"Discord.py versión: {discord.__version__}")
    logger.info(f"Python versión: {platform.python_version()}")
    logger.info(f"Sistema: {platform.system()} {platform.release()} ({platform.architecture()[0]})")
    
    # Iniciar tareas en segundo plano
    update_status.start()
    check_reminders.start()
    
    # Cargar datos en caché
    try:
        # Economía
        economy_file = 'data/economy.json'
        if os.path.exists(economy_file):
            with open(economy_file, 'r', encoding='utf-8') as f:
                bot.economy_data = json.load(f)
                logger.info(f"Datos de economía cargados: {len(bot.economy_data)} usuarios")
        else:
            bot.economy_data = {}
            logger.info("No se encontraron datos de economía, se creará al usar comandos")
        
        # Interacciones
        interactions_file = 'data/interactions.json'
        if os.path.exists(interactions_file):
            with open(interactions_file, 'r', encoding='utf-8') as f:
                bot.interactions = json.load(f)
                logger.info(f"Datos de interacciones cargados")
        else:
            bot.interactions = {}
            logger.info("No se encontraron datos de interacciones, se creará al usar comandos")
        
        # Configuraciones por servidor
        bot.guild_configs = {}
        logger.info("Sistema de configuración por servidor iniciado")
    except Exception as e:
        logger.error(f"Error al cargar datos: {e}")
    
    await bot.tree.sync()  # Sincronizar comandos de barra diagonal
    
    # Banner de inicio
    logger.info("""
    ╔════════════════════════════════════════════════════════╗
    ║                                                        ║
    ║  █▀▄▀█ █ █▄▀ █ █ █▄ █ █▀▀   ▀█   █▀█ █▄ █ █   █ █▄ █  ║
    ║  █ ▀ █ █ █ █ █▄█ █ ▀█ ██▄   █▄   █▄█ █ ▀█ █▄▄ █ █ ▀█  ║
    ║                                                        ║
    ║           Bot multifuncional de Discord                ║
    ╚════════════════════════════════════════════════════════╝
    """)


@tasks.loop(minutes=30)
async def update_status():
    """Cambia el estado del bot periódicamente para mostrar información útil."""
    await bot.wait_until_ready()
    
    # Calcular tiempo de actividad
    uptime = datetime.now(pytz.UTC) - bot.launch_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m"
    
    statuses = [
        discord.Activity(type=discord.ActivityType.listening, name=f"{os.environ.get('PREFIX', ';;')}help | ¡Comando de ayuda!"),
        discord.Activity(type=discord.ActivityType.playing, name=f"en {len(bot.guilds)} servidores"),
        discord.Activity(type=discord.ActivityType.watching, name="anime con mis usuarios"),
        discord.Activity(type=discord.ActivityType.competing, name="ser el mejor bot"),
        discord.Game(name=f"Activo desde hace {uptime_str}"),
        discord.Activity(type=discord.ActivityType.streaming, name="música para ti", url="https://www.twitch.tv/mikune"),
        discord.Activity(type=discord.ActivityType.listening, name="tus comandos favoritos"),
        discord.Activity(type=discord.ActivityType.watching, name="memes de gatos"),
        discord.Activity(type=discord.ActivityType.playing, name=f"mencióname para ayudarte"),
        discord.Activity(type=discord.ActivityType.playing, name="con la IA más avanzada")
    ]
    
    # Use random choice instead of current_iteration
    current_status = random.choice(statuses)
    await bot.change_presence(activity=current_status)


@tasks.loop(minutes=1)
async def check_reminders():
    """Comprueba y envía recordatorios pendientes."""
    await bot.wait_until_ready()
    
    # Archivo de recordatorios (se creará si no existe)
    reminders_file = 'data/reminders.json'
    
    try:
        # Cargar recordatorios
        if os.path.exists(reminders_file):
            with open(reminders_file, 'r', encoding='utf-8') as f:
                reminders = json.load(f)
        else:
            reminders = []
            
        # Verificar recordatorios que deben enviarse
        current_time = datetime.now(pytz.UTC).timestamp()
        reminders_to_send = [r for r in reminders if r['time'] <= current_time]
        
        # Enviar recordatorios pendientes
        for reminder in reminders_to_send:
            try:
                # Intentar obtener usuario y canal
                user = await bot.fetch_user(reminder['user_id'])
                channel = bot.get_channel(reminder['channel_id'])
                
                if channel:
                    embed = discord.Embed(
                        title="⏰ Recordatorio",
                        description=reminder['message'],
                        color=discord.Color.blue(),
                        timestamp=datetime.utcfromtimestamp(reminder['created_at'])
                    )
                    embed.set_footer(text=f"Recordatorio establecido")
                    
                    await channel.send(f"{user.mention}", embed=embed)
                    logger.info(f"Recordatorio enviado a {user.name} (ID: {user.id})")
            except Exception as e:
                logger.error(f"Error al enviar recordatorio: {e}")
            
        # Eliminar recordatorios enviados
        if reminders_to_send:
            reminders = [r for r in reminders if r['time'] > current_time]
            with open(reminders_file, 'w', encoding='utf-8') as f:
                json.dump(reminders, f, indent=2)
                
    except Exception as e:
        logger.error(f"Error en check_reminders: {e}")


@bot.event
async def on_message(message):
    """Evento que se dispara con cada mensaje, permite reaccionar a ciertos textos."""
    # No responder a mensajes del bot
    if message.author.bot:
        return
        
    # Mensaje de mención directa al bot
    if message.content == f"<@{bot.user.id}>" or message.content == f"<@!{bot.user.id}>":
        prefix = os.environ.get("PREFIX", ";;")
        embed = discord.Embed(
            title="¡Hola! 👋",
            description=f"Mi prefijo es `{prefix}`. Usa `{prefix}help` para ver mis comandos.",
            color=0x7289da
        )
        
        # Agregar campos de información
        embed.add_field(
            name="💡 Comandos populares",
            value=f"`{prefix}anime` • `{prefix}economy` • `{prefix}games` • `{prefix}meme`",
            inline=False
        )
        
        embed.add_field(
            name="🤖 ¿Preguntas?",
            value=f"Usa `{prefix}pregunta` para interactuar con mi IA avanzada",
            inline=False
        )
        
        embed.set_footer(text="Desarrollado con 💖 | Versión 2.0.0")
        await message.reply(embed=embed)
        return
    
    # Respuestas personalizadas a frases específicas
    if message.content.lower() in ["hola mikune", "hello mikune", "hey mikune"]:
        greetings = [
            "¡Hola! ¿Cómo estás hoy?",
            "¡Hey! ¿En qué puedo ayudarte?",
            "¡Saludos! Estoy aquí para lo que necesites.",
            "¡Buenas! ¿Qué planes tienes hoy?",
            "¡Hola! Me alegra verte por aquí."
        ]
        await message.reply(random.choice(greetings))
        
    # Respuesta a palabras clave
    if "ayuda" in message.content.lower() and "mikune" in message.content.lower():
        prefix = os.environ.get("PREFIX", ";;")
        await message.channel.send(f"¿Necesitas ayuda? Usa `{prefix}help` para ver todos mis comandos.")
        
    # Continuar procesando comandos
    await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    """Se activa cuando el bot se une a un nuevo servidor."""
    logger.info(f"MIKUNE 2 se unió al servidor: {guild.name} (ID: {guild.id})")
    
    # Intentar enviar mensaje de bienvenida al canal general o primer canal de texto
    channel = None
    for ch in guild.text_channels:
        if ch.permissions_for(guild.me).send_messages:
            channel = ch
            break
    
    if channel:
        prefix = os.environ.get("PREFIX", ";;")
        
        embed = discord.Embed(
            title="¡Gracias por añadir a MIKUNE 2! 🎉",
            description=f"Soy un bot multifuncional que ofrece diversión, utilidades, juegos y mucho más.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 Primeros pasos",
            value=f"• Mi prefijo es `{prefix}`\n• Usa `{prefix}help` para ver todos mis comandos\n• Mencióname en cualquier momento para recordar mi prefijo",
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Configuración",
            value=f"Puedes personalizar mi comportamiento en tu servidor con `{prefix}config`",
            inline=False
        )
        
        embed.add_field(
            name="🔗 Enlaces útiles",
            value="[Servidor de soporte](https://discord.gg/invite) | [Invitación](https://discord.com/oauth2/authorize)",
            inline=False
        )
        
        embed.set_footer(text="Espero que disfrutes usando MIKUNE 2 en tu servidor.")
        
        try:
            await channel.send(embed=embed)
        except:
            logger.error(f"No se pudo enviar mensaje de bienvenida en {guild.name}")


@bot.event
async def on_command_error(ctx, error):
    """Manejo global de errores para comandos."""
    # Los errores serán manejados principalmente por el cog error_handler
    # Este es solo un respaldo
    if hasattr(ctx.command, 'on_error'):
        return
        
    if isinstance(error, commands.CommandNotFound):
        return  # Ignorar comandos no encontrados
        
    if isinstance(error, commands.CommandOnCooldown):
        remaining = int(error.retry_after)
        embed = discord.Embed(
            title="⏰ Comando en enfriamiento",
            description=f"Debes esperar **{remaining}s** antes de volver a usar este comando.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, delete_after=5)
        return
        
    # Registrar otros errores en el log
    logger.error(f"Error en comando {ctx.command}: {error}")


@bot.event
async def on_command_completion(ctx):
    """Registra estadísticas de uso de comandos."""
    bot.total_commands_used += 1
    command_name = ctx.command.qualified_name
    
    if command_name in bot.command_stats:
        bot.command_stats[command_name] += 1
    else:
        bot.command_stats[command_name] = 1
        
    # Crear un indicador de actividad aleatoriamente para simular "escribiendo"
    # Esto da la sensación de que el bot está más vivo
    if random.random() < 0.1:  # 10% de probabilidad
        async with ctx.channel.typing():
            await asyncio.sleep(random.uniform(0.5, 1.5))


async def load_extensions():
    """Carga todos los módulos (cogs) configurados."""
    try:
        # Try to import the extension handler
        from extension_handler import safe_load_extension
        
        # First, try to install missing dependencies if needed
        try:
            import importlib.metadata
            required_packages = [
                "animec", "beautifulsoup4", "asyncdagpi", 
                "google-search-python", "jishaku"
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    importlib.metadata.version(package)
                except importlib.metadata.PackageNotFoundError:
                    missing_packages.append(package)
            
            if missing_packages:
                logger.warning(f"Missing packages detected: {', '.join(missing_packages)}")
                logger.info("Attempting to install missing packages...")
                
                import subprocess
                import sys
                
                for package in missing_packages:
                    try:
                        logger.info(f"Installing {package}...")
                        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                        logger.info(f"Successfully installed {package}")
                    except Exception as e:
                        logger.error(f"Failed to install {package}: {e}")
        except Exception as e:
            logger.error(f"Error checking for missing packages: {e}")
        
        # Now load all extensions
        for cog in EXTENSIONS:
            try:
                await safe_load_extension(bot, cog)
            except Exception as e:
                logger.error(f'❌ Error loading module cogs.{cog}: {e}')
                logger.error(traceback.format_exc())
        
        # Load jishaku if available
        try:
            await bot.load_extension('jishaku')
            logger.info('✅ Módulo jishaku cargado exitosamente')
        except Exception as e:
            logger.warning(f'⚠️ Jishaku no disponible: {type(e).__name__}: {e}')
    except ImportError:
        # Fallback to the original implementation if extension_handler can't be imported
        for cog in EXTENSIONS:
            try:
                cog_path = f'cogs.{cog}'
                logger.info(f"Intentando cargar módulo: {cog_path}")
                
                try:
                    await bot.load_extension(cog_path)
                    logger.info(f'✅ Módulo cargado exitosamente: {cog_path}')
                except commands.ExtensionAlreadyLoaded:
                    await bot.reload_extension(cog_path)
                    logger.info(f'🔄 Módulo recargado: {cog_path}')
                
            except Exception as e:
                logger.error(f'❌ Error al cargar módulo {cog_path}: {type(e).__name__}: {e}')
                logger.error(traceback.format_exc())
        
        # Cargar extensiones adicionales
        try:
            await bot.load_extension('jishaku')
            logger.info('✅ Módulo jishaku cargado exitosamente')
        except Exception as e:
            logger.warning(f'⚠️ Jishaku no disponible: {type(e).__name__}: {e}')


async def cleanup():
    """Limpieza al cerrar el bot."""
    logger.info("Realizando limpieza antes de cerrar...")
    
    # Cerrar sesión HTTP
    if bot.session:
        await bot.session.close()
        logger.info("Sesión HTTP cerrada")
    
    # Guardar datos
    try:
        # Guardar economía
        if hasattr(bot, 'economy_data'):
            with open('data/economy.json', 'w', encoding='utf-8') as f:
                json.dump(bot.economy_data, f, indent=2)
            logger.info("Datos de economía guardados")
            
        # Guardar interacciones
        if hasattr(bot, 'interactions'):
            with open('data/interactions.json', 'w', encoding='utf-8') as f:
                json.dump(bot.interactions, f, indent=2)
            logger.info("Datos de interacciones guardados")
    except Exception as e:
        logger.error(f"Error al guardar datos: {e}")
    
    logger.info("Limpieza completada. ¡Hasta pronto!")


if __name__ == '__main__':
    # Verificar token
    token = os.environ.get('TOKEN')
    if not token:
        logger.error("ERROR: Variable de entorno TOKEN no encontrada.")
        logger.error("1. Verifica que exista un archivo .env con TOKEN=tu_token")
        logger.error("2. O establece la variable de entorno TOKEN en tu sistema")
        logger.error("Obtén tu token en: https://discord.com/developers/applications")
        exit(1)
    
    # Iniciar el bot
    async def main():
        try:
            async with bot:
                await load_extensions()
                await bot.start(token)
        except KeyboardInterrupt:
            logger.info("Cerrando por interrupción del usuario...")
        except Exception as e:
            logger.error(f"Error al iniciar el bot: {e}")
            logger.error(traceback.format_exc())
        finally:
            await cleanup()
    
    asyncio.run(main())
