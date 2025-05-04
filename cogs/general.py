import discord
import os
import platform
import time
import psutil
import datetime
import json
import random
import asyncio
import aiohttp
from discord.ext import commands, tasks

class General(commands.Cog):
    """📋 Comandos generales y utilidades básicas para MIKUNE 2"""

    def __init__(self, bot):
        self.bot = bot
        self.afk_users = {}
        self.afk_file_path = 'data/afk.json'
        self.afk_image_cache = {}  # Caché para imágenes AFK
        self.afk_notification_cooldowns = {}  # Anti-spam para notificaciones
        self._load_afk_data()
        self.cleanup_afk_data.start()  # Iniciar tarea de limpieza automática

    def _load_afk_data(self):
        """Carga los datos AFK desde el archivo JSON."""
        try:
            if os.path.exists(self.afk_file_path):
                with open(self.afk_file_path, 'r', encoding='utf-8') as f:
                    self.afk_users = json.load(f)
            else:
                self.afk_users = {}
                # Crear el directorio si no existe
                os.makedirs('data', exist_ok=True)
                self._save_afk_data()
        except Exception as e:
            print(f"Error cargando datos AFK: {e}")
            self.afk_users = {}

    def _save_afk_data(self):
        """Guarda los datos AFK en un archivo JSON."""
        try:
            with open(self.afk_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.afk_users, f, indent=2)
        except Exception as e:
            print(f"Error guardando datos AFK: {e}")

    def cog_unload(self):
        """Se llama cuando el cog se descarga."""
        self.cleanup_afk_data.cancel()
        self._save_afk_data()

    @tasks.loop(hours=24)
    async def cleanup_afk_data(self):
        """Tarea periódica que limpia estados AFK antiguos."""
        try:
            current_time = datetime.datetime.utcnow().timestamp()
            users_to_remove = []
            
            # Verificar estados AFK antiguos (más de 7 días)
            for user_id, afk_data in self.afk_users.items():
                # Si el estado AFK tiene más de 7 días, marcarlo para eliminar
                if current_time - afk_data.get('timestamp', 0) > 7 * 24 * 60 * 60:  # 7 días en segundos
                    users_to_remove.append(user_id)
            
            # Eliminar los estados AFK antiguos
            for user_id in users_to_remove:
                del self.afk_users[user_id]
            
            # Si se eliminaron usuarios, guardar los cambios
            if users_to_remove:
                self._save_afk_data()
                print(f"Limpieza automática: {len(users_to_remove)} estados AFK antiguos eliminados")
        except Exception as e:
            print(f"Error durante la limpieza automática: {e}")

    @cleanup_afk_data.before_loop
    async def before_cleanup(self):
        """Espera a que el bot esté listo antes de iniciar la tarea."""
        await self.bot.wait_until_ready()

    async def _get_anime_sleep_image(self, theme=None):
        """Obtiene una imagen de anime aleatoria relacionada con sueño/AFK.
        
        Args:
            theme (str, optional): El tema para buscar imágenes específicas.
        """
        # Usar caché si es posible para evitar muchas solicitudes
        if self.afk_image_cache and random.random() < 0.6 and not theme:  # 60% probabilidad usar caché si no es tema específico
            return random.choice(list(self.afk_image_cache.values()))
        
        # Términos de búsqueda según el tema seleccionado
        search_terms = ["anime sleeping", "anime afk", "anime nap", "anime tired"]
        
        # Si hay un tema específico, usar sus términos de búsqueda
        if theme:
            try:
                themes = await self._generate_afk_themes()
                if theme in themes and "search_terms" in themes[theme]:
                    search_terms = themes[theme]["search_terms"]
            except Exception as e:
                print(f"Error obteniendo términos de búsqueda para tema {theme}: {e}")
        
        # Intentar obtener un GIF de Tenor primero (prioridad)
        try:
            if hasattr(self.bot, 'session') and self.bot.session:
                search_term = random.choice(search_terms)
                
                # API de Tenor - Búsqueda aleatoria con límite aumentado para más opciones
                tenor_url = f"https://tenor.googleapis.com/v2/search?q={search_term}&key=AIzaSyAQmmT4ceTK_xesoEG1PRfWx7xHnT7k2IE&limit=20&media_filter=gif"
                
                async with self.bot.session.get(tenor_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'results' in data and data['results']:
                            # Seleccionar un GIF aleatorio de los resultados
                            results = data['results']
                            random.shuffle(results)  # Mezclar resultados para más variedad
                            
                            for gif in results[:10]:  # Intentar con los primeros 10
                                if 'media_formats' in gif:
                                    # Usar preferentemente 'tinygif' por ser más ligero, o 'gif' como respaldo
                                    if 'tinygif' in gif['media_formats']:
                                        image_url = gif['media_formats']['tinygif']['url']
                                    elif 'gif' in gif['media_formats']:
                                        image_url = gif['media_formats']['gif']['url']
                                    else:
                                        continue
                                        
                                    # Añadir a la caché
                                    if len(self.afk_image_cache) > 30:  # Aumentar tamaño caché
                                        self.afk_image_cache.pop(next(iter(self.afk_image_cache)))
                                    cache_key = f"tenor_{theme or 'default'}_{len(self.afk_image_cache)}"
                                    self.afk_image_cache[cache_key] = image_url
                                    return image_url
        except Exception as e:
            print(f"Error obteniendo GIF de Tenor: {e}")
        
        # Intentar con otra fuente - GIPHY como alternativa
        try:
            if hasattr(self.bot, 'session') and self.bot.session and random.random() < 0.3:
                giphy_api_key = "pX2FnH7mJgpYNLnMBUEPvwd3xJVzKdst"  # Clave gratuita para pruebas
                giphy_search = search_terms[0].replace(" ", "+")
                giphy_url = f"https://api.giphy.com/v1/gifs/search?api_key={giphy_api_key}&q={giphy_search}&limit=10&rating=g"
                
                async with self.bot.session.get(giphy_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'data' in data and data['data']:
                            gif_data = random.choice(data['data'])
                            image_url = gif_data['images']['original']['url']
                            
                            # Añadir a la caché
                            cache_key = f"giphy_{theme or 'default'}_{len(self.afk_image_cache)}"
                            self.afk_image_cache[cache_key] = image_url
                            return image_url
        except Exception as e:
            print(f"Error con API alternativa: {e}")
        
        # Lista de GIFs anime de alta calidad con temática AFK/sleeping
        anime_sleep_images = [
            # GIFs de anime durmiendo de alta calidad
            "https://i.imgur.com/KWVMYoA.gif",  # Anime sleeping
            "https://i.imgur.com/L4cRU7A.gif",  # Cute sleeping
            "https://i.imgur.com/OZfA4WJ.gif",  # Cute anime sleeping
            "https://i.imgur.com/u9LFkbG.gif",  # Anime girl sleeping
            "https://i.imgur.com/TwrHOQR.gif",  # Cozy anime sleep
            "https://i.imgur.com/s90l00M.gif",  # Dreaming anime
            "https://i.imgur.com/YdmZz9t.gif",  # Sleepy anime girl
            "https://i.imgur.com/5KbLONe.gif",  # Anime nap
            "https://i.imgur.com/5lUspQH.gif",  # Peaceful anime sleep
            # GIFs de anime cansado/ausente
            "https://i.imgur.com/3EJbtFy.gif",  # Tired anime
            "https://i.imgur.com/UkEtLGr.gif",  # Exhausted anime
            "https://i.imgur.com/SOHZrTg.gif",  # AFK anime girl
            "https://i.imgur.com/r7R3rcO.gif",  # Anime resting
            "https://i.imgur.com/tCSXg9W.gif",  # Anime head on desk
            "https://i.imgur.com/GIq5EJb.gif",   # Anime yawning
            # GIFs adicionales de anime durmiendo (alta calidad)
            "https://i.imgur.com/lQUwjKA.gif",   # Sleepy anime in bed
            "https://i.imgur.com/26VIfw6.gif",   # Cute anime sleeping
            "https://i.imgur.com/0YkCMrj.gif",   # Anime girl falling asleep
            "https://i.imgur.com/XOvhOEs.gif",   # Anime napping at desk
            "https://i.imgur.com/K81pj2t.gif",    # Anime tucked in bed
            # Nueva colección ampliada
            "https://i.imgur.com/CXry04r.gif",   # Anime girl sleeping peacefully
            "https://i.imgur.com/N10wSIU.gif",   # Anime sleep at table
            "https://i.imgur.com/hNK4AuP.gif",   # Anime yawning cute
            "https://i.imgur.com/R31SHRu.gif",   # Anime sleep with pillow
            "https://i.imgur.com/FXHknA5.gif"    # Anime dozing off
        ]
        
        # Intentar obtener nuevas imágenes de anime con API alternativa
        try:
            if hasattr(self.bot, 'session') and self.bot.session and random.random() < 0.4:  # 40% de probabilidad
                apis = [
                    'https://api.waifu.pics/sfw/sleep',
                    'https://api.waifu.im/search/?included_tags=sleeping'
                ]
                
                async with self.bot.session.get(random.choice(apis)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'url' in data and data['url'].endswith(('.jpg', '.png', '.gif', '.jpeg')):
                            image_url = data['url']
                            # Añadir a la caché
                            cache_key = f"api_{theme or 'default'}_{len(self.afk_image_cache)}"
                            self.afk_image_cache[cache_key] = image_url
                            return image_url
                        elif 'images' in data and data['images'] and len(data['images']) > 0:
                            # Para api.waifu.im
                            image_url = data['images'][0].get('url')
                            if image_url:
                                cache_key = f"waifuim_{theme or 'default'}_{len(self.afk_image_cache)}"
                                self.afk_image_cache[cache_key] = image_url
                                return image_url
        except Exception as e:
            print(f"Error obteniendo imagen anime de API alternativa: {e}")
            
        # Si no se pudo obtener una nueva, usar la lista predefinida
        selected_image = random.choice(anime_sleep_images)
        
        # Actualizar caché
        if len(self.afk_image_cache) > 30:  # Aumentar tamaño caché
            self.afk_image_cache.pop(next(iter(self.afk_image_cache)))
        cache_key = f"local_{selected_image[-10:]}"
        self.afk_image_cache[cache_key] = selected_image
            
        return selected_image

    async def _get_return_image(self):
        """Obtiene una imagen de anime relacionada con regresar/despertar."""
        # Intentar obtener un GIF de Tenor primero (prioridad)
        try:
            if self.bot.session:
                tenor_search_terms = ["anime waking up", "anime welcome back", "anime return", "anime wave", "anime hello"]
                search_term = random.choice(tenor_search_terms)
                
                # API de Tenor - Búsqueda aleatoria
                async with self.bot.session.get(
                    f"https://tenor.googleapis.com/v2/search?q={search_term}&key=AIzaSyAQmmT4ceTK_xesoEG1PRfWx7xHnT7k2IE&limit=15&media_filter=gif"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'results' in data and data['results']:
                            # Seleccionar un GIF aleatorio de los resultados
                            gif = random.choice(data['results'])
                            if 'media_formats' in gif and 'gif' in gif['media_formats']:
                                return gif['media_formats']['gif']['url']
        except Exception as e:
            print(f"Error obteniendo GIF de Tenor para regreso: {e}")
        
        # Lista de GIFs anime de alta calidad para regresar/despertar
        return_images = [
            "https://i.imgur.com/bFQmQXy.gif",  # Anime waking up
            "https://i.imgur.com/9TpbSWT.gif",  # Anime stretching
            "https://i.imgur.com/YWQAaG5.gif",  # Anime yawn and wake up
            "https://i.imgur.com/5Jz7xZl.gif",  # Anime refreshed
            "https://i.imgur.com/lWDnqKU.gif",  # Anime back online
            "https://i.imgur.com/dljt2Pw.gif",  # Anime returning
            "https://i.imgur.com/hqNHlGq.gif",  # Anime hello again
            # GIFs adicionales para retorno
            "https://i.imgur.com/tUVZB2K.gif",  # Anime welcome back
            "https://i.imgur.com/lH8Bkh2.gif",  # Anime waving
            "https://i.imgur.com/IySD2U5.gif",  # Anime hello
            "https://i.imgur.com/ElmsBNr.gif",  # Anime greeting
            "https://i.imgur.com/NYMcVBK.gif"   # Anime cheerful return
        ]
        
        # Intentar obtener nuevas imágenes de API alternativa
        try:
            if self.bot.session and random.random() < 0.3:  # 30% de probabilidad
                # Probar con waifu.pics para variedad
                apis = [
                    'https://api.waifu.pics/sfw/wave',
                    'https://api.waifu.pics/sfw/smile',
                    'https://api.waifu.pics/sfw/happy'
                ]
                
                async with self.bot.session.get(random.choice(apis)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'url' in data and data['url'].endswith(('.jpg', '.png', '.gif', '.jpeg')):
                            return data['url']
        except Exception as e:
            print(f"Error obteniendo imagen de regreso alternativa: {e}")
            
        return random.choice(return_images)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Evento para detectar menciones a usuarios AFK y usuarios AFK que vuelven."""
        if message.author.bot:
            return

        # Convertir a string para compatibilidad con claves del diccionario
        author_id = str(message.author.id)

        # Verificar si el autor del mensaje estaba AFK
        if author_id in self.afk_users:
            # Verificar si es un comando afk (para evitar desactivación al usar comandos afk)
            if message.content.startswith(f"{self.bot.command_prefix}afk"):
                return
                
            # Usuario ha vuelto
            afk_data = self.afk_users.pop(author_id)
            self._save_afk_data()

            # Calcular tiempo AFK
            afk_time = datetime.datetime.utcnow().timestamp() - afk_data['timestamp']
            time_formatted = self._format_time_difference(afk_time)

            # Restaurar nickname si fue cambiado
            try:
                if (message.guild and message.guild.me.guild_permissions.manage_nicknames and 
                    message.author.top_role < message.guild.me.top_role):
                    if message.author.display_name.startswith("[AFK]"):
                        # Usar el nombre original si está guardado, o quitar el prefijo AFK
                        original_name = afk_data.get('original_name', message.author.display_name[6:])
                        await message.author.edit(nick=original_name)
            except Exception as e:
                print(f"Error al restaurar nickname: {e}")

            # Crear embed de bienvenida
            welcome_back = discord.Embed(
                title="👋 ¡Bienvenido de vuelta!",
                description=f"Tu estado AFK ha sido eliminado. Estuviste ausente durante **{time_formatted}**.",
                color=discord.Color.green()
            )
            
            # Estadísticas sobre el periodo AFK
            if 'mentions_received' in afk_data:
                mentions = afk_data['mentions_received']
                if mentions > 0:
                    plural = "s" if mentions > 1 else ""
                    welcome_back.add_field(
                        name="📨 Menciones recibidas",
                        value=f"Recibiste **{mentions}** mención{plural} mientras estabas ausente.",
                        inline=False
                    )
            
            welcome_back.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            welcome_back.set_footer(text="Puedes volver a activar tu estado AFK usando el comando afk")
            
            # Añadir imagen de bienvenida
            return_image = await self._get_return_image()
            welcome_back.set_image(url=return_image)  # Cambiar a set_image en lugar de set_thumbnail

            try:
                # Enviar como mensaje efímero con botón para volver a AFK si es posible
                view = None
                if hasattr(discord, "ui") and hasattr(discord.ui, "View"):
                    class QuickAFKView(discord.ui.View):
                        def __init__(self, afk_command, reason):
                            super().__init__(timeout=60)
                            self.afk_command = afk_command
                            self.reason = reason
                            
                        @discord.ui.button(label="Volver a AFK", style=discord.ButtonStyle.gray, emoji="💤")
                        async def afk_again_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                            # Verificar que quien presiona es el dueño del mensaje
                            if interaction.user.id != message.author.id:
                                await interaction.response.send_message("Este botón no es para ti.", ephemeral=True)
                                return
                                
                            # Usar el bot desde la interacción en lugar de desde el comando
                            ctx = await interaction.client.get_context(message)
                            await self.afk_command(ctx, reason=self.reason)
                            # Deshabilitar el botón
                            button.disabled = True
                            button.label = "AFK Reactivado"
                            await interaction.response.edit_message(view=self)
                            
                    # Crear vista con botón para volver a AFK rápidamente
                    reason = afk_data.get('reason', "Ausente")
                    view = QuickAFKView(self.afk_set, reason)
                
                # Enviar mensaje de bienvenida
                await message.channel.send(embed=welcome_back, view=view, delete_after=45)  # Aumentar tiempo
            except Exception as e:
                print(f"Error al enviar mensaje de bienvenida: {e}")

        # Verificar si se menciona a algún usuario AFK
        if message.mentions:
            afk_mentions = []
            now = datetime.datetime.utcnow().timestamp()
            
            for mentioned in message.mentions:
                mentioned_id = str(mentioned.id)
                
                # Comprobar si el usuario está AFK y no es el autor
                if mentioned_id in self.afk_users and mentioned_id != author_id:
                    # Verificar cooldown para evitar spam (máximo 1 notificación cada 60 segundos para el mismo usuario)
                    cooldown_key = f"{author_id}_{mentioned_id}"
                    last_notification = self.afk_notification_cooldowns.get(cooldown_key, 0)
                    
                    if now - last_notification < 60:  # 60 segundos de cooldown
                        continue  # Omitir esta mención (todavía en cooldown)
                    
                    # Actualizar cooldown
                    self.afk_notification_cooldowns[cooldown_key] = now
                    
                    # Obtener datos del usuario AFK
                    afk_data = self.afk_users[mentioned_id]
                    reason = afk_data.get('reason', 'No se especificó razón')
                    
                    # Incrementar contador de menciones
                    if 'mentions_received' not in afk_data:
                        afk_data['mentions_received'] = 0
                    afk_data['mentions_received'] += 1
                    
                    # Registrar quién mencionó para estadísticas
                    if 'mentioned_by' not in afk_data:
                        afk_data['mentioned_by'] = []
                    afk_data['mentioned_by'].append({
                        'user_id': author_id,
                        'username': message.author.display_name,
                        'timestamp': now,
                        'message': message.content[:100]  # Almacenar una parte del mensaje
                    })
                    
                    # Guardar cambios
                    self._save_afk_data()
                    
                    # Calcular tiempo transcurrido
                    afk_time = now - afk_data['timestamp']
                    time_formatted = self._format_time_difference(afk_time)
                    
                    # Añadir a la lista de menciones para mostrar
                    afk_mentions.append({
                        'user': mentioned,
                        'reason': reason,
                        'time': time_formatted,
                        'image': afk_data.get('image_url', None)
                    })
            
            # Si hay menciones AFK, crear un embed
            if afk_mentions:
                embed = discord.Embed(
                    title="💤 Usuario(s) AFK Mencionado(s)",
                    description="Los siguientes usuarios están temporalmente ausentes:",
                    color=discord.Color.purple()
                )
                
                # Añadir campo para cada usuario AFK mencionado
                for mention in afk_mentions:
                    embed.add_field(
                        name=f"{mention['user'].display_name}",
                        value=f"**Razón:** {mention['reason']}\n**Ausente desde hace:** {mention['time']}",
                        inline=False
                    )
                
                # Si solo hay una mención, usar su imagen
                if len(afk_mentions) == 1 and afk_mentions[0]['image']:
                    embed.set_image(url=afk_mentions[0]['image'])  # Cambiar a set_image
                else:
                    # De lo contrario, usar una imagen genérica AFK
                    embed.set_image(url=await self._get_anime_sleep_image())  # Cambiar a set_image
                
                embed.set_footer(text="Los usuarios serán notificados de tus menciones cuando regresen")
                
                try:
                    await message.reply(embed=embed)
                except:
                    await message.channel.send(embed=embed)

    def _format_time_difference(self, seconds):
        """Formatea la diferencia de tiempo en un formato legible y detallado."""
        if seconds < 60:
            return f"{int(seconds)} segundos"
        
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        parts = []
        if days > 0:
            parts.append(f"{days} día{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hora{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minuto{'s' if minutes != 1 else ''}")
        if seconds > 0 and len(parts) < 2:  # Solo incluir segundos si no tenemos ya 2 unidades
            parts.append(f"{seconds} segundo{'s' if seconds != 1 else ''}")
        
        # Unir las partes con comas y "y"
        if len(parts) > 1:
            return f"{', '.join(parts[:-1])} y {parts[-1]}"
        else:
            return parts[0]

    async def _generate_afk_themes(self):
        """Genera una lista de temas disponibles para el modo AFK."""
        return {
            "anime": {
                "name": "Anime",
                "description": "Temática de anime clásica",
                "color": discord.Color.purple(),
                "emoji": "🌸",
                "search_terms": ["anime sleeping", "anime nap", "anime tired", "kawaii sleep"]
            },
            "gaming": {
                "name": "Gaming",
                "description": "Para gamers que toman un descanso",
                "color": discord.Color.green(),
                "emoji": "🎮",
                "search_terms": ["gaming break", "gamer sleeping", "sleepy gamer", "tired gamer"]
            },
            "working": {
                "name": "Trabajando",
                "description": "Indica que estás ocupado con trabajo",
                "color": discord.Color.orange(),
                "emoji": "💼",
                "search_terms": ["busy working", "work break", "office nap", "anime working"]
            },
            "sleeping": {
                "name": "Durmiendo",
                "description": "Para cuando te vas a dormir",
                "color": discord.Color.dark_blue(),
                "emoji": "😴",
                "search_terms": ["anime sleep", "sleeping anime girl", "anime dreaming", "anime zzz"]
            },
            "studying": {
                "name": "Estudiando",
                "description": "Indica que estás concentrado estudiando",
                "color": discord.Color.teal(),
                "emoji": "📚",
                "search_terms": ["anime studying", "study break", "tired student anime", "anime school sleep"]
            },
            "movie": {
                "name": "Viendo Película",
                "description": "Para cuando estás viendo una película",
                "color": discord.Color.red(),
                "emoji": "🎬",
                "search_terms": ["anime watching movie", "anime cinema", "anime watching tv", "anime popcorn"]
            },
            "vacation": {
                "name": "Vacaciones",
                "description": "Avisa que estás de vacaciones",
                "color": discord.Color.gold(),
                "emoji": "🏖️",
                "search_terms": ["anime vacation", "anime beach", "anime relax", "anime holiday"]
            },
            "eating": {
                "name": "Comiendo",
                "description": "Para cuando estás en una comida",
                "color": discord.Color.orange(),
                "emoji": "🍜",
                "search_terms": ["anime eating", "anime food", "anime lunch", "anime dinner"]
            },
            "crying": {
                "name": "Llorando",
                "description": "Para momentos tristes",
                "color": discord.Color.blue(),
                "emoji": "😢",
                "search_terms": ["anime crying", "anime sad", "anime tears", "anime emotional"]
            },
            "rage": {
                "name": "Rage Mode",
                "description": "Cuando necesitas un tiempo para calmarte",
                "color": discord.Color.red(),
                "emoji": "💢",
                "search_terms": ["anime rage", "anime angry", "anime mad", "anime fury"]
            },
            "travel": {
                "name": "Viajando",
                "description": "Indica que estás en movimiento",
                "color": discord.Color.blue(),
                "emoji": "✈️",
                "search_terms": ["anime travel", "anime journey", "anime boarding", "anime train"]
            },
            "date": {
                "name": "Cita",
                "description": "Cuando tienes una cita romántica",
                "color": discord.Color.magenta(),
                "emoji": "❤️",
                "search_terms": ["anime date", "anime romantic", "anime couple", "anime love"]
            }
        }

    @commands.group(name="afk", help="Sistema avanzado de ausencia")
    async def afk_group(self, ctx):
        """Grupo de comandos para el sistema AFK mejorado"""
        if ctx.invoked_subcommand is None:
            # Si no se especifica subcomando, activar el AFK básico
            reason = ctx.message.content[len(ctx.prefix + ctx.command.name):].strip()
            await self.afk_set(ctx, reason=reason if reason else None)

    @afk_group.command(name="set", help="Establece tu estado como ausente con opciones avanzadas")
    async def afk_set(self, ctx, *, reason=None):
        """Establece tu estado como AFK con un mensaje personalizado y tema."""
        author_id = str(ctx.author.id)
        current_time = datetime.datetime.utcnow().timestamp()
        
        if not reason:
            reason = "Ausente (No se especificó razón)"
            
        # Detectar posible tema en el mensaje
        lower_reason = reason.lower()
        theme = "anime"  # Tema por defecto
        theme_emoji = "🌸"
        theme_color = discord.Color.purple()
        
        # Obtener todos los temas disponibles
        themes = await self._generate_afk_themes()
        
        # Buscar palabras clave para detectar el tema automáticamente
        theme_keywords = {
            "gaming": ["juego", "gaming", "jugando", "gamer", "game", "ps4", "ps5", "xbox", "switch", "lol"],
            "working": ["trabajo", "trabajando", "reunión", "meeting", "ocupado", "busy", "currando"],
            "sleeping": ["durmiendo", "dormido", "sueño", "dormir", "cansado", "cama", "siesta", "acostado"],
            "studying": ["estudiando", "estudiar", "examen", "universidad", "escuela", "tarea", "deberes"],
            "movie": ["película", "serie", "viendo", "netflix", "watching", "cinema", "cine", "tv", "anime"],
            "vacation": ["vacaciones", "playa", "descanso", "descansar", "vacation", "holiday", "viaje"],
            "eating": ["comiendo", "comer", "almuerzo", "comida", "cena", "desayuno", "eating", "lunch"],
            "crying": ["llorando", "triste", "sad", "depre", "depresión", "crying", "lágrimas"],
            "rage": ["rage", "enojado", "enfadado", "molesto", "rabia", "ira", "furioso", "angry"],
            "travel": ["viajando", "viaje", "traveling", "journey", "tren", "avión", "airport"],
            "date": ["cita", "date", "pareja", "novio", "novia", "romantico", "romance", "love", "amor"]
        }
        
        # Detectar tema basado en palabras clave
        detected_theme = None
        for theme_id, keywords in theme_keywords.items():
            if any(keyword in lower_reason for keyword in keywords):
                detected_theme = theme_id
                break
                
        # Si se detectó un tema, usarlo
        if detected_theme and detected_theme in themes:
            theme = detected_theme
            theme_emoji = themes[theme]["emoji"]
            theme_color = themes[theme]["color"]
            
        # Obtener una imagen temática específica para el tema detectado
        image_url = await self._get_anime_sleep_image(theme)
        
        # Guardar datos del usuario
        self.afk_users[author_id] = {
            'timestamp': current_time,
            'reason': reason,
            'guild_id': str(ctx.guild.id),
            'channel_id': str(ctx.channel.id),
            'username': ctx.author.display_name,
            'theme': theme,
            'theme_emoji': theme_emoji,
            'image_url': image_url,
            'mentions_received': 0,
            'mentioned_by': []
        }
        
        # Cambiar nickname si es posible (añadiendo prefijo AFK)
        try:
            if ctx.guild.me.guild_permissions.manage_nicknames and ctx.author.top_role < ctx.guild.me.top_role:
                current_name = ctx.author.display_name
                new_name = f"[AFK] {current_name}"
                
                # Solo cambiar si no excede el límite y no tiene ya el prefijo
                if len(new_name) <= 32 and not current_name.startswith("[AFK]"):
                    await ctx.author.edit(nick=new_name)
                    # Guardar nombre original para restaurarlo después
                    self.afk_users[author_id]['original_name'] = current_name
        except Exception as e:
            print(f"Error al cambiar nickname: {e}")
        
        # Guardar datos
        self._save_afk_data()
        
        # Crear y enviar un embed con confirmación
        afk_embed = discord.Embed(
            title=f"{theme_emoji} Estado AFK Activado",
            description=f"{ctx.author.mention} está ahora ausente. Los usuarios que te mencionen recibirán una notificación.",
            color=theme_color
        )
        
        # Información sobre el tema detectado
        if detected_theme:
            theme_name = themes[theme]["name"]
            afk_embed.add_field(
                name="🎨 Tema detectado",
                value=f"Se ha activado automáticamente el tema **{theme_name}** basado en tu mensaje.",
                inline=False
            )
        
        afk_embed.add_field(
            name=f"📝 Mensaje de ausencia",
            value=reason,
            inline=False
        )
        
        # Añadir campos informativos
        afk_embed.add_field(
            name="🔄 Desactivación automática",
            value="Tu estado AFK se desactivará cuando envíes un mensaje.",
            inline=True
        )
        
        afk_embed.add_field(
            name="📝 Comandos útiles",
            value=f"`{ctx.prefix}afk remove` - Desactivar manualmente\n`{ctx.prefix}afk status` - Ver usuarios AFK\n`{ctx.prefix}afk theme` - Cambiar tema",
            inline=True
        )
        
        afk_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        afk_embed.set_footer(text=f"AFK desde: {datetime.datetime.utcnow().strftime('%d/%m/%Y • %H:%M:%S')}")
        
        # Añadir imagen temática
        afk_embed.set_image(url=image_url)
        
        # Enviar mensaje de confirmación con botones si están disponibles
        try:
            view = None
            if hasattr(discord, "ui") and hasattr(discord.ui, "View"):
                class AFKControlsView(discord.ui.View):
                    def __init__(self, cog, ctx):
                        super().__init__(timeout=60)
                        self.cog = cog
                        self.ctx = ctx
                        
                    @discord.ui.button(label="Cambiar Tema", style=discord.ButtonStyle.primary, emoji="🎨")
                    async def change_theme_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                        if interaction.user.id != self.ctx.author.id:
                            await interaction.response.send_message("Este botón no es para ti.", ephemeral=True)
                            return
                            
                        # Mostrar temas disponibles
                        await interaction.response.defer()
                        await self.cog.afk_theme(self.ctx)
                        
                    @discord.ui.button(label="Desactivar AFK", style=discord.ButtonStyle.danger, emoji="✖️")
                    async def remove_afk_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                        if interaction.user.id != self.ctx.author.id:
                            await interaction.response.send_message("Este botón no es para ti.", ephemeral=True)
                            return
                            
                        # Desactivar AFK
                        await interaction.response.defer()
                        await self.cog.afk_remove(self.ctx)
                        
                view = AFKControlsView(self, ctx)
                
            await ctx.send(embed=afk_embed, view=view)
        except Exception as e:
            print(f"Error al enviar mensaje con botones: {e}")
            # Fallback sin botones
            await ctx.send(embed=afk_embed)

    @afk_group.command(name="theme", aliases=["tema"], help="Cambia el tema de tu estado AFK")
    async def afk_theme(self, ctx, theme=None):
        """Establece un tema para tu estado AFK."""
        author_id = str(ctx.author.id)
        
        # Verificar si el usuario está AFK
        if author_id not in self.afk_users:
            # Si no está AFK, primero establecer el estado
            await ctx.send("No estás en modo AFK. Primero debes activar tu estado AFK con `afk set`.")
            return
        
        # Obtener lista de temas disponibles
        themes = await self._generate_afk_themes()
        
        # Si no se especificó tema o es inválido, mostrar opciones disponibles
        if not theme or theme.lower() not in themes:
            embed = discord.Embed(
                title="🎨 Temas AFK Disponibles",
                description="Selecciona un tema para personalizar tu estado AFK:",
                color=discord.Color.blue()
            )
            
            for theme_id, theme_data in themes.items():
                embed.add_field(
                    name=f"{theme_data['emoji']} {theme_data['name']}",
                    value=f"{theme_data['description']}\nUsa `{ctx.prefix}afk theme {theme_id}`",
                    inline=True
                )
                
            embed.set_footer(text="El tema afecta a cómo se muestran las notificaciones de tu ausencia")
            await ctx.send(embed=embed)
            return
        
        # Aplicar el tema seleccionado
        selected_theme = theme.lower()
        if selected_theme in themes:
            # Actualizar tema y emoji
            self.afk_users[author_id]['theme'] = selected_theme
            self.afk_users[author_id]['theme_emoji'] = themes[selected_theme]['emoji']
            
            # Obtener nueva imagen según el tema
            self.afk_users[author_id]['image_url'] = await self._get_anime_sleep_image()
            
            # Guardar cambios
            self._save_afk_data()
            
            # Confirmar cambio
            embed = discord.Embed(
                title=f"{themes[selected_theme]['emoji']} Tema AFK Actualizado",
                description=f"Has seleccionado el tema **{themes[selected_theme]['name']}** para tu estado AFK.",
                color=themes[selected_theme]['color']
            )
            
            embed.set_footer(text="Los usuarios que te mencionen verán este tema en la notificación")
            embed.set_thumbnail(url=self.afk_users[author_id]['image_url'])
            
            await ctx.send(embed=embed)

    @afk_group.command(name="remove", aliases=["unafk"], help="Elimina tu estado AFK")
    async def afk_remove(self, ctx):
        """Elimina manualmente tu estado AFK."""
        author_id = str(ctx.author.id)
        
        if author_id not in self.afk_users:
            await ctx.send("No estás en modo AFK actualmente.", delete_after=5)
            return
        
        # Obtener datos antes de eliminarlos
        afk_data = self.afk_users.pop(author_id)
        self._save_afk_data()
        
        # Restaurar nickname si fue cambiado
        try:
            if ctx.guild.me.guild_permissions.manage_nicknames and ctx.author.top_role < ctx.guild.me.top_role:
                if ctx.author.display_name.startswith("[AFK]"):
                    # Usar el nombre original si está guardado, o quitar el prefijo AFK
                    original_name = afk_data.get('original_name', ctx.author.display_name[6:])
                    await ctx.author.edit(nick=original_name)
        except Exception as e:
            print(f"Error al restaurar nickname: {e}")
        
        # Calcular tiempo AFK
        afk_time = datetime.datetime.utcnow().timestamp() - afk_data['timestamp']
        time_formatted = self._format_time_difference(afk_time)
        
        # Crear un embed para informar de la desactivación
        embed = discord.Embed(
            title="✅ Estado AFK Desactivado",
            description=f"Has desactivado manualmente tu estado AFK. Estuviste ausente durante **{time_formatted}**.",
            color=discord.Color.green()
        )
        
        # Estadísticas sobre el periodo AFK
        if 'mentions_received' in afk_data:
            mentions = afk_data['mentions_received']
            if mentions > 0:
                plural = "s" if mentions > 1 else ""
                embed.add_field(
                    name="📨 Menciones recibidas",
                    value=f"Recibiste **{mentions}** mención{plural} mientras estabas ausente.",
                    inline=False
                )
                
                # Mostrar las últimas menciones (máximo 3)
                if 'mentioned_by' in afk_data and afk_data['mentioned_by']:
                    recent_mentions = afk_data['mentioned_by'][-3:]  # Últimas 3 menciones
                    mention_list = []
                    
                    for i, mention in enumerate(reversed(recent_mentions), 1):
                        username = mention.get('username', 'Usuario')
                        message = mention.get('message', '').replace('`', '')
                        mention_time = datetime.datetime.fromtimestamp(mention.get('timestamp', 0))
                        time_str = mention_time.strftime('%H:%M:%S')
                        
                        mention_list.append(f"**{i}.** {username} a las {time_str}\n> {message}")
                    
                    if mention_list:
                        embed.add_field(
                            name="🔍 Últimas menciones",
                            value="\n".join(mention_list),
                            inline=False
                        )
        
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"AFK desactivado a las {datetime.datetime.utcnow().strftime('%H:%M:%S')}")
        
        # Añadir imagen de "regreso"
        embed.set_thumbnail(url=await self._get_return_image())
        
        await ctx.send(embed=embed)

    @afk_group.command(name="status", help="Muestra información sobre usuarios AFK")
    async def afk_status(self, ctx, *, member: discord.Member = None):
        """Muestra información sobre los usuarios AFK en el servidor o un usuario específico."""
        if member:
            # Comprobar si el miembro está AFK
            member_id = str(member.id)
            if member_id in self.afk_users:
                afk_data = self.afk_users[member_id]
                reason = afk_data.get('reason', 'No se especificó razón')
                theme_emoji = afk_data.get('theme_emoji', '💤')
                
                # Calcular tiempo transcurrido
                afk_time = datetime.datetime.utcnow().timestamp() - afk_data['timestamp']
                time_formatted = self._format_time_difference(afk_time)
                
                # Obtener la hora exacta de inicio de AFK
                afk_start = datetime.datetime.fromtimestamp(afk_data['timestamp'])
                
                embed = discord.Embed(
                    title=f"{theme_emoji} Estado AFK de {member.display_name}",
                    description=f"{member.mention} está actualmente ausente.",
                    color=member.color
                )
                
                embed.add_field(
                    name="📝 Mensaje",
                    value=reason,
                    inline=False
                )
                
                embed.add_field(
                    name="⏱️ Ausente desde hace",
                    value=time_formatted,
                    inline=True
                )
                
                embed.add_field(
                    name="🕒 Hora de inicio",
                    value=afk_start.strftime('%d/%m/%Y • %H:%M:%S'),
                    inline=True
                )
                
                # Mostrar menciones recibidas si hay alguna
                if 'mentions_received' in afk_data and afk_data['mentions_received'] > 0:
                    embed.add_field(
                        name="📨 Menciones recibidas",
                        value=f"{afk_data['mentions_received']} menciones durante su ausencia",
                        inline=True
                    )
                
                # Usar la imagen guardada del usuario o una por defecto
                if 'image_url' in afk_data:
                    embed.set_image(url=afk_data['image_url'])
                else:
                    embed.set_thumbnail(url=member.display_avatar.url)
                
                embed.set_footer(text="Los horarios están basados en UTC")
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"{member.display_name} no está AFK actualmente.")
        else:
            # Mostrar todos los usuarios AFK del servidor actual
            guild_id = str(ctx.guild.id)
            server_afk_users = {k: v for k, v in self.afk_users.items() if v.get('guild_id') == guild_id}
            
            if not server_afk_users:
                await ctx.send("No hay usuarios AFK en este servidor actualmente.")
                return
            
            embed = discord.Embed(
                title="💤 Usuarios AFK en este servidor",
                description=f"Hay **{len(server_afk_users)}** usuarios ausentes actualmente.",
                color=discord.Color.blue()
            )
            
            for user_id, afk_data in server_afk_users.items():
                try:
                    # Intentar obtener el miembro del servidor
                    member = ctx.guild.get_member(int(user_id))
                    if member:
                        reason = afk_data.get('reason', 'No se especificó razón')
                        theme_emoji = afk_data.get('theme_emoji', '💤')
                        
                        # Calcular tiempo transcurrido
                        afk_time = datetime.datetime.utcnow().timestamp() - afk_data['timestamp']
                        time_formatted = self._format_time_difference(afk_time)
                        
                        # Añadir información de menciones si hay
                        mentions_info = ""
                        if 'mentions_received' in afk_data and afk_data['mentions_received'] > 0:
                            mentions_info = f"\n**Menciones:** {afk_data['mentions_received']}"
                        
                        embed.add_field(
                            name=f"{theme_emoji} {member.display_name}",
                            value=f"**Razón:** {reason}\n**Ausente desde hace:** {time_formatted}{mentions_info}",
                            inline=False
                        )
                except Exception as e:
                    print(f"Error al obtener miembro AFK: {e}")
            
            # Añadir imagen temática
            embed.set_thumbnail(url=await self._get_anime_sleep_image())
            embed.set_footer(text=f"Usa {ctx.prefix}afk status @usuario para ver detalles específicos")
            
            await ctx.send(embed=embed)

    @afk_group.command(name="stats", help="Muestra estadísticas globales de AFK")
    async def afk_stats(self, ctx):
        """Muestra estadísticas globales del sistema AFK."""
        if not self.afk_users:
            await ctx.send("No hay datos de AFK para analizar.")
            return

        # Estadísticas generales
        total_afk = len(self.afk_users)
        total_mentions = sum(data.get('mentions_received', 0) for data in self.afk_users.values())
        
        # Calcular duración promedio (usuarios actuales)
        current_time = datetime.datetime.utcnow().timestamp()
        total_duration = sum(current_time - data.get('timestamp', current_time) for data in self.afk_users.values())
        avg_duration = total_duration / total_afk if total_afk > 0 else 0
        
        # Usuario con más tiempo AFK
        longest_afk_user_id = max(self.afk_users.items(), key=lambda x: current_time - x[1].get('timestamp', 0))[0] if self.afk_users else None
        
        embed = discord.Embed(
            title="📊 Estadísticas del Sistema AFK",
            description="Información sobre el uso del sistema de ausencias.",
            color=discord.Color.gold()
        )
        
        # Estadísticas generales
        stats_general = (
            f"**Usuarios AFK actualmente:** {total_afk}\n"
            f"**Menciones a usuarios AFK:** {total_mentions}\n"
            f"**Duración promedio:** {self._format_time_difference(avg_duration)}\n"
        )
        embed.add_field(name="📌 General", value=stats_general, inline=False)
        
        # Usuario con más tiempo AFK
        if longest_afk_user_id:
            try:
                user_data = self.afk_users[longest_afk_user_id]
                username = user_data.get('username', 'Usuario')
                duration = current_time - user_data.get('timestamp', 0)
                reason = user_data.get('reason', 'No especificado')
                
                longest_afk = (
                    f"**Usuario:** {username}\n"
                    f"**Tiempo ausente:** {self._format_time_difference(duration)}\n"
                    f"**Razón:** {reason}\n"
                )
                embed.add_field(name="🏆 Ausencia más larga", value=longest_afk, inline=False)
            except Exception as e:
                print(f"Error al obtener usuario con más tiempo AFK: {e}")
        
        # Obtener una distribución de temas
        themes = {}
        for user_data in self.afk_users.values():
            theme = user_data.get('theme', 'anime')
            themes[theme] = themes.get(theme, 0) + 1
        
        if themes:
            theme_info = []
            for theme, count in themes.items():
                emoji = "🌸"
                if theme == "gaming": emoji = "🎮"
                elif theme == "working": emoji = "💼"
                elif theme == "sleeping": emoji = "😴"
                elif theme == "studying": emoji = "📚"
                elif theme == "movie": emoji = "🎬"
                
                theme_info.append(f"{emoji} **{theme.capitalize()}:** {count}")
            
            embed.add_field(name="🎨 Temas utilizados", value="\n".join(theme_info), inline=True)
        
        # Añadir imagen decorativa
        embed.set_thumbnail(url=await self._get_anime_sleep_image())
        embed.set_footer(text="Estadísticas actualizadas " + datetime.datetime.utcnow().strftime('%d/%m/%Y • %H:%M:%S'))
        
        await ctx.send(embed=embed)

    @afk_group.command(name="image", aliases=["imagen", "gif"], help="Personaliza la imagen de tu estado AFK")
    async def afk_image(self, ctx, *, search_term=None):
        """Permite personalizar la imagen GIF que se muestra en tu estado AFK."""
        author_id = str(ctx.author.id)
        
        # Verificar si el usuario está AFK
        if author_id not in self.afk_users:
            await ctx.send("No estás en modo AFK actualmente. Primero debes activar tu estado AFK con `afk set`.")
            return
        
        # Si no se especifica término de búsqueda, mostrar instrucciones
        if not search_term:
            embed = discord.Embed(
                title="🖼️ Personalizar imagen AFK",
                description="Este comando te permite cambiar la imagen de tu estado AFK por una de tu elección.",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="💡 Cómo usar",
                value=f"Escribe `{ctx.prefix}afk image <término de búsqueda>` para buscar un GIF específico.\n"
                      f"Ejemplo: `{ctx.prefix}afk image anime sleeping`",
                inline=False
            )
            
            embed.add_field(
                name="🔍 Sugerencias",
                value="• Puedes buscar GIFs de anime\n"
                      "• Intenta términos como 'cute sleeping', 'anime tired', etc.\n"
                      "• El sistema buscará usando Tenor y otras fuentes",
                inline=False
            )
            
            embed.set_footer(text="Los mejores resultados se obtienen con búsquedas en inglés")
            await ctx.send(embed=embed)
            return
            
        # Enviar mensaje de espera mientras se busca
        loading_message = await ctx.send("🔍 Buscando GIFs para tu estado AFK... Esto puede tomar unos segundos.")
            
        # Intentar obtener una imagen con el término de búsqueda
        try:
            # Buscar usando Tenor
            if hasattr(self.bot, 'session') and self.bot.session:
                # Preparar el término de búsqueda
                if not search_term.lower().startswith("anime") and not "anime" in search_term.lower():
                    # Añadir "anime" al término si no lo tiene para mejores resultados
                    tenor_search = f"anime {search_term}"
                else:
                    tenor_search = search_term
                    
                # API de Tenor
                tenor_url = f"https://tenor.googleapis.com/v2/search?q={tenor_search}&key=AIzaSyAQmmT4ceTK_xesoEG1PRfWx7xHnT7k2IE&limit=8&media_filter=gif"
                
                async with self.bot.session.get(tenor_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'results' in data and data['results']:
                            # Crear un menú de selección con los resultados
                            results = data['results'][:8]  # Limitar a 8 resultados
                            
                            # Preparar embed con las opciones
                            embed = discord.Embed(
                                title="🖼️ Selecciona una imagen para tu AFK",
                                description=f"Resultados para: **{search_term}**\n"
                                          f"Reacciona con el número para seleccionar la imagen deseada.",
                                color=discord.Color.purple()
                            )
                            
                            # Añadir cada resultado numerado
                            gif_urls = []
                            for i, gif in enumerate(results, 1):
                                if 'media_formats' in gif:
                                    if 'gif' in gif['media_formats']:
                                        gif_url = gif['media_formats']['gif']['url']
                                        gif_urls.append(gif_url)
                                        embed.add_field(
                                            name=f"Opción {i}",
                                            value=f"[Ver GIF]({gif_url})",
                                            inline=True
                                        )
                            
                            # Si estamos usando una versión de discord.py que soporta vistas y botones
                            if hasattr(discord, "ui") and hasattr(discord.ui, "View"):
                                class GIFSelectView(discord.ui.View):
                                    def __init__(self, ctx, gif_urls, afk_users, user_id):
                                        super().__init__(timeout=60)
                                        self.ctx = ctx
                                        self.gif_urls = gif_urls
                                        self.afk_users = afk_users
                                        self.user_id = user_id
                                        self._add_buttons()
                                        
                                    def _add_buttons(self):
                                        # Añadir botones numerados para cada GIF (máximo 5 por fila)
                                        for i, url in enumerate(self.gif_urls, 1):
                                            button = discord.ui.Button(
                                                label=f"Opción {i}", 
                                                style=discord.ButtonStyle.primary,
                                                custom_id=f"gif_{i-1}"
                                            )
                                            button.callback = self.make_callback(i-1)
                                            self.add_item(button)
                                            
                                    def make_callback(self, index):
                                        async def callback(interaction):
                                            if interaction.user.id != self.ctx.author.id:
                                                await interaction.response.send_message("Solo quien solicitó las imágenes puede seleccionar.", ephemeral=True)
                                                return
                                                
                                            if index < len(self.gif_urls):
                                                selected_url = self.gif_urls[index]
                                                # Actualizar la imagen AFK del usuario
                                                if self.user_id in self.afk_users:
                                                    self.afk_users[self.user_id]['image_url'] = selected_url
                                                    self._save_afk_data()
                                                    
                                                    # Confirmar selección
                                                    embed = discord.Embed(
                                                        title="✅ Imagen AFK actualizada",
                                                        description="La imagen para tu estado AFK ha sido cambiada exitosamente.",
                                                        color=discord.Color.green()
                                                    )
                                                    embed.set_image(url=selected_url)
                                                    await interaction.response.edit_message(content=None, embed=embed, view=None)
                                                else:
                                                    await interaction.response.send_message("Ya no estás en modo AFK.", ephemeral=True)
                                            else:
                                                await interaction.response.send_message("Opción no válida.", ephemeral=True)
                                        return callback
                                        
                                    def _save_afk_data(self):
                                        try:
                                            with open(self.ctx.cog.afk_file_path, 'w', encoding='utf-8') as f:
                                                json.dump(self.afk_users, f, indent=2)
                                        except Exception as e:
                                            print(f"Error guardando datos AFK: {e}")
                                
                                # Crear vista con botones para seleccionar GIF
                                view = GIFSelectView(ctx, gif_urls, self.afk_users, author_id)
                                
                                # Actualizar el mensaje de espera con los resultados
                                await loading_message.edit(content=None, embed=embed, view=view)
                            else:
                                # Versión sin botones para versiones antiguas de discord.py
                                await loading_message.edit(content="Lo siento, esta función requiere una versión más reciente de discord.py.", embed=None)
                        else:
                            await loading_message.edit(content=f"No se encontraron GIFs para '{search_term}'. Intenta con otro término.")
                    else:
                        await loading_message.edit(content="Hubo un error al buscar GIFs. Inténtalo más tarde.")
                        
        except Exception as e:
            print(f"Error en afk_image: {e}")
            await loading_message.edit(content="Ocurrió un error al buscar imágenes. Inténtalo nuevamente más tarde.")

    @afk_group.command(name="message", aliases=["mensaje", "msg"], help="Actualiza tu mensaje AFK")
    async def afk_message(self, ctx, *, new_message=None):
        """Actualiza tu mensaje de ausencia sin desactivar el estado AFK."""
        author_id = str(ctx.author.id)
        
        # Verificar si el usuario está AFK
        if author_id not in self.afk_users:
            await ctx.send("No estás en modo AFK actualmente. Primero debes activar tu estado AFK con `afk set`.")
            return
            
        # Si no se proporciona un nuevo mensaje, mostrar el actual
        if not new_message:
            current_message = self.afk_users[author_id].get('reason', 'No se especificó razón')
            embed = discord.Embed(
                title="📝 Tu mensaje AFK actual",
                description=f"Actualmente tu mensaje de ausencia es:\n\n> {current_message}",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Cómo actualizar",
                value=f"Para cambiarlo, usa `{ctx.prefix}afk message <nuevo mensaje>`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
            
        # Actualizar el mensaje
        old_message = self.afk_users[author_id].get('reason', 'No se especificó razón')
        self.afk_users[author_id]['reason'] = new_message
        
        # Detectar posible tema en el nuevo mensaje (igual que en afk_set)
        lower_message = new_message.lower()
        themes = await self._generate_afk_themes()
        theme_keywords = {
            "gaming": ["juego", "gaming", "jugando", "gamer", "game", "ps4", "ps5", "xbox", "switch", "lol"],
            "working": ["trabajo", "trabajando", "reunión", "meeting", "ocupado", "busy", "currando"],
            "sleeping": ["durmiendo", "dormido", "sueño", "dormir", "cansado", "cama", "siesta", "acostado"],
            "studying": ["estudiando", "estudiar", "examen", "universidad", "escuela", "tarea", "deberes"],
            "movie": ["película", "serie", "viendo", "netflix", "watching", "cinema", "cine", "tv", "anime"],
            "vacation": ["vacaciones", "playa", "descanso", "descansar", "vacation", "holiday", "viaje"],
            "eating": ["comiendo", "comer", "almuerzo", "comida", "cena", "desayuno", "eating", "lunch"],
            "crying": ["llorando", "triste", "sad", "depre", "depresión", "crying", "lágrimas"],
            "rage": ["rage", "enojado", "enfadado", "molesto", "rabia", "ira", "furioso", "angry"],
            "travel": ["viajando", "viaje", "traveling", "journey", "tren", "avión", "airport"],
            "date": ["cita", "date", "pareja", "novio", "novia", "romantico", "romance", "love", "amor"]
        }
        
        # Detectar tema basado en palabras clave
        detected_theme = None
        for theme_id, keywords in theme_keywords.items():
            if any(keyword in lower_message for keyword in keywords):
                detected_theme = theme_id
                break
                
        # Si se detectó un tema, sugerir cambiarlo
        theme_detected = False
        if detected_theme and detected_theme in themes and detected_theme != self.afk_users[author_id].get('theme', 'anime'):
            theme_detected = True
            theme_name = themes[detected_theme]["name"]
            theme_emoji = themes[detected_theme]["emoji"]
        
        # Guardar cambios
        self._save_afk_data()
        
        # Confirmar actualización
        embed = discord.Embed(
            title="✅ Mensaje AFK Actualizado",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Mensaje anterior",
            value=f"> {old_message}",
            inline=False
        )
        
        embed.add_field(
            name="Nuevo mensaje",
            value=f"> {new_message}",
            inline=False
        )
        
        # Si se detectó un tema, sugerir cambiarlo
        if theme_detected:
            embed.add_field(
                name=f"{theme_emoji} Tema sugerido",
                value=f"Tu mensaje sugiere el tema **{theme_name}**. Puedes cambiarlo con `{ctx.prefix}afk theme {detected_theme}`",
                inline=False
            )
        
        embed.set_footer(text="Tu estado AFK permanece activo")
        await ctx.send(embed=embed)

    @afk_group.command(name="timer", aliases=["tiempo", "recordatorio"], help="Establece un temporizador para tu AFK")
    async def afk_timer(self, ctx, duration: str = None):
        """Establece un temporizador para tu estado AFK que te recordará cuando expire."""
        author_id = str(ctx.author.id)
        
        # Verificar si el usuario está AFK
        if author_id not in self.afk_users:
            await ctx.send("No estás en modo AFK actualmente. Primero debes activar tu estado AFK con `afk set`.")
            return
        
        # Si no se proporciona duración, mostrar ayuda
        if not duration:
            embed = discord.Embed(
                title="⏲️ Temporizador AFK",
                description="Establece un recordatorio para cuando termine tu tiempo AFK.",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Formato",
                value=f"`{ctx.prefix}afk timer <duración>`\n"
                      f"La duración puede ser: '30m', '2h', '1d', etc.",
                inline=False
            )
            
            embed.add_field(
                name="Ejemplos",
                value=f"`{ctx.prefix}afk timer 30m` - Recordatorio en 30 minutos\n"
                      f"`{ctx.prefix}afk timer 2h` - Recordatorio en 2 horas\n"
                      f"`{ctx.prefix}afk timer 1d` - Recordatorio en 1 día",
                inline=False
            )
            
            await ctx.send(embed=embed)
            return
        
        # Parsear la duración
        total_seconds = 0
        duration_lower = duration.lower()
        
        try:
            # Formatos soportados: 30s, 15m, 2h, 1d
            if 'd' in duration_lower:
                days = int(duration_lower.split('d')[0])
                total_seconds += days * 86400
            elif 'h' in duration_lower:
                hours = int(duration_lower.split('h')[0])
                total_seconds += hours * 3600
            elif 'm' in duration_lower:
                minutes = int(duration_lower.split('m')[0])
                total_seconds += minutes * 60
            elif 's' in duration_lower:
                seconds = int(duration_lower.split('s')[0])
                total_seconds += seconds
            else:
                # Intenta interpretar como minutos si es solo un número
                total_seconds = int(duration_lower) * 60
        except ValueError:
            await ctx.send("❌ Formato de duración no válido. Usa '30m', '2h', '1d', etc.")
            return
        
        # Verificar límites razonables
        if total_seconds < 60:
            await ctx.send("❌ La duración mínima es de 1 minuto.")
            return
        elif total_seconds > 86400 * 7:  # 7 días
            await ctx.send("❌ La duración máxima es de 7 días.")
            return
        
        # Calcular el tiempo de expiración
        expiration_time = datetime.datetime.utcnow().timestamp() + total_seconds
        
        # Guardar en los datos del usuario
        self.afk_users[author_id]['timer_expiration'] = expiration_time
        self._save_afk_data()
        
        # Formatear el tiempo para mostrar
        expiration_datetime = datetime.datetime.fromtimestamp(expiration_time)
        formatted_time = expiration_datetime.strftime('%d/%m/%Y • %H:%M:%S')
        duration_formatted = self._format_time_difference(total_seconds)
        
        # Enviar confirmación
        embed = discord.Embed(
            title="⏰ Temporizador AFK establecido",
            description=f"Se ha configurado un recordatorio para cuando termine tu tiempo AFK.",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="⏱️ Duración",
            value=duration_formatted,
            inline=True
        )
        
        embed.add_field(
            name="🔄 Vence el",
            value=formatted_time,
            inline=True
        )
        
        embed.set_footer(text="Recibirás un mensaje cuando expire el temporizador")
        
        await ctx.send(embed=embed)
        
        # Programar tarea en segundo plano para notificar cuando expire
        async def timer_task():
            await asyncio.sleep(total_seconds)
            # Verificar si el usuario sigue AFK
            if author_id in self.afk_users and 'timer_expiration' in self.afk_users[author_id]:
                # Calcular si realmente es tiempo de notificar
                current_time = datetime.datetime.utcnow().timestamp()
                if abs(current_time - self.afk_users[author_id]['timer_expiration']) <= 10:  # 10 segundos de tolerancia
                    try:
                        # Intentar enviar DM al usuario
                        user = self.bot.get_user(int(author_id))
                        if user:
                            reminder_embed = discord.Embed(
                                title="⏰ Recordatorio AFK",
                                description="¡Tu temporizador de AFK ha expirado!",
                                color=discord.Color.orange()
                            )
                            
                            reason = self.afk_users[author_id].get('reason', 'No se especificó razón')
                            reminder_embed.add_field(
                                name="📝 Tu mensaje AFK",
                                value=reason,
                                inline=False
                            )
                            
                            # Calcular tiempo total AFK
                            afk_time = current_time - self.afk_users[author_id].get('timestamp', current_time)
                            time_formatted = self._format_time_difference(afk_time)
                            reminder_embed.add_field(
                                name="⏱️ Tiempo AFK total",
                                value=time_formatted,
                                inline=True
                            )
                            
                            reminder_embed.add_field(
                                name="🔄 Opciones",
                                value=f"Usar `afk remove` para desactivar el modo AFK",
                                inline=True
                            )
                            
                            await user.send(embed=reminder_embed)
                    except Exception as e:
                        print(f"Error al enviar recordatorio AFK: {e}")
        
        # Iniciar tarea en segundo plano
        self.bot.loop.create_task(timer_task())

async def setup(bot):
    await bot.add_cog(General(bot))