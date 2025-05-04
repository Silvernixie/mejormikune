import discord
from discord.ext import commands
import json
import datetime
import os
import asyncio
import matplotlib.pyplot as plt
from io import BytesIO
import typing
from collections import Counter
import matplotlib
matplotlib.use('Agg')  # Necesario para entornos sin GUI

class Statistics(commands.Cog):
    """Sistema de registro y estadísticas para el servidor"""
    
    def __init__(self, bot):
        self.bot = bot
        self.stats_file = "data/statistics.json"
        self.data = self.load_data()
        self.event_types = {
            "messages": "Mensajes enviados",
            "joins": "Usuarios unidos",
            "leaves": "Usuarios salidos",
            "reactions": "Reacciones añadidas",
            "voice_time": "Tiempo en voz (minutos)",
            "commands": "Comandos usados"
        }
        # Iniciar tareas de fondo
        self.bg_task = self.bot.loop.create_task(self.save_data_periodically())
        self.daily_reset_task = self.bot.loop.create_task(self.daily_reset())
        
    def cog_unload(self):
        self.bg_task.cancel()
        self.daily_reset_task.cancel()
        self.save_data()
    
    def load_data(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading statistics data: {e}")
                return self.initialize_data()
        return self.initialize_data()
    
    def initialize_data(self):
        return {
            "guilds": {},
            "users": {},
            "channels": {},
            "global": {
                "start_date": datetime.datetime.now().timestamp(),
                "total_messages": 0,
                "commands_used": 0,
                "users_joined": 0,
                "users_left": 0,
                "voice_minutes": 0
            },
            "daily": {},
            "voice_sessions": {}
        }
    
    def save_data(self):
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving statistics data: {e}")
    
    async def save_data_periodically(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.save_data()
            await asyncio.sleep(300)  # Guardar cada 5 minutos
    
    async def daily_reset(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # Calcular hora hasta la próxima medianoche
            now = datetime.datetime.now()
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            seconds_until_midnight = (tomorrow - now).total_seconds()
            
            # Esperar hasta la medianoche
            await asyncio.sleep(seconds_until_midnight)
            
            # Realizar la actualización diaria
            today_str = now.strftime("%Y-%m-%d")
            if today_str not in self.data["daily"]:
                self.data["daily"][today_str] = {
                    "messages": 0,
                    "commands": 0,
                    "joins": 0,
                    "leaves": 0,
                    "voice_time": 0,
                    "active_users": 0,
                    "reactions": 0
                }
            
            # Guarda los datos
            self.save_data()
            print(f"[Stats] Daily reset completed at {datetime.datetime.now()}")
    
    def get_guild_data(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.data["guilds"]:
            self.data["guilds"][guild_id] = {
                "messages": 0,
                "commands": 0,
                "joins": 0,
                "leaves": 0,
                "voice_time": 0,
                "channels": {},
                "members": {},
                "hourly_activity": {str(i): 0 for i in range(24)},
                "commands_used": {},
                "first_seen": datetime.datetime.now().timestamp()
            }
        return self.data["guilds"][guild_id]
    
    def get_user_data(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "messages": 0,
                "commands": 0,
                "voice_time": 0,
                "reactions_added": 0,
                "reactions_received": 0,
                "guilds": {},
                "first_seen": datetime.datetime.now().timestamp(),
                "last_seen": datetime.datetime.now().timestamp(),
                "last_message": None
            }
        return self.data["users"][user_id]
    
    def get_channel_data(self, channel_id):
        channel_id = str(channel_id)
        if channel_id not in self.data["channels"]:
            self.data["channels"][channel_id] = {
                "messages": 0,
                "commands": 0,
                "users": {},
                "hourly_activity": {str(i): 0 for i in range(24)},
                "first_message": datetime.datetime.now().timestamp(),
                "last_message": datetime.datetime.now().timestamp()
            }
        return self.data["channels"][channel_id]
    
    def get_today_data(self):
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        if today_str not in self.data["daily"]:
            self.data["daily"][today_str] = {
                "messages": 0,
                "commands": 0,
                "joins": 0,
                "leaves": 0,
                "voice_time": 0,
                "active_users": 0,
                "reactions": 0
            }
        return self.data["daily"][today_str]
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Actualizar estadísticas globales
        self.data["global"]["total_messages"] += 1
        
        # Actualizar estadísticas de hoy
        today_data = self.get_today_data()
        today_data["messages"] += 1
        
        # Si es un mensaje en un servidor, actualizar datos del servidor
        if message.guild:
            guild_id = str(message.guild.id)
            channel_id = str(message.channel.id)
            user_id = str(message.author.id)
            
            # Actualizar datos del servidor
            guild_data = self.get_guild_data(guild_id)
            guild_data["messages"] += 1
            
            # Actualizar actividad por hora
            hour = datetime.datetime.now().hour
            guild_data["hourly_activity"][str(hour)] = guild_data["hourly_activity"].get(str(hour), 0) + 1
            
            # Actualizar datos del canal
            if channel_id not in guild_data["channels"]:
                guild_data["channels"][channel_id] = {"messages": 0, "users": {}}
            
            guild_data["channels"][channel_id]["messages"] = guild_data["channels"][channel_id].get("messages", 0) + 1
            
            if user_id not in guild_data["channels"][channel_id].get("users", {}):
                guild_data["channels"][channel_id]["users"][user_id] = 0
            
            guild_data["channels"][channel_id]["users"][user_id] = guild_data["channels"][channel_id]["users"].get(user_id, 0) + 1
            
            # Actualizar datos del miembro en el servidor
            if user_id not in guild_data.get("members", {}):
                guild_data["members"][user_id] = {"messages": 0, "commands": 0, "voice_time": 0}
            
            guild_data["members"][user_id]["messages"] = guild_data["members"][user_id].get("messages", 0) + 1
            
            # Actualizar datos del canal global
            channel_data = self.get_channel_data(channel_id)
            channel_data["messages"] += 1
            channel_data["last_message"] = datetime.datetime.now().timestamp()
            
            if user_id not in channel_data.get("users", {}):
                channel_data["users"][user_id] = 0
            
            channel_data["users"][user_id] = channel_data["users"].get(user_id, 0) + 1
            
            # Actualizar actividad por hora del canal
            channel_data["hourly_activity"][str(hour)] = channel_data["hourly_activity"].get(str(hour), 0) + 1
        
        # Actualizar datos del usuario
        user_data = self.get_user_data(message.author.id)
        user_data["messages"] += 1
        user_data["last_seen"] = datetime.datetime.now().timestamp()
        user_data["last_message"] = {
            "content": message.content[:100] + ("..." if len(message.content) > 100 else ""),
            "timestamp": datetime.datetime.now().timestamp(),
            "channel_id": str(message.channel.id) if message.channel else None,
            "guild_id": str(message.guild.id) if message.guild else None
        }
        
        # Si es un mensaje en un servidor, actualizar la relación usuario-servidor
        if message.guild:
            guild_id = str(message.guild.id)
            if guild_id not in user_data.get("guilds", {}):
                user_data["guilds"][guild_id] = {"messages": 0, "commands": 0, "voice_time": 0}
            
            user_data["guilds"][guild_id]["messages"] = user_data["guilds"][guild_id].get("messages", 0) + 1
        
        # Incrementar el contador de usuarios activos hoy si es la primera vez que vemos a este usuario hoy
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        if not any(m.get("timestamp", 0) > datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() for m in [user_data.get("last_message", {})] if m):
            today_data["active_users"] += 1
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        if ctx.author.bot:
            return
        
        command_name = ctx.command.qualified_name
        
        # Actualizar estadísticas globales
        self.data["global"]["commands_used"] += 1
        
        # Actualizar estadísticas de hoy
        today_data = self.get_today_data()
        today_data["commands"] += 1
        
        # Si es un comando en un servidor, actualizar datos del servidor
        if ctx.guild:
            guild_id = str(ctx.guild.id)
            user_id = str(ctx.author.id)
            
            # Actualizar datos del servidor
            guild_data = self.get_guild_data(guild_id)
            guild_data["commands"] += 1
            
            # Actualizar contador de comandos específicos
            if "commands_used" not in guild_data:
                guild_data["commands_used"] = {}
            
            guild_data["commands_used"][command_name] = guild_data["commands_used"].get(command_name, 0) + 1
            
            # Actualizar datos del miembro en el servidor
            if user_id not in guild_data.get("members", {}):
                guild_data["members"][user_id] = {"messages": 0, "commands": 0, "voice_time": 0}
            
            guild_data["members"][user_id]["commands"] = guild_data["members"][user_id].get("commands", 0) + 1
        
        # Actualizar datos del usuario
        user_data = self.get_user_data(ctx.author.id)
        user_data["commands"] += 1
        user_data["last_seen"] = datetime.datetime.now().timestamp()
        
        # Si es un comando en un servidor, actualizar la relación usuario-servidor
        if ctx.guild:
            guild_id = str(ctx.guild.id)
            if guild_id not in user_data.get("guilds", {}):
                user_data["guilds"][guild_id] = {"messages": 0, "commands": 0, "voice_time": 0}
            
            user_data["guilds"][guild_id]["commands"] = user_data["guilds"][guild_id].get("commands", 0) + 1
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        
        # Actualizar estadísticas de hoy
        today_data = self.get_today_data()
        today_data["reactions"] += 1
        
        # Actualizar datos del usuario que reaccionó
        user_data = self.get_user_data(user.id)
        user_data["reactions_added"] += 1
        user_data["last_seen"] = datetime.datetime.now().timestamp()
        
        # Actualizar datos del autor del mensaje si no es un bot
        if not reaction.message.author.bot:
            author_data = self.get_user_data(reaction.message.author.id)
            author_data["reactions_received"] += 1
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        
        # Actualizar estadísticas globales
        self.data["global"]["users_joined"] += 1
        
        # Actualizar estadísticas de hoy
        today_data = self.get_today_data()
        today_data["joins"] += 1
        
        # Actualizar datos del servidor
        guild_id = str(member.guild.id)
        guild_data = self.get_guild_data(guild_id)
        guild_data["joins"] += 1
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return
        
        # Actualizar estadísticas globales
        self.data["global"]["users_left"] += 1
        
        # Actualizar estadísticas de hoy
        today_data = self.get_today_data()
        today_data["leaves"] += 1
        
        # Actualizar datos del servidor
        guild_id = str(member.guild.id)
        guild_data = self.get_guild_data(guild_id)
        guild_data["leaves"] += 1
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        
        user_id = str(member.id)
        now = datetime.datetime.now().timestamp()
        
        # Entró a un canal de voz
        if before.channel is None and after.channel is not None:
            if "voice_sessions" not in self.data:
                self.data["voice_sessions"] = {}
            
            self.data["voice_sessions"][user_id] = {
                "start_time": now,
                "channel_id": str(after.channel.id),
                "guild_id": str(after.channel.guild.id)
            }
        
        # Salió de un canal de voz
        elif before.channel is not None and (after.channel is None or before.channel.id != after.channel.id):
            if "voice_sessions" in self.data and user_id in self.data["voice_sessions"]:
                session = self.data["voice_sessions"][user_id]
                start_time = session.get("start_time", now)
                duration_seconds = now - start_time
                duration_minutes = duration_seconds / 60
                
                # Actualizar estadísticas globales
                self.data["global"]["voice_minutes"] += duration_minutes
                
                # Actualizar estadísticas de hoy
                today_data = self.get_today_data()
                today_data["voice_time"] += duration_minutes
                
                # Actualizar datos del usuario
                user_data = self.get_user_data(user_id)
                user_data["voice_time"] += duration_minutes
                user_data["last_seen"] = now
                
                # Actualizar datos del servidor y la relación usuario-servidor
                if "guild_id" in session:
                    guild_id = session["guild_id"]
                    guild_data = self.get_guild_data(guild_id)
                    guild_data["voice_time"] += duration_minutes
                    
                    # Asegurarse de que existe la entrada para el miembro
                    if user_id not in guild_data.get("members", {}):
                        guild_data["members"][user_id] = {"messages": 0, "commands": 0, "voice_time": 0}
                    
                    guild_data["members"][user_id]["voice_time"] = guild_data["members"][user_id].get("voice_time", 0) + duration_minutes
                    
                    # Actualizar la relación usuario-servidor
                    if "guilds" not in user_data:
                        user_data["guilds"] = {}
                    
                    if guild_id not in user_data["guilds"]:
                        user_data["guilds"][guild_id] = {"messages": 0, "commands": 0, "voice_time": 0}
                    
                    user_data["guilds"][guild_id]["voice_time"] = user_data["guilds"][guild_id].get("voice_time", 0) + duration_minutes
                
                # Eliminar la sesión
                del self.data["voice_sessions"][user_id]
    
    @commands.hybrid_command(name="serverstats", description="Muestra estadísticas del servidor")
    async def serverstats(self, ctx):
        """Muestra estadísticas detalladas del servidor"""
        if not ctx.guild:
            await ctx.send("❌ Este comando solo puede ser usado en un servidor.")
            return
        
        guild_data = self.get_guild_data(ctx.guild.id)
        
        # Calcular tasa de retención
        retention_rate = 0
        if guild_data["joins"] > 0:
            retention_rate = max(0, (guild_data["joins"] - guild_data["leaves"]) / guild_data["joins"] * 100)
        
        # Crear embed
        embed = discord.Embed(
            title=f"Estadísticas de {ctx.guild.name}",
            color=discord.Color.blue(),
            description=f"Estadísticas desde {datetime.datetime.fromtimestamp(guild_data.get('first_seen', 0)).strftime('%d/%m/%Y')}"
        )
        
        # Añadir campos principales
        embed.add_field(name="Mensajes Totales", value=f"{guild_data['messages']:,}", inline=True)
        embed.add_field(name="Comandos Usados", value=f"{guild_data['commands']:,}", inline=True)
        embed.add_field(name="Tiempo en Voz", value=f"{int(guild_data['voice_time']):,} minutos", inline=True)
        embed.add_field(name="Miembros Unidos", value=f"{guild_data['joins']:,}", inline=True)
        embed.add_field(name="Miembros Salidos", value=f"{guild_data['leaves']:,}", inline=True)
        embed.add_field(name="Tasa de Retención", value=f"{retention_rate:.1f}%", inline=True)
        
        # Comandos más usados
        top_commands = sorted(guild_data.get("commands_used", {}).items(), key=lambda x: x[1], reverse=True)[:5]
        if top_commands:
            commands_text = "\n".join([f"• {cmd}: {count:,}" for cmd, count in top_commands])
            embed.add_field(name="Comandos Más Usados", value=commands_text or "No hay datos", inline=False)
        
        # Usuarios más activos (mensajes)
        top_users_messages = sorted(guild_data.get("members", {}).items(), key=lambda x: x[1].get("messages", 0), reverse=True)[:5]
        if top_users_messages:
            users_text = "\n".join([f"• <@{user_id}>: {data.get('messages', 0):,} mensajes" for user_id, data in top_users_messages])
            embed.add_field(name="Usuarios Más Activos (Mensajes)", value=users_text or "No hay datos", inline=False)
        
        # Usuarios más activos (voz)
        top_users_voice = sorted(guild_data.get("members", {}).items(), key=lambda x: x[1].get("voice_time", 0), reverse=True)[:5]
        if top_users_voice:
            users_text = "\n".join([f"• <@{user_id}>: {int(data.get('voice_time', 0)):,} minutos" for user_id, data in top_users_voice])
            embed.add_field(name="Usuarios Más Activos (Voz)", value=users_text or "No hay datos", inline=False)
        
        # Establecer thumbnail
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="channelstats", description="Muestra estadísticas del canal")
    async def channelstats(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        """Muestra estadísticas detalladas de un canal de texto"""
        if not ctx.guild:
            await ctx.send("❌ Este comando solo puede ser usado en un servidor.")
            return
        
        target_channel = channel or ctx.channel
        channel_id = str(target_channel.id)
        
        channel_data = self.get_channel_data(channel_id)
        guild_data = self.get_guild_data(ctx.guild.id)
        
        # Crear embed
        embed = discord.Embed(
            title=f"Estadísticas del Canal #{target_channel.name}",
            color=discord.Color.blue(),
            description=f"Estadísticas desde {datetime.datetime.fromtimestamp(channel_data.get('first_message', 0)).strftime('%d/%m/%Y')}"
        )
        
        # Añadir campos principales
        embed.add_field(name="Mensajes Totales", value=f"{channel_data['messages']:,}", inline=True)
        embed.add_field(name="Comandos Usados", value=f"{channel_data['commands']:,}", inline=True)
        
        # Porcentaje de actividad del servidor
        if guild_data["messages"] > 0:
            activity_percent = (channel_data['messages'] / guild_data["messages"]) * 100
            embed.add_field(name="% de Actividad del Servidor", value=f"{activity_percent:.1f}%", inline=True)
        
        # Último mensaje
        last_message_time = datetime.datetime.fromtimestamp(channel_data.get('last_message', 0))
        embed.add_field(name="Último Mensaje", value=f"{last_message_time.strftime('%d/%m/%Y %H:%M')}", inline=True)
        
        # Usuarios más activos en el canal
        top_users = sorted(channel_data.get("users", {}).items(), key=lambda x: x[1], reverse=True)[:5]
        if top_users:
            users_text = "\n".join([f"• <@{user_id}>: {count:,} mensajes" for user_id, count in top_users])
            embed.add_field(name="Usuarios Más Activos", value=users_text or "No hay datos", inline=False)
        
        # Gráfico de actividad por hora
        await self.send_hourly_activity_chart(ctx, channel_data.get("hourly_activity", {}), f"Actividad por Hora - #{target_channel.name}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="userstats", description="Muestra estadísticas de un usuario")
    async def userstats(self, ctx, user: typing.Optional[discord.Member] = None):
        """Muestra estadísticas detalladas de un usuario"""
        if not ctx.guild:
            await ctx.send("❌ Este comando solo puede ser usado en un servidor.")
            return
        
        target_user = user or ctx.author
        user_id = str(target_user.id)
        
        user_data = self.get_user_data(user_id)
        guild_data = self.get_guild_data(ctx.guild.id)
        
        # Obtener datos específicos del usuario en este servidor
        guild_user_data = guild_data.get("members", {}).get(user_id, {"messages": 0, "commands": 0, "voice_time": 0})
        
        # Crear embed
        embed = discord.Embed(
            title=f"Estadísticas de {target_user.display_name}",
            color=target_user.color,
            description=f"Miembro desde {target_user.joined_at.strftime('%d/%m/%Y')}"
        )
        
        # Añadir campos principales (globales)
        embed.add_field(name="🌐 Mensajes Totales", value=f"{user_data['messages']:,}", inline=True)
        embed.add_field(name="🌐 Comandos Usados", value=f"{user_data['commands']:,}", inline=True)
        embed.add_field(name="🌐 Tiempo en Voz", value=f"{int(user_data['voice_time']):,} minutos", inline=True)
        
        # Añadir campos del servidor
        embed.add_field(name="📊 Mensajes en Servidor", value=f"{guild_user_data.get('messages', 0):,}", inline=True)
        embed.add_field(name="📊 Comandos en Servidor", value=f"{guild_user_data.get('commands', 0):,}", inline=True)
        embed.add_field(name="📊 Tiempo en Voz en Servidor", value=f"{int(guild_user_data.get('voice_time', 0)):,} minutos", inline=True)
        
        # Reacciones
        embed.add_field(name="Reacciones Añadidas", value=f"{user_data.get('reactions_added', 0):,}", inline=True)
        embed.add_field(name="Reacciones Recibidas", value=f"{user_data.get('reactions_received', 0):,}", inline=True)
        
        # Última actividad
        last_seen = datetime.datetime.fromtimestamp(user_data.get('last_seen', 0))
        embed.add_field(name="Última Vez Visto", value=f"{last_seen.strftime('%d/%m/%Y %H:%M')}", inline=True)
        
        # Posición en clasificaciones del servidor
        if guild_data.get("members"):
            sorted_by_messages = sorted(guild_data["members"].items(), key=lambda x: x[1].get("messages", 0), reverse=True)
            message_rank = next((i + 1 for i, (uid, _) in enumerate(sorted_by_messages) if uid == user_id), None)
            
            sorted_by_voice = sorted(guild_data["members"].items(), key=lambda x: x[1].get("voice_time", 0), reverse=True)
            voice_rank = next((i + 1 for i, (uid, _) in enumerate(sorted_by_voice) if uid == user_id), None)
            
            if message_rank:
                embed.add_field(name="Ranking de Mensajes", value=f"#{message_rank} de {len(guild_data['members'])}", inline=True)
            
            if voice_rank:
                embed.add_field(name="Ranking de Voz", value=f"#{voice_rank} de {len(guild_data['members'])}", inline=True)
        
        # Establecer thumbnail
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="globalstats", description="Muestra estadísticas globales del bot")
    async def globalstats(self, ctx):
        """Muestra estadísticas globales del bot en todos los servidores"""
        global_data = self.data["global"]
        
        # Calcular tiempo en línea
        start_timestamp = global_data.get("start_date", datetime.datetime.now().timestamp())
        start_date = datetime.datetime.fromtimestamp(start_timestamp)
        uptime = datetime.datetime.now() - start_date
        
        # Crear embed
        embed = discord.Embed(
            title="Estadísticas Globales del Bot",
            color=discord.Color.gold(),
            description=f"En línea desde {start_date.strftime('%d/%m/%Y')}\nTiempo en línea: {uptime.days} días, {uptime.seconds // 3600} horas"
        )
        
        # Añadir campos principales
        embed.add_field(name="Mensajes Procesados", value=f"{global_data['total_messages']:,}", inline=True)
        embed.add_field(name="Comandos Ejecutados", value=f"{global_data['commands_used']:,}", inline=True)
        embed.add_field(name="Tiempo en Canales de Voz", value=f"{int(global_data['voice_minutes']):,} minutos", inline=True)
        embed.add_field(name="Usuarios Unidos", value=f"{global_data['users_joined']:,}", inline=True)
        embed.add_field(name="Usuarios Salidos", value=f"{global_data['users_left']:,}", inline=True)
        
        # Información de servidores y usuarios
        guilds_count = len(self.bot.guilds)
        users_count = sum(g.member_count for g in self.bot.guilds)
        channels_count = sum(len(g.channels) for g in self.bot.guilds)
        
        embed.add_field(name="Servidores", value=str(guilds_count), inline=True)
        embed.add_field(name="Usuarios", value=f"{users_count:,}", inline=True)
        embed.add_field(name="Canales", value=str(channels_count), inline=True)
        
        # Estadísticas de hoy
        today_data = self.get_today_data()
        embed.add_field(name="Mensajes Hoy", value=f"{today_data['messages']:,}", inline=True)
        embed.add_field(name="Comandos Hoy", value=f"{today_data['commands']:,}", inline=True)
        embed.add_field(name="Usuarios Activos Hoy", value=f"{today_data['active_users']:,}", inline=True)
        
        # Establecer thumbnail con el avatar del bot
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="activitychart", description="Muestra un gráfico de actividad por hora")
    async def activitychart(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        """Muestra un gráfico de actividad por hora en el servidor o canal"""
        if not ctx.guild:
            await ctx.send("❌ Este comando solo puede ser usado en un servidor.")
            return
        
        if channel:
            # Gráfico de actividad de un canal específico
            channel_data = self.get_channel_data(channel.id)
            hourly_data = channel_data.get("hourly_activity", {})
            title = f"Actividad por Hora - #{channel.name}"
        else:
            # Gráfico de actividad del servidor
            guild_data = self.get_guild_data(ctx.guild.id)
            hourly_data = guild_data.get("hourly_activity", {})
            title = f"Actividad por Hora - {ctx.guild.name}"
        
        await self.send_hourly_activity_chart(ctx, hourly_data, title)
    
    async def send_hourly_activity_chart(self, ctx, hourly_data, title):
        """Crea y envía un gráfico de actividad por hora"""
        plt.figure(figsize=(10, 6))
        
        # Procesar los datos
        hours = range(24)
        values = [hourly_data.get(str(hour), 0) for hour in hours]
        
        # Crear el gráfico
        plt.bar(hours, values, color='blue', alpha=0.7)
        plt.title(title)
        plt.xlabel('Hora del día')
        plt.ylabel('Mensajes')
        plt.xticks(hours, [f"{h:02d}:00" for h in hours], rotation=45)
        plt.tight_layout()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Guardar el gráfico en un buffer
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        
        # Enviar el gráfico
        file = discord.File(buf, 'activity_chart.png')
        await ctx.send(file=file)
    
    @commands.hybrid_command(name="cmdstats", description="Muestra estadísticas de comandos")
    async def cmdstats(self, ctx):
        """Muestra estadísticas detalladas de los comandos más usados"""
        if not ctx.guild:
            await ctx.send("❌ Este comando solo puede ser usado en un servidor.")
            return
        
        guild_data = self.get_guild_data(ctx.guild.id)
        cmd_stats = guild_data.get("commands_used", {})
        
        if not cmd_stats:
            await ctx.send("❌ No hay estadísticas de comandos disponibles para este servidor.")
            return
        
        # Ordenar comandos por uso
        sorted_cmds = sorted(cmd_stats.items(), key=lambda x: x[1], reverse=True)
        
        # Preparar el gráfico para los 10 comandos más usados
        top_cmds = sorted_cmds[:10]
        
        plt.figure(figsize=(10, 6))
        cmd_names = [cmd for cmd, _ in top_cmds]
        cmd_counts = [count for _, count in top_cmds]
        
        # Crear gráfico horizontal
        plt.barh(cmd_names, cmd_counts, color='green', alpha=0.7)
        plt.title(f"Comandos Más Usados - {ctx.guild.name}")
        plt.xlabel('Veces usado')
        plt.tight_layout()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Guardar el gráfico en un buffer
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        
        # Crear embed con estadísticas textuales
        embed = discord.Embed(
            title=f"Estadísticas de Comandos - {ctx.guild.name}",
            color=discord.Color.green()
        )
        
        # Total de comandos usados
        total_cmds = sum(cmd_stats.values())
        embed.add_field(name="Comandos Totales Usados", value=f"{total_cmds:,}", inline=False)
        
        # Lista de los 15 comandos más usados
        cmd_list = "\n".join([f"• **/{cmd}**: {count:,} usos ({count/total_cmds*100:.1f}%)" for cmd, count in sorted_cmds[:15]])
        embed.add_field(name="Comandos Más Populares", value=cmd_list, inline=False)
        
        # Enviar el gráfico y el embed
        file = discord.File(buf, 'cmd_stats.png')
        embed.set_image(url="attachment://cmd_stats.png")
        
        await ctx.send(embed=embed, file=file)
    
    @commands.hybrid_command(name="topchannels", description="Muestra los canales más activos")
    async def topchannels(self, ctx):
        """Muestra los canales más activos del servidor"""
        if not ctx.guild:
            await ctx.send("❌ Este comando solo puede ser usado en un servidor.")
            return
        
        guild_data = self.get_guild_data(ctx.guild.id)
        channel_data = guild_data.get("channels", {})
        
        if not channel_data:
            await ctx.send("❌ No hay estadísticas de canales disponibles para este servidor.")
            return
        
        # Obtener datos de mensajes por canal y filtrar canales que ya no existen
        channel_messages = []
        for channel_id, data in channel_data.items():
            channel = ctx.guild.get_channel(int(channel_id))
            if channel and isinstance(channel, discord.TextChannel):
                channel_messages.append((channel, data.get("messages", 0)))
        
        # Ordenar por número de mensajes
        sorted_channels = sorted(channel_messages, key=lambda x: x[1], reverse=True)
        
        # Crear embed
        embed = discord.Embed(
            title=f"Canales Más Activos - {ctx.guild.name}",
            color=discord.Color.blue()
        )
        
        # Total de mensajes en el servidor
        total_messages = guild_data.get("messages", 0)
        embed.description = f"Total de mensajes en el servidor: {total_messages:,}"
        
        # Mostrar los 15 canales más activos
        for i, (channel, messages) in enumerate(sorted_channels[:15], 1):
            percent = (messages / total_messages * 100) if total_messages > 0 else 0
            embed.add_field(
                name=f"{i}. #{channel.name}",
                value=f"{messages:,} mensajes ({percent:.1f}%)",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="dailystats", description="Muestra estadísticas diarias")
    async def dailystats(self, ctx):
        """Muestra las estadísticas de actividad del día actual"""
        today_data = self.get_today_data()
        
        # Crear embed
        embed = discord.Embed(
            title=f"Estadísticas de Hoy ({datetime.datetime.now().strftime('%d/%m/%Y')})",
            color=discord.Color.gold()
        )
        
        # Añadir campos principales
        embed.add_field(name="Mensajes", value=f"{today_data['messages']:,}", inline=True)
        embed.add_field(name="Comandos", value=f"{today_data['commands']:,}", inline=True)
        embed.add_field(name="Usuarios Activos", value=f"{today_data['active_users']:,}", inline=True)
        embed.add_field(name="Nuevos Miembros", value=f"{today_data['joins']:,}", inline=True)
        embed.add_field(name="Miembros Salidos", value=f"{today_data['leaves']:,}", inline=True)
        embed.add_field(name="Reacciones", value=f"{today_data['reactions']:,}", inline=True)
        embed.add_field(name="Tiempo en Voz", value=f"{int(today_data['voice_time']):,} minutos", inline=True)
        
        # Calcular promedio de mensajes por usuario activo
        if today_data['active_users'] > 0:
            avg_messages = today_data['messages'] / today_data['active_users']
            embed.add_field(name="Promedio Mensajes/Usuario", value=f"{avg_messages:.1f}", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="memberstats", description="Muestra estadísticas de miembros")
    async def memberstats(self, ctx):
        """Muestra estadísticas detalladas de los miembros del servidor"""
        if not ctx.guild:
            await ctx.send("❌ Este comando solo puede ser usado en un servidor.")
            return
        
        # Reunir datos sobre roles
        role_counts = Counter()
        bot_count = 0
        human_count = 0
        online_count = 0
        
        for member in ctx.guild.members:
            if member.bot:
                bot_count += 1
            else:
                human_count += 1
                
                # Contar miembros online
                if member.status != discord.Status.offline:
                    online_count += 1
                
            # Contar roles
            for role in member.roles:
                if role.name != "@everyone":
                    role_counts[role.name] += 1
        
        # Crear embed
        embed = discord.Embed(
            title=f"Estadísticas de Miembros - {ctx.guild.name}",
            color=discord.Color.blue()
        )
        
        # Información general
        embed.add_field(name="Total Miembros", value=str(ctx.guild.member_count), inline=True)
        embed.add_field(name="Humanos", value=str(human_count), inline=True)
        embed.add_field(name="Bots", value=str(bot_count), inline=True)
        embed.add_field(name="En línea", value=str(online_count), inline=True)
        embed.add_field(name="Desconectados", value=str(human_count - online_count), inline=True)
        
        # Datos del servidor
        guild_data = self.get_guild_data(ctx.guild.id)
        embed.add_field(name="Miembros Unidos", value=f"{guild_data.get('joins', 0):,}", inline=True)
        embed.add_field(name="Miembros Salidos", value=f"{guild_data.get('leaves', 0):,}", inline=True)
        
        # Tasa de retención
        if guild_data.get('joins', 0) > 0:
            retention = (guild_data.get('joins', 0) - guild_data.get('leaves', 0)) / guild_data.get('joins', 0) * 100
            embed.add_field(name="Tasa de Retención", value=f"{max(0, retention):.1f}%", inline=True)
        
        # Roles más comunes
        top_roles = role_counts.most_common(10)
        if top_roles:
            roles_text = "\n".join([f"• **{role}**: {count} miembros" for role, count in top_roles])
            embed.add_field(name="Roles Más Comunes", value=roles_text, inline=False)
        
        # Establecer thumbnail
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Statistics(bot))