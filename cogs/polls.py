import discord
from discord.ext import commands
import json
import asyncio
import datetime
import os
import random
from discord import app_commands
import typing
import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Necesario para entornos sin GUI

class Polls(commands.Cog):
    """Sistema de encuestas y votaciones para el servidor"""
    
    def __init__(self, bot):
        self.bot = bot
        self.polls_file = "data/polls.json"
        self.polls = self.load_polls()
        self.poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        self.yes_no_emojis = ["✅", "❌"]
        
        # Iniciar tarea para verificar encuestas expiradas
        self.poll_check_task = self.bot.loop.create_task(self.check_expired_polls())
        
    def cog_unload(self):
        # Cancelar la tarea de verificación de encuestas al descargar el cog
        self.poll_check_task.cancel()
        self.save_polls()
    
    def load_polls(self):
        """Cargar las encuestas desde el archivo JSON"""
        if os.path.exists(self.polls_file):
            try:
                with open(self.polls_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando encuestas: {e}")
                return {"active": {}, "completed": []}
        return {"active": {}, "completed": []}
    
    def save_polls(self):
        """Guardar las encuestas en el archivo JSON"""
        try:
            with open(self.polls_file, 'w', encoding='utf-8') as f:
                json.dump(self.polls, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error guardando encuestas: {e}")
    
    async def check_expired_polls(self):
        """Verificar periódicamente si hay encuestas que han expirado"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            now = datetime.datetime.now().timestamp()
            expired_polls = []
            
            # Buscar encuestas que hayan expirado
            for poll_id, poll in self.polls["active"].items():
                if "end_time" in poll and poll["end_time"] < now:
                    expired_polls.append(poll_id)
            
            # Cerrar las encuestas expiradas
            for poll_id in expired_polls:
                try:
                    await self.end_poll(poll_id)
                except Exception as e:
                    print(f"Error al cerrar encuesta expirada {poll_id}: {e}")
            
            # Guardar los cambios
            if expired_polls:
                self.save_polls()
            
            # Esperar 60 segundos antes de la próxima verificación
            await asyncio.sleep(60)
    
    async def end_poll(self, poll_id):
        """Finalizar una encuesta y mostrar los resultados"""
        poll = self.polls["active"].get(poll_id)
        if not poll:
            return
        
        # Obtener el canal y mensaje de la encuesta
        try:
            channel = self.bot.get_channel(int(poll["channel_id"]))
            if not channel:
                return
            
            message = await channel.fetch_message(int(poll["message_id"]))
            if not message:
                return
            
            # Actualizar las reacciones del mensaje para obtener los votos actuales
            await message.fetch()
            
            # Contar los votos
            votes = {}
            total_votes = 0
            
            # Determinar qué conjunto de emojis se utilizó
            emojis = self.poll_emojis if poll["type"] == "multiple" else self.yes_no_emojis
            
            # Contar los votos para cada opción
            for i, option in enumerate(poll["options"]):
                if i < len(emojis):
                    emoji = emojis[i]
                    reaction = discord.utils.get(message.reactions, emoji=emoji)
                    count = 0
                    if reaction:
                        count = reaction.count - 1  # Restar 1 por la reacción del bot
                        if count < 0:
                            count = 0
                    votes[option] = count
                    total_votes += count
            
            # Crear el mensaje de resultados
            results_embed = discord.Embed(
                title=f"Resultados: {poll['title']}",
                description=f"La encuesta ha finalizado. Total de votos: {total_votes}",
                color=discord.Color.blue()
            )
            
            if total_votes > 0:
                # Añadir los resultados al embed
                for option, count in votes.items():
                    percentage = (count / total_votes) * 100 if total_votes > 0 else 0
                    bar = "█" * int(percentage / 10) if percentage > 0 else ""
                    results_embed.add_field(
                        name=option,
                        value=f"{count} votos ({percentage:.1f}%)\n{bar}",
                        inline=False
                    )
                
                # Determinar la(s) opción(es) ganadora(s)
                max_votes = max(votes.values()) if votes else 0
                winners = [option for option, count in votes.items() if count == max_votes]
                
                if max_votes > 0:
                    winners_text = "\n".join(winners)
                    results_embed.add_field(
                        name="Opción(es) ganadora(s)",
                        value=winners_text,
                        inline=False
                    )
                
                # Generar y adjuntar gráfico si hay más de una opción y hay votos
                if len(poll["options"]) > 1 and total_votes > 0:
                    chart_file = await self.generate_poll_chart(poll["title"], votes)
                    
                    # Enviar mensaje con el gráfico
                    await channel.send(embed=results_embed, file=chart_file)
                else:
                    # Enviar mensaje sin gráfico
                    await channel.send(embed=results_embed)
            else:
                results_embed.add_field(
                    name="Sin votos",
                    value="Nadie votó en esta encuesta.",
                    inline=False
                )
                await channel.send(embed=results_embed)
            
            # Marcar el mensaje original como cerrado
            closed_embed = discord.Embed(
                title=poll["title"],
                description="📊 **ENCUESTA CERRADA** 📊\n\n" + poll["description"],
                color=discord.Color.red()
            )
            closed_embed.set_footer(text=f"Encuesta creada por {poll['author_name']} • Finalizada")
            
            await message.edit(embed=closed_embed)
            
            # Mover la encuesta a completadas
            poll["end_time"] = datetime.datetime.now().timestamp()
            poll["votes"] = votes
            poll["total_votes"] = total_votes
            self.polls["completed"].append(poll)
            del self.polls["active"][poll_id]
            
        except Exception as e:
            print(f"Error al finalizar encuesta {poll_id}: {e}")
            # Intentar limpiar la encuesta fallida
            if poll_id in self.polls["active"]:
                del self.polls["active"][poll_id]
    
    async def generate_poll_chart(self, title, votes):
        """Generar un gráfico de barras para los resultados de la encuesta"""
        # Configurar matplotlib para gráficos
        plt.figure(figsize=(10, 6))
        plt.style.use('ggplot')
        
        options = list(votes.keys())
        counts = list(votes.values())
        
        # Crear gráfico de barras horizontal
        bars = plt.barh(options, counts, color='royalblue')
        
        # Añadir etiquetas con valores
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 0.3, bar.get_y() + bar.get_height()/2, f'{width:.0f}', 
                    ha='left', va='center')
        
        plt.title(f'Resultados: {title}')
        plt.xlabel('Número de Votos')
        plt.tight_layout()
        
        # Guardar el gráfico en un buffer
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        
        # Crear archivo de Discord
        return discord.File(buf, 'poll_results.png')
    
    @commands.hybrid_command(name="poll", description="Crear una encuesta simple de sí/no")
    async def poll(self, ctx, *, question: str):
        """Crea una encuesta simple de sí/no"""
        embed = discord.Embed(
            title="📊 " + question,
            description="Reacciona con ✅ para sí o ❌ para no.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Encuesta creada por {ctx.author.display_name}")
        
        poll_message = await ctx.send(embed=embed)
        
        # Añadir reacciones
        for emoji in self.yes_no_emojis:
            await poll_message.add_reaction(emoji)
        
        # Guardar la encuesta en la base de datos
        poll_id = str(poll_message.id)
        self.polls["active"][poll_id] = {
            "type": "yes_no",
            "title": question,
            "description": "Reacciona con ✅ para sí o ❌ para no.",
            "options": ["Sí", "No"],
            "author_id": str(ctx.author.id),
            "author_name": ctx.author.display_name,
            "channel_id": str(ctx.channel.id),
            "message_id": poll_id,
            "guild_id": str(ctx.guild.id) if ctx.guild else None,
            "created_at": datetime.datetime.now().timestamp(),
            "end_time": None  # Sin tiempo de expiración
        }
        self.save_polls()
    
    @commands.hybrid_command(name="advancedpoll", description="Crear una encuesta avanzada con múltiples opciones")
    @app_commands.describe(
        question="La pregunta de la encuesta",
        duration="Duración de la encuesta en formato 1h, 1d, etc. (opcional)",
        option1="Opción 1",
        option2="Opción 2",
        option3="Opción 3 (opcional)",
        option4="Opción 4 (opcional)",
        option5="Opción 5 (opcional)",
        option6="Opción 6 (opcional)",
        option7="Opción 7 (opcional)",
        option8="Opción 8 (opcional)",
        option9="Opción 9 (opcional)",
        option10="Opción 10 (opcional)"
    )
    async def advancedpoll(
        self, ctx, 
        question: str,
        duration: typing.Optional[str] = None,
        option1: str = None,
        option2: str = None,
        option3: typing.Optional[str] = None,
        option4: typing.Optional[str] = None,
        option5: typing.Optional[str] = None,
        option6: typing.Optional[str] = None,
        option7: typing.Optional[str] = None,
        option8: typing.Optional[str] = None,
        option9: typing.Optional[str] = None,
        option10: typing.Optional[str] = None
    ):
        """Crea una encuesta con múltiples opciones y duración opcional"""
        if not option1 or not option2:
            await ctx.send("❌ Debes proporcionar al menos dos opciones para la encuesta.")
            return
        
        options = [opt for opt in [option1, option2, option3, option4, option5, 
                                  option6, option7, option8, option9, option10] if opt]
        
        # Validar que no hay más de 10 opciones
        if len(options) > 10:
            await ctx.send("❌ No puedes crear una encuesta con más de 10 opciones.")
            return
        
        # Procesar la duración si se proporciona
        end_time = None
        duration_text = "sin límite de tiempo"
        
        if duration:
            try:
                duration_seconds = self.parse_duration(duration)
                if duration_seconds > 0:
                    end_time = datetime.datetime.now().timestamp() + duration_seconds
                    # Formatear la duración para mostrarla
                    if duration_seconds < 60:
                        duration_text = f"{duration_seconds} segundos"
                    elif duration_seconds < 3600:
                        minutes = duration_seconds // 60
                        duration_text = f"{minutes} minuto{'s' if minutes != 1 else ''}"
                    elif duration_seconds < 86400:
                        hours = duration_seconds // 3600
                        duration_text = f"{hours} hora{'s' if hours != 1 else ''}"
                    else:
                        days = duration_seconds // 86400
                        duration_text = f"{days} día{'s' if days != 1 else ''}"
            except ValueError:
                await ctx.send("❌ Formato de duración inválido. Usa formatos como '1h', '30m', '1d', etc.")
                return
        
        # Crear el mensaje de la encuesta
        description = f"**Duración:** {duration_text}\n\n"
        for i, option in enumerate(options):
            emoji = self.poll_emojis[i]
            description += f"{emoji} {option}\n"
        
        embed = discord.Embed(
            title="📊 " + question,
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Encuesta creada por {ctx.author.display_name}")
        
        poll_message = await ctx.send(embed=embed)
        
        # Añadir reacciones
        for i in range(len(options)):
            await poll_message.add_reaction(self.poll_emojis[i])
        
        # Guardar la encuesta en la base de datos
        poll_id = str(poll_message.id)
        self.polls["active"][poll_id] = {
            "type": "multiple",
            "title": question,
            "description": description,
            "options": options,
            "author_id": str(ctx.author.id),
            "author_name": ctx.author.display_name,
            "channel_id": str(ctx.channel.id),
            "message_id": poll_id,
            "guild_id": str(ctx.guild.id) if ctx.guild else None,
            "created_at": datetime.datetime.now().timestamp(),
            "end_time": end_time
        }
        self.save_polls()
    
    @commands.hybrid_command(name="endpoll", description="Finalizar una encuesta manualmente")
    async def endpoll(self, ctx, message_id: str):
        """Finaliza una encuesta manualmente usando su ID de mensaje"""
        # Verificar si el mensaje_id es válido
        try:
            int(message_id)
        except ValueError:
            await ctx.send("❌ ID de mensaje inválido. Debe ser un número.")
            return
        
        # Verificar si la encuesta existe
        if message_id not in self.polls["active"]:
            await ctx.send("❌ No se encontró ninguna encuesta activa con ese ID.")
            return
        
        poll = self.polls["active"][message_id]
        
        # Verificar si el usuario tiene permisos para finalizar la encuesta
        is_author = str(ctx.author.id) == poll["author_id"]
        is_admin = ctx.author.guild_permissions.administrator if ctx.guild else False
        
        if not (is_author or is_admin):
            await ctx.send("❌ Solo el creador de la encuesta o un administrador puede finalizarla.")
            return
        
        # Finalizar la encuesta
        await ctx.send("🔄 Finalizando encuesta...")
        await self.end_poll(message_id)
        self.save_polls()
        await ctx.send("✅ Encuesta finalizada y resultados publicados.")
    
    @commands.hybrid_command(name="pollinfo", description="Muestra información sobre una encuesta activa")
    async def pollinfo(self, ctx, message_id: str):
        """Muestra información detallada sobre una encuesta activa"""
        try:
            int(message_id)
        except ValueError:
            await ctx.send("❌ ID de mensaje inválido. Debe ser un número.")
            return
        
        if message_id not in self.polls["active"]:
            await ctx.send("❌ No se encontró ninguna encuesta activa con ese ID.")
            return
        
        poll = self.polls["active"][message_id]
        
        # Calcular tiempo restante si hay un tiempo de finalización
        remaining_time = "Sin límite de tiempo"
        if poll["end_time"]:
            now = datetime.datetime.now().timestamp()
            if poll["end_time"] > now:
                seconds_remaining = int(poll["end_time"] - now)
                # Formatear el tiempo restante
                if seconds_remaining < 60:
                    remaining_time = f"{seconds_remaining} segundos"
                elif seconds_remaining < 3600:
                    minutes = seconds_remaining // 60
                    remaining_time = f"{minutes} minuto{'s' if minutes != 1 else ''}"
                elif seconds_remaining < 86400:
                    hours = seconds_remaining // 3600
                    minutes = (seconds_remaining % 3600) // 60
                    remaining_time = f"{hours} hora{'s' if hours != 1 else ''} y {minutes} minuto{'s' if minutes != 1 else ''}"
                else:
                    days = seconds_remaining // 86400
                    hours = (seconds_remaining % 86400) // 3600
                    remaining_time = f"{days} día{'s' if days != 1 else ''} y {hours} hora{'s' if hours != 1 else ''}"
            else:
                remaining_time = "Finalizada (pendiente de procesar)"
        
        # Crear embed con la información
        embed = discord.Embed(
            title=f"Información de Encuesta: {poll['title']}",
            color=discord.Color.blue()
        )
        
        # Información básica
        embed.add_field(name="Creada por", value=poll["author_name"], inline=True)
        
        # Convertir timestamp a fecha legible
        created_at = datetime.datetime.fromtimestamp(poll["created_at"])
        embed.add_field(name="Creada el", value=created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        
        embed.add_field(name="Tiempo restante", value=remaining_time, inline=True)
        
        # Opciones
        options_text = "\n".join([f"• {option}" for option in poll["options"]])
        embed.add_field(name="Opciones", value=options_text, inline=False)
        
        # Enlace al mensaje
        channel_id = int(poll["channel_id"])
        message_id = int(poll["message_id"])
        guild_id = int(poll["guild_id"]) if poll["guild_id"] else None
        
        if guild_id and guild_id == ctx.guild.id:
            embed.add_field(
                name="Enlace",
                value=f"[Ir a la encuesta](https://discord.com/channels/{guild_id}/{channel_id}/{message_id})",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="activepolls", description="Muestra todas las encuestas activas en el servidor")
    async def activepolls(self, ctx):
        """Muestra una lista de todas las encuestas activas en el servidor"""
        if not ctx.guild:
            await ctx.send("❌ Este comando solo puede ser usado en un servidor.")
            return
        
        # Filtrar encuestas por el servidor actual
        guild_id = str(ctx.guild.id)
        guild_polls = {poll_id: poll for poll_id, poll in self.polls["active"].items() 
                      if poll.get("guild_id") == guild_id}
        
        if not guild_polls:
            await ctx.send("📊 No hay encuestas activas en este servidor.")
            return
        
        # Crear embed con la lista de encuestas
        embed = discord.Embed(
            title="Encuestas Activas",
            description=f"Hay {len(guild_polls)} encuestas activas en este servidor.",
            color=discord.Color.blue()
        )
        
        # Añadir cada encuesta al embed
        for poll_id, poll in guild_polls.items():
            # Calcular tiempo restante si hay un tiempo de finalización
            time_info = "Sin límite de tiempo"
            if poll["end_time"]:
                now = datetime.datetime.now().timestamp()
                if poll["end_time"] > now:
                    seconds_remaining = int(poll["end_time"] - now)
                    if seconds_remaining < 60:
                        time_info = f"{seconds_remaining}s restantes"
                    elif seconds_remaining < 3600:
                        minutes = seconds_remaining // 60
                        time_info = f"{minutes}m restantes"
                    elif seconds_remaining < 86400:
                        hours = seconds_remaining // 3600
                        time_info = f"{hours}h restantes"
                    else:
                        days = seconds_remaining // 86400
                        time_info = f"{days}d restantes"
                else:
                    time_info = "Finalizada (pendiente)"
            
            # Crear enlace al mensaje
            channel_id = poll["channel_id"]
            message_id = poll["message_id"]
            message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
            
            # Añadir campo al embed
            embed.add_field(
                name=poll["title"],
                value=f"Creada por: {poll['author_name']}\nTiempo: {time_info}\n[Ir a la encuesta]({message_link})\nID: `{poll_id}`",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="pollstats", description="Muestra estadísticas de las encuestas del servidor")
    async def pollstats(self, ctx):
        """Muestra estadísticas de las encuestas del servidor"""
        if not ctx.guild:
            await ctx.send("❌ Este comando solo puede ser usado en un servidor.")
            return
        
        guild_id = str(ctx.guild.id)
        
        # Contar encuestas activas en este servidor
        active_polls = [poll for poll_id, poll in self.polls["active"].items() 
                       if poll.get("guild_id") == guild_id]
        active_count = len(active_polls)
        
        # Contar encuestas completadas en este servidor
        completed_polls = [poll for poll in self.polls["completed"] 
                          if poll.get("guild_id") == guild_id]
        completed_count = len(completed_polls)
        
        # Calcular estadísticas adicionales
        total_votes = sum(poll.get("total_votes", 0) for poll in completed_polls)
        avg_votes_per_poll = total_votes / completed_count if completed_count > 0 else 0
        
        # Contar por tipo de encuesta
        yes_no_count = sum(1 for poll in completed_polls if poll.get("type") == "yes_no")
        multiple_count = sum(1 for poll in completed_polls if poll.get("type") == "multiple")
        
        # Contar creadores de encuestas
        creators = {}
        for poll in completed_polls + active_polls:
            author_id = poll.get("author_id")
            if author_id:
                creators[author_id] = creators.get(author_id, 0) + 1
        
        top_creators = sorted(creators.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Crear embed con estadísticas
        embed = discord.Embed(
            title=f"Estadísticas de Encuestas - {ctx.guild.name}",
            color=discord.Color.blue()
        )
        
        # Añadir estadísticas generales
        embed.add_field(name="Encuestas Activas", value=str(active_count), inline=True)
        embed.add_field(name="Encuestas Completadas", value=str(completed_count), inline=True)
        embed.add_field(name="Total de Encuestas", value=str(active_count + completed_count), inline=True)
        
        # Añadir estadísticas de votación
        embed.add_field(name="Total de Votos", value=f"{total_votes:,}", inline=True)
        embed.add_field(name="Promedio de Votos por Encuesta", value=f"{avg_votes_per_poll:.1f}", inline=True)
        
        # Añadir estadísticas por tipo
        embed.add_field(name="Encuestas Sí/No", value=str(yes_no_count), inline=True)
        embed.add_field(name="Encuestas Múltiples", value=str(multiple_count), inline=True)
        
        # Añadir top creadores
        if top_creators:
            creators_text = ""
            for author_id, count in top_creators:
                user = ctx.guild.get_member(int(author_id))
                name = user.display_name if user else "Usuario Desconocido"
                creators_text += f"• {name}: {count} encuestas\n"
            
            embed.add_field(name="Top Creadores de Encuestas", value=creators_text, inline=False)
        
        # Establecer thumbnail con el icono del servidor
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="quickpoll", description="Crear rápidamente una encuesta con múltiples opciones")
    @app_commands.describe(
        question="La pregunta de la encuesta",
        options="Las opciones separadas por comas (ej: Opción 1, Opción 2, Opción 3)"
    )
    async def quickpoll(self, ctx, question: str, options: str):
        """Crea rápidamente una encuesta con opciones separadas por comas"""
        # Dividir las opciones por comas
        option_list = [opt.strip() for opt in options.split(',') if opt.strip()]
        
        if len(option_list) < 2:
            await ctx.send("❌ Debes proporcionar al menos dos opciones para la encuesta.")
            return
        
        if len(option_list) > 10:
            await ctx.send("❌ No puedes crear una encuesta con más de 10 opciones.")
            return
        
        # Crear el mensaje de la encuesta
        description = ""
        for i, option in enumerate(option_list):
            emoji = self.poll_emojis[i]
            description += f"{emoji} {option}\n"
        
        embed = discord.Embed(
            title="📊 " + question,
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Encuesta creada por {ctx.author.display_name}")
        
        poll_message = await ctx.send(embed=embed)
        
        # Añadir reacciones
        for i in range(len(option_list)):
            await poll_message.add_reaction(self.poll_emojis[i])
        
        # Guardar la encuesta en la base de datos
        poll_id = str(poll_message.id)
        self.polls["active"][poll_id] = {
            "type": "multiple",
            "title": question,
            "description": description,
            "options": option_list,
            "author_id": str(ctx.author.id),
            "author_name": ctx.author.display_name,
            "channel_id": str(ctx.channel.id),
            "message_id": poll_id,
            "guild_id": str(ctx.guild.id) if ctx.guild else None,
            "created_at": datetime.datetime.now().timestamp(),
            "end_time": None  # Sin tiempo de expiración
        }
        self.save_polls()
    
    @commands.hybrid_command(name="vote", description="Votar en una encuesta por su ID")
    async def vote(self, ctx, poll_id: str, option: int):
        """Vota en una encuesta usando su ID y el número de opción"""
        if poll_id not in self.polls["active"]:
            await ctx.send("❌ No se encontró ninguna encuesta activa con ese ID.")
            return
        
        poll = self.polls["active"][poll_id]
        
        # Verificar si la opción es válida
        if option < 1 or option > len(poll["options"]):
            await ctx.send(f"❌ Opción inválida. Debe ser un número entre 1 y {len(poll['options'])}.")
            return
        
        try:
            # Obtener mensaje de la encuesta
            channel = self.bot.get_channel(int(poll["channel_id"]))
            if not channel:
                await ctx.send("❌ No se pudo encontrar el canal de la encuesta.")
                return
            
            message = await channel.fetch_message(int(poll["message_id"]))
            if not message:
                await ctx.send("❌ No se pudo encontrar el mensaje de la encuesta.")
                return
            
            # Determinar el emoji a usar
            emoji_index = option - 1
            emojis = self.poll_emojis if poll["type"] == "multiple" else self.yes_no_emojis
            emoji = emojis[emoji_index]
            
            # Añadir la reacción del usuario
            await message.add_reaction(emoji)
            
            # Confirmar al usuario
            option_text = poll["options"][emoji_index]
            await ctx.send(f"✅ Has votado por la opción **{option_text}** en la encuesta: {poll['title']}")
            
        except Exception as e:
            await ctx.send(f"❌ Error al votar: {str(e)}")
    
    def parse_duration(self, duration_str):
        """Convierte una cadena de duración (como '1h', '30m', '1d') a segundos"""
        duration_str = duration_str.lower().strip()
        
        # Si solo hay números, asumir segundos
        if duration_str.isdigit():
            return int(duration_str)
        
        # Buscar el formato de duración
        if not any(unit in duration_str for unit in ['s', 'm', 'h', 'd']):
            raise ValueError("Formato de duración inválido")
        
        total_seconds = 0
        
        # Procesar segundos
        if 's' in duration_str:
            s_split = duration_str.split('s')
            if s_split[0]:
                seconds = int(''.join(filter(str.isdigit, s_split[0])))
                total_seconds += seconds
            duration_str = s_split[-1] if len(s_split) > 1 else ''
        
        # Procesar minutos
        if 'm' in duration_str:
            m_split = duration_str.split('m')
            if m_split[0]:
                minutes = int(''.join(filter(str.isdigit, m_split[0])))
                total_seconds += minutes * 60
            duration_str = m_split[-1] if len(m_split) > 1 else ''
        
        # Procesar horas
        if 'h' in duration_str:
            h_split = duration_str.split('h')
            if h_split[0]:
                hours = int(''.join(filter(str.isdigit, h_split[0])))
                total_seconds += hours * 3600
            duration_str = h_split[-1] if len(h_split) > 1 else ''
        
        # Procesar días
        if 'd' in duration_str:
            d_split = duration_str.split('d')
            if d_split[0]:
                days = int(''.join(filter(str.isdigit, d_split[0])))
                total_seconds += days * 86400
        
        return total_seconds

async def setup(bot):
    await bot.add_cog(Polls(bot))