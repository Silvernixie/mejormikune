import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
import datetime
import os
import typing
import random
import uuid
from enum import Enum

class TicketStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"

class Tickets(commands.Cog):
    """Sistema de tickets para soporte y ayuda"""
    
    def __init__(self, bot):
        self.bot = bot
        self.tickets_file = "data/tickets.json"
        self.tickets_data = self.load_data()
        
        # Verificar si existen las carpetas necesarias
        tickets_dir = os.path.join("data", "ticket_archives")
        if not os.path.exists(tickets_dir):
            os.makedirs(tickets_dir)
    
    def load_data(self):
        """Cargar datos de tickets desde el archivo JSON"""
        if os.path.exists(self.tickets_file):
            try:
                with open(self.tickets_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error al cargar tickets: {e}")
                return self.get_default_data()
        return self.get_default_data()
    
    def get_default_data(self):
        """Crear estructura de datos predeterminada para tickets"""
        return {
            "settings": {},
            "tickets": {},
            "user_tickets": {},
            "categories": {
                "general": {
                    "name": "Soporte General",
                    "description": "Ayuda con cualquier consulta general",
                    "color": "blue",
                    "emoji": "❓"
                },
                "technical": {
                    "name": "Soporte Técnico",
                    "description": "Problemas técnicos con el bot o el servidor",
                    "color": "red",
                    "emoji": "🔧"
                },
                "report": {
                    "name": "Reportes",
                    "description": "Reportar usuarios o comportamientos",
                    "color": "orange",
                    "emoji": "🚨"
                }
            },
            "counters": {}
        }
    
    def save_data(self):
        """Guardar datos de tickets en el archivo JSON"""
        try:
            with open(self.tickets_file, "w", encoding="utf-8") as f:
                json.dump(self.tickets_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar tickets: {e}")
    
    def get_color(self, color_name):
        """Convertir nombres de colores a objetos de color de Discord"""
        colors = {
            "blue": discord.Color.blue(),
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "orange": discord.Color.orange(),
            "purple": discord.Color.purple(),
            "gold": discord.Color.gold(),
            "teal": discord.Color.teal()
        }
        return colors.get(color_name.lower(), discord.Color.blurple())
    
    def get_guild_settings(self, guild_id):
        """Obtener la configuración de tickets para un servidor específico"""
        guild_id = str(guild_id)
        if guild_id not in self.tickets_data["settings"]:
            # Establecer valores predeterminados
            self.tickets_data["settings"][guild_id] = {
                "ticket_channel_id": None,
                "support_role_id": None,
                "admin_role_id": None,
                "transcript_channel_id": None,
                "enabled_categories": ["general", "technical", "report"],
                "ticket_prefix": "ticket",
                "auto_close_inactive": 24,  # Horas antes de notificar inactividad
                "auto_archive": True
            }
            self.save_data()
        
        return self.tickets_data["settings"][guild_id]
    
    def get_guild_counter(self, guild_id):
        """Obtener el contador de tickets para un servidor"""
        guild_id = str(guild_id)
        if guild_id not in self.tickets_data["counters"]:
            self.tickets_data["counters"][guild_id] = 0
        
        self.tickets_data["counters"][guild_id] += 1
        self.save_data()
        return self.tickets_data["counters"][guild_id]
    
    def get_ticket_data(self, channel_id):
        """Obtener datos de un ticket por su ID de canal"""
        channel_id = str(channel_id)
        return self.tickets_data["tickets"].get(channel_id)
    
    def create_ticket_id(self, guild_id):
        """Crear un ID de ticket único"""
        counter = self.get_guild_counter(guild_id)
        settings = self.get_guild_settings(guild_id)
        prefix = settings.get("ticket_prefix", "ticket")
        return f"{prefix}-{counter:04d}"
    
    async def create_transcript(self, channel, ticket_data):
        """Crear una transcripción del ticket"""
        try:
            # Crear un archivo con el historial del ticket
            transcript_file = os.path.join("data", "ticket_archives", f"{ticket_data['ticket_id']}.txt")
            
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(f"Ticket: {ticket_data['ticket_id']}\n")
                f.write(f"Categoría: {ticket_data['category']}\n")
                f.write(f"Abierto por: {ticket_data['user_name']} (ID: {ticket_data['user_id']})\n")
                f.write(f"Abierto el: {datetime.datetime.fromtimestamp(ticket_data['opened_at']).strftime('%d/%m/%Y %H:%M:%S')}\n")
                
                if ticket_data["status"] == TicketStatus.CLOSED.value:
                    f.write(f"Cerrado por: {ticket_data.get('closed_by_name', 'N/A')}\n")
                    f.write(f"Cerrado el: {datetime.datetime.fromtimestamp(ticket_data.get('closed_at', 0)).strftime('%d/%m/%Y %H:%M:%S')}\n")
                
                f.write(f"Motivo: {ticket_data['reason']}\n\n")
                f.write("=== Historial de mensajes ===\n\n")
                
                async for message in channel.history(limit=500, oldest_first=True):
                    # Formato del tiempo
                    timestamp = message.created_at.strftime("%d/%m/%Y %H:%M:%S")
                    
                    # Ignorar mensajes del bot que son las instrucciones o paneles
                    if message.author.bot and len(message.embeds) > 0:
                        continue
                    
                    # Agregar el mensaje a la transcripción
                    f.write(f"[{timestamp}] {message.author.name}: {message.content}\n")
                    
                    # Incluir archivos adjuntos
                    for attachment in message.attachments:
                        f.write(f"[{timestamp}] {message.author.name} adjuntó: {attachment.url}\n")
            
            # Devolver la ruta al archivo de transcripción
            return transcript_file
            
        except Exception as e:
            print(f"Error al crear transcripción: {e}")
            return None
    
    @commands.hybrid_group(name="ticket", description="Comandos del sistema de tickets")
    async def ticket(self, ctx):
        """Grupo de comandos para el sistema de tickets"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Sistema de Tickets",
                description="Usa `/ticket help` para ver los comandos disponibles.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
    
    @ticket.command(name="help", description="Muestra ayuda sobre el sistema de tickets")
    async def ticket_help(self, ctx):
        """Muestra la ayuda del sistema de tickets"""
        embed = discord.Embed(
            title="Ayuda del Sistema de Tickets",
            description="Los siguientes comandos están disponibles:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Para usuarios",
            value="`/ticket create` - Crear un nuevo ticket\n"
                  "`/ticket list` - Listar tus tickets activos\n"
                  "`/ticket close` - Cerrar un ticket (solo en canal de ticket)",
            inline=False
        )
        
        embed.add_field(
            name="Para personal de soporte",
            value="`/ticket add @usuario` - Añadir usuario a un ticket\n"
                  "`/ticket remove @usuario` - Eliminar usuario de un ticket\n"
                  "`/ticket rename nuevo_nombre` - Renombrar un ticket",
            inline=False
        )
        
        embed.add_field(
            name="Para administradores",
            value="`/ticket setup` - Configurar el sistema de tickets\n"
                  "`/ticket categories` - Gestionar categorías de tickets\n"
                  "`/ticket stats` - Ver estadísticas de tickets",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @ticket.command(name="setup", description="Configurar el sistema de tickets para el servidor")
    @commands.has_permissions(administrator=True)
    async def ticket_setup(
        self, ctx,
        ticket_channel: discord.TextChannel = None,
        support_role: discord.Role = None,
        admin_role: discord.Role = None,
        transcript_channel: discord.TextChannel = None
    ):
        """Configurar el sistema de tickets para el servidor"""
        # Actualizar configuración
        settings = self.get_guild_settings(ctx.guild.id)
        
        if ticket_channel:
            settings["ticket_channel_id"] = str(ticket_channel.id)
        
        if support_role:
            settings["support_role_id"] = str(support_role.id)
        
        if admin_role:
            settings["admin_role_id"] = str(admin_role.id)
        
        if transcript_channel:
            settings["transcript_channel_id"] = str(transcript_channel.id)
        
        # Guardar cambios
        self.save_data()
        
        # Responder al usuario
        embed = discord.Embed(
            title="Configuración de Tickets Actualizada",
            description="La configuración del sistema de tickets ha sido actualizada.",
            color=discord.Color.green()
        )
        
        # Mostrar configuración actual
        ticket_channel_id = settings.get("ticket_channel_id")
        support_role_id = settings.get("support_role_id")
        admin_role_id = settings.get("admin_role_id")
        transcript_channel_id = settings.get("transcript_channel_id")
        
        embed.add_field(
            name="Canal de Tickets",
            value=f"<#{ticket_channel_id}>" if ticket_channel_id else "No configurado",
            inline=True
        )
        
        embed.add_field(
            name="Rol de Soporte",
            value=f"<@&{support_role_id}>" if support_role_id else "No configurado",
            inline=True
        )
        
        embed.add_field(
            name="Rol de Administrador",
            value=f"<@&{admin_role_id}>" if admin_role_id else "No configurado",
            inline=True
        )
        
        embed.add_field(
            name="Canal de Transcripciones",
            value=f"<#{transcript_channel_id}>" if transcript_channel_id else "No configurado",
            inline=True
        )
        
        # Si el canal de tickets está configurado, ofrecer crear panel
        if ticket_channel_id:
            embed.add_field(
                name="Siguiente Paso",
                value="Usa `/ticket panel` para crear un panel de tickets en el canal configurado.",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @ticket.command(name="panel", description="Crear un panel de tickets en el canal configurado")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx):
        """Crear un panel de tickets en el canal configurado"""
        settings = self.get_guild_settings(ctx.guild.id)
        ticket_channel_id = settings.get("ticket_channel_id")
        
        if not ticket_channel_id:
            await ctx.send("❌ Primero debes configurar un canal de tickets con `/ticket setup`.")
            return
        
        # Obtener canal de tickets
        ticket_channel = ctx.guild.get_channel(int(ticket_channel_id))
        if not ticket_channel:
            await ctx.send("❌ El canal de tickets configurado no existe o no puedo acceder a él.")
            return
        
        # Crear embed del panel
        embed = discord.Embed(
            title="Sistema de Soporte y Tickets",
            description="¡Bienvenido al sistema de soporte! Para crear un ticket, selecciona una categoría haciendo clic en el botón correspondiente a continuación.",
            color=discord.Color.blue()
        )
        
        # Agregar información sobre categorías disponibles
        categories_text = ""
        for category_id, category_data in self.tickets_data["categories"].items():
            if category_id in settings.get("enabled_categories", []):
                emoji = category_data.get("emoji", "❓")
                name = category_data.get("name", "Categoría")
                description = category_data.get("description", "Sin descripción")
                categories_text += f"{emoji} **{name}**: {description}\n\n"
        
        if categories_text:
            embed.add_field(name="Categorías Disponibles", value=categories_text, inline=False)
        
        # Agregar instrucciones adicionales
        embed.add_field(
            name="Instrucciones",
            value="1. Selecciona la categoría que mejor se adapte a tu consulta.\n"
                  "2. Proporciona detalles claros sobre tu problema.\n"
                  "3. El personal de soporte te atenderá lo antes posible.\n"
                  "4. Ten paciencia y respeta a los miembros del equipo.",
            inline=False
        )
        
        embed.set_footer(text="Sistema de Tickets • Creado con ❤️")
        
        # Crear botones para categorías
        view = discord.ui.View(timeout=None)
        
        for category_id, category_data in self.tickets_data["categories"].items():
            if category_id in settings.get("enabled_categories", []):
                emoji = category_data.get("emoji", "❓")
                name = category_data.get("name", "Categoría")
                
                # Crear botón para esta categoría
                button = discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label=name,
                    emoji=emoji,
                    custom_id=f"ticket_create_{category_id}"
                )
                view.add_item(button)
        
        # Enviar el panel al canal
        await ticket_channel.send(embed=embed, view=view)
        
        # Confirmar al usuario
        await ctx.send("✅ Panel de tickets creado correctamente.")
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        """Manejar interacciones con botones y menús"""
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = interaction.data.get("custom_id", "")
        
        # Verificar si es una interacción de tickets
        if custom_id.startswith("ticket_create_"):
            # Extraer categoría
            category = custom_id.replace("ticket_create_", "")
            
            # Mostrar modal para crear ticket
            await self.show_ticket_modal(interaction, category)
        
        elif custom_id == "ticket_close":
            # Cerrar ticket
            await self.close_ticket_button(interaction)
        
        elif custom_id == "ticket_transcript":
            # Generar transcripción
            await self.generate_transcript_button(interaction)
    
    async def show_ticket_modal(self, interaction, category):
        """Mostrar modal para crear un ticket"""
        # Verificar si la categoría existe
        if category not in self.tickets_data["categories"]:
            await interaction.response.send_message("❌ Categoría de ticket inválida.", ephemeral=True)
            return
        
        category_data = self.tickets_data["categories"][category]
        
        # Crear modal para recopilar la razón del ticket
        modal = discord.ui.Modal(title=f"Crear Ticket - {category_data['name']}")
        
        # Agregar campos al modal
        reason_input = discord.ui.TextInput(
            label="Explica tu problema o consulta",
            placeholder="Proporciona todos los detalles posibles para que podamos ayudarte mejor...",
            style=discord.TextStyle.paragraph,
            required=True,
            min_length=10,
            max_length=1000
        )
        modal.add_item(reason_input)
        
        # Definir el callback
        async def modal_callback(interaction):
            # Obtener razón
            reason = reason_input.value
            
            # Crear el ticket
            await self.create_ticket(interaction, category, reason)
        
        modal.on_submit = modal_callback
        
        # Mostrar el modal
        await interaction.response.send_modal(modal)
    
    async def create_ticket(self, interaction, category, reason):
        """Crear un nuevo ticket"""
        guild = interaction.guild
        user = interaction.user
        
        # Verificar si el usuario ya tiene tickets abiertos
        user_id = str(user.id)
        if user_id in self.tickets_data["user_tickets"]:
            active_tickets = [ticket_id for ticket_id in self.tickets_data["user_tickets"][user_id] 
                            if self.tickets_data["tickets"].get(ticket_id, {}).get("status") == TicketStatus.OPEN.value]
            
            # Limitar a 3 tickets activos por usuario
            if len(active_tickets) >= 3:
                await interaction.response.send_message(
                    "❌ Tienes demasiados tickets abiertos (máximo 3). Por favor, cierra alguno antes de crear uno nuevo.",
                    ephemeral=True
                )
                return
        
        # Obtener categoría
        category_data = self.tickets_data["categories"][category]
        
        # Obtener configuración del servidor
        settings = self.get_guild_settings(guild.id)
        
        # Generar ID de ticket
        ticket_id = self.create_ticket_id(guild.id)
        
        # Crear el canal del ticket
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(
                read_messages=True, 
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True
            )
        }
        
        # Añadir permisos para rol de soporte
        if settings.get("support_role_id"):
            support_role = guild.get_role(int(settings["support_role_id"]))
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True,
                    attach_files=True,
                    embed_links=True,
                    read_message_history=True,
                    manage_messages=True
                )
        
        # Añadir permisos para rol de admin
        if settings.get("admin_role_id"):
            admin_role = guild.get_role(int(settings["admin_role_id"]))
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True,
                    attach_files=True,
                    embed_links=True,
                    read_message_history=True,
                    manage_messages=True,
                    manage_channels=True
                )
        
        # Crear el canal
        try:
            channel_name = f"{ticket_id.lower()}-{user.name.lower()}"
            channel = await guild.create_text_channel(
                name=channel_name,
                topic=f"Ticket de {user.name} | Categoría: {category_data['name']} | Razón: {reason[:50]}...",
                overwrites=overwrites
            )
            
            # Crear mensaje de bienvenida en el canal
            embed = discord.Embed(
                title=f"Ticket: {ticket_id}",
                description=f"Gracias por crear un ticket, {user.mention}. El equipo de soporte te atenderá lo antes posible.",
                color=self.get_color(category_data.get("color", "blue"))
            )
            
            embed.add_field(name="Categoría", value=category_data["name"], inline=True)
            embed.add_field(name="Creado por", value=user.mention, inline=True)
            embed.add_field(name="Razón", value=reason, inline=False)
            
            # Crear botones
            view = discord.ui.View(timeout=None)
            
            close_button = discord.ui.Button(
                style=discord.ButtonStyle.red,
                label="Cerrar Ticket",
                emoji="🔒",
                custom_id="ticket_close"
            )
            view.add_item(close_button)
            
            transcript_button = discord.ui.Button(
                style=discord.ButtonStyle.grey,
                label="Generar Transcripción",
                emoji="📝",
                custom_id="ticket_transcript"
            )
            view.add_item(transcript_button)
            
            welcome_message = await channel.send(embed=embed, view=view)
            
            # Mencionar al usuario y al rol de soporte
            mention_text = f"{user.mention}"
            
            if settings.get("support_role_id"):
                mention_text += f" <@&{settings['support_role_id']}>"
            
            await channel.send(mention_text)
            
            # Almacenar datos del ticket
            channel_id = str(channel.id)
            ticket_data = {
                "ticket_id": ticket_id,
                "channel_id": channel_id,
                "guild_id": str(guild.id),
                "user_id": user_id,
                "user_name": user.name,
                "category": category,
                "reason": reason,
                "status": TicketStatus.OPEN.value,
                "opened_at": datetime.datetime.now().timestamp(),
                "closed_at": None,
                "closed_by": None,
                "closed_by_name": None,
                "participants": [user_id],
                "welcome_message_id": str(welcome_message.id)
            }
            
            # Guardar el ticket en la base de datos
            self.tickets_data["tickets"][channel_id] = ticket_data
            
            # Actualizar la lista de tickets del usuario
            if user_id not in self.tickets_data["user_tickets"]:
                self.tickets_data["user_tickets"][user_id] = []
            
            self.tickets_data["user_tickets"][user_id].append(channel_id)
            
            # Guardar datos
            self.save_data()
            
            # Responder a la interacción
            await interaction.response.send_message(
                f"✅ Tu ticket ha sido creado: {channel.mention}",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error al crear el ticket: {str(e)}",
                ephemeral=True
            )
            print(f"Error creating ticket: {e}")
    
    async def close_ticket_button(self, interaction):
        """Cerrar un ticket usando el botón"""
        channel = interaction.channel
        
        # Verificar si es un canal de ticket
        ticket_data = self.get_ticket_data(channel.id)
        if not ticket_data:
            await interaction.response.send_message("❌ Este no es un canal de ticket válido.", ephemeral=True)
            return
        
        # Verificar si el ticket ya está cerrado
        if ticket_data["status"] != TicketStatus.OPEN.value:
            await interaction.response.send_message("❌ Este ticket ya está cerrado.", ephemeral=True)
            return
        
        # Comprobar permisos
        user = interaction.user
        user_id = str(user.id)
        
        # Permitir cerrar el ticket a: creador, miembros del rol de soporte o administradores
        settings = self.get_guild_settings(interaction.guild.id)
        
        is_creator = user_id == ticket_data["user_id"]
        is_support = False
        is_admin = False
        
        # Verificar roles
        if settings.get("support_role_id") and interaction.guild.get_role(int(settings["support_role_id"])) in user.roles:
            is_support = True
        
        if settings.get("admin_role_id") and interaction.guild.get_role(int(settings["admin_role_id"])) in user.roles:
            is_admin = True
        
        if not (is_creator or is_support or is_admin):
            await interaction.response.send_message("❌ No tienes permisos para cerrar este ticket.", ephemeral=True)
            return
        
        # Confirmar cierre
        embed = discord.Embed(
            title="Confirmar Cierre de Ticket",
            description="¿Estás seguro de que deseas cerrar este ticket? Se generará una transcripción y el canal será eliminado en 24 horas.",
            color=discord.Color.orange()
        )
        
        # Crear botones de confirmación
        view = discord.ui.View(timeout=60)
        
        async def confirm_callback(confirm_interaction):
            if confirm_interaction.user.id != interaction.user.id:
                await confirm_interaction.response.send_message("❌ Solo la persona que inició el cierre puede confirmarlo.", ephemeral=True)
                return
            
            await confirm_interaction.response.defer()
            await self.close_ticket(channel, ticket_data, user)
            for item in view.children:
                item.disabled = True
            await confirm_interaction.message.edit(view=view)
        
        async def cancel_callback(cancel_interaction):
            if cancel_interaction.user.id != interaction.user.id:
                await cancel_interaction.response.send_message("❌ Solo la persona que inició el cierre puede cancelarlo.", ephemeral=True)
                return
            
            await cancel_interaction.response.defer()
            for item in view.children:
                item.disabled = True
            
            await cancel_interaction.message.edit(
                content="✅ Cierre de ticket cancelado.",
                embed=None,
                view=view
            )
        
        # Añadir botones al view
        confirm_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Confirmar Cierre")
        confirm_button.callback = confirm_callback
        view.add_item(confirm_button)
        
        cancel_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Cancelar")
        cancel_button.callback = cancel_callback
        view.add_item(cancel_button)
        
        # Responder a la interacción
        await interaction.response.send_message(embed=embed, view=view)
    
    async def close_ticket(self, channel, ticket_data, closed_by):
        """Cerrar un ticket"""
        try:
            # Actualizar datos del ticket
            ticket_data["status"] = TicketStatus.CLOSED.value
            ticket_data["closed_at"] = datetime.datetime.now().timestamp()
            ticket_data["closed_by"] = str(closed_by.id)
            ticket_data["closed_by_name"] = closed_by.name
            
            self.save_data()
            
            # Generar transcripción
            transcript_file = await self.create_transcript(channel, ticket_data)
            
            # Enviar mensaje de cierre
            embed = discord.Embed(
                title="Ticket Cerrado",
                description=f"Este ticket ha sido cerrado por {closed_by.mention}. El canal será eliminado en 24 horas.",
                color=discord.Color.red()
            )
            
            await channel.send(embed=embed)
            
            # Enviar transcripción al canal de transcripciones si está configurado
            settings = self.get_guild_settings(channel.guild.id)
            transcript_channel_id = settings.get("transcript_channel_id")
            
            if transcript_channel_id and transcript_file:
                transcript_channel = channel.guild.get_channel(int(transcript_channel_id))
                
                if transcript_channel:
                    # Crear mensaje con la transcripción
                    transcript_embed = discord.Embed(
                        title=f"Transcripción: {ticket_data['ticket_id']}",
                        description=f"Ticket cerrado por {closed_by.name}",
                        color=discord.Color.blue()
                    )
                    
                    transcript_embed.add_field(name="Categoría", value=self.tickets_data["categories"][ticket_data["category"]]["name"], inline=True)
                    transcript_embed.add_field(name="Usuario", value=f"<@{ticket_data['user_id']}> ({ticket_data['user_name']})", inline=True)
                    transcript_embed.add_field(name="Motivo", value=ticket_data["reason"], inline=False)
                    
                    created_at = datetime.datetime.fromtimestamp(ticket_data["opened_at"])
                    closed_at = datetime.datetime.fromtimestamp(ticket_data["closed_at"])
                    duration = closed_at - created_at
                    
                    transcript_embed.add_field(name="Abierto", value=created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
                    transcript_embed.add_field(name="Cerrado", value=closed_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
                    transcript_embed.add_field(name="Duración", value=str(duration).split(".")[0], inline=True)
                    
                    # Enviar archivo de transcripción
                    with open(transcript_file, "rb") as f:
                        file = discord.File(f, filename=f"{ticket_data['ticket_id']}.txt")
                        await transcript_channel.send(embed=transcript_embed, file=file)
            
            # Modificar permisos para evitar que se envíen nuevos mensajes
            for target, overwrite in channel.overwrites.items():
                if isinstance(target, discord.Member) or isinstance(target, discord.Role):
                    overwrite.send_messages = False
                    await channel.set_permissions(target, overwrite=overwrite)
            
            # Programar eliminación del canal en 24 horas
            self.bot.loop.create_task(self.delete_ticket_channel(channel, 86400))  # 24 horas
            
        except Exception as e:
            print(f"Error closing ticket: {e}")
            await channel.send(f"❌ Error al cerrar el ticket: {str(e)}")
    
    async def delete_ticket_channel(self, channel, delay):
        """Eliminar el canal del ticket después de un retraso"""
        await asyncio.sleep(delay)
        try:
            await channel.delete(reason="Ticket cerrado y archivado")
        except Exception as e:
            print(f"Error deleting ticket channel: {e}")
    
    async def generate_transcript_button(self, interaction):
        """Generar transcripción desde el botón"""
        channel = interaction.channel
        
        # Verificar si es un canal de ticket
        ticket_data = self.get_ticket_data(channel.id)
        if not ticket_data:
            await interaction.response.send_message("❌ Este no es un canal de ticket válido.", ephemeral=True)
            return
        
        # Comprobar permisos
        user = interaction.user
        settings = self.get_guild_settings(interaction.guild.id)
        
        is_creator = str(user.id) == ticket_data["user_id"]
        is_support = False
        is_admin = False
        
        # Verificar roles
        if settings.get("support_role_id") and interaction.guild.get_role(int(settings["support_role_id"])) in user.roles:
            is_support = True
        
        if settings.get("admin_role_id") and interaction.guild.get_role(int(settings["admin_role_id"])) in user.roles:
            is_admin = True
        
        if not (is_creator or is_support or is_admin):
            await interaction.response.send_message("❌ No tienes permisos para generar transcripciones.", ephemeral=True)
            return
        
        # Responder a la interacción
        await interaction.response.defer(ephemeral=True)
        
        # Generar transcripción
        transcript_file = await self.create_transcript(channel, ticket_data)
        
        if transcript_file:
            # Enviar el archivo al usuario
            with open(transcript_file, "rb") as f:
                file = discord.File(f, filename=f"{ticket_data['ticket_id']}.txt")
                await interaction.followup.send("✅ Aquí tienes la transcripción del ticket:", file=file, ephemeral=True)
        else:
            await interaction.followup.send("❌ Error al generar la transcripción.", ephemeral=True)
    
    @ticket.command(name="create", description="Crear un nuevo ticket manualmente")
    @app_commands.describe(
        category="La categoría del ticket",
        reason="La razón o descripción de tu problema"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="Soporte General", value="general"),
        app_commands.Choice(name="Soporte Técnico", value="technical"),
        app_commands.Choice(name="Reportes", value="report")
    ])
    async def ticket_create(self, ctx, category: str, *, reason: str):
        """Crear un nuevo ticket manualmente"""
        await ctx.defer(ephemeral=True)
        
        # Verificar categoría
        if category not in self.tickets_data["categories"]:
            await ctx.send("❌ Categoría inválida.", ephemeral=True)
            return
        
        # Crear ticket
        await self.create_ticket(ctx.interaction, category, reason)
    
    @ticket.command(name="close", description="Cerrar un ticket actual")
    async def ticket_close(self, ctx, *, reason: typing.Optional[str] = "No se proporcionó motivo"):
        """Cerrar un ticket actual"""
        channel = ctx.channel
        
        # Verificar si es un canal de ticket
        ticket_data = self.get_ticket_data(channel.id)
        if not ticket_data:
            await ctx.send("❌ Este comando solo puede usarse en un canal de ticket.", ephemeral=True)
            return
        
        # Verificar si el ticket ya está cerrado
        if ticket_data["status"] != TicketStatus.OPEN.value:
            await ctx.send("❌ Este ticket ya está cerrado.", ephemeral=True)
            return
        
        # Comprobar permisos
        user = ctx.author
        user_id = str(user.id)
        
        # Permitir cerrar el ticket a: creador, miembros del rol de soporte o administradores
        settings = self.get_guild_settings(ctx.guild.id)
        
        is_creator = user_id == ticket_data["user_id"]
        is_support = False
        is_admin = False
        
        # Verificar roles
        if settings.get("support_role_id") and ctx.guild.get_role(int(settings["support_role_id"])) in user.roles:
            is_support = True
        
        if settings.get("admin_role_id") and ctx.guild.get_role(int(settings["admin_role_id"])) in user.roles:
            is_admin = True
        
        if not (is_creator or is_support or is_admin):
            await ctx.send("❌ No tienes permisos para cerrar este ticket.", ephemeral=True)
            return
        
        # Cerrar el ticket
        await ctx.send("🔄 Cerrando ticket...")
        await self.close_ticket(channel, ticket_data, user)
    
    @ticket.command(name="add", description="Añadir un usuario a un ticket")
    @app_commands.describe(user="El usuario a añadir al ticket")
    async def ticket_add(self, ctx, user: discord.Member):
        """Añadir un usuario a un ticket"""
        channel = ctx.channel
        
        # Verificar si es un canal de ticket
        ticket_data = self.get_ticket_data(channel.id)
        if not ticket_data:
            await ctx.send("❌ Este comando solo puede usarse en un canal de ticket.", ephemeral=True)
            return
        
        # Verificar si el ticket está abierto
        if ticket_data["status"] != TicketStatus.OPEN.value:
            await ctx.send("❌ No se pueden añadir usuarios a un ticket cerrado.", ephemeral=True)
            return
        
        # Comprobar permisos
        author = ctx.author
        settings = self.get_guild_settings(ctx.guild.id)
        
        is_creator = str(author.id) == ticket_data["user_id"]
        is_support = False
        is_admin = False
        
        # Verificar roles
        if settings.get("support_role_id") and ctx.guild.get_role(int(settings["support_role_id"])) in author.roles:
            is_support = True
        
        if settings.get("admin_role_id") and ctx.guild.get_role(int(settings["admin_role_id"])) in author.roles:
            is_admin = True
        
        if not (is_creator or is_support or is_admin):
            await ctx.send("❌ No tienes permisos para añadir usuarios a este ticket.", ephemeral=True)
            return
        
        # Verificar si el usuario ya tiene acceso
        if str(user.id) in ticket_data["participants"]:
            await ctx.send(f"❌ {user.mention} ya tiene acceso a este ticket.", ephemeral=True)
            return
        
        # Añadir permiso al usuario
        try:
            await channel.set_permissions(
                user,
                read_messages=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True
            )
            
            # Actualizar lista de participantes
            ticket_data["participants"].append(str(user.id))
            self.save_data()
            
            # Confirmar
            await ctx.send(f"✅ {user.mention} ha sido añadido al ticket.")
            
        except Exception as e:
            await ctx.send(f"❌ Error al añadir usuario: {str(e)}", ephemeral=True)
    
    @ticket.command(name="remove", description="Eliminar un usuario de un ticket")
    @app_commands.describe(user="El usuario a eliminar del ticket")
    async def ticket_remove(self, ctx, user: discord.Member):
        """Eliminar un usuario de un ticket"""
        channel = ctx.channel
        
        # Verificar si es un canal de ticket
        ticket_data = self.get_ticket_data(channel.id)
        if not ticket_data:
            await ctx.send("❌ Este comando solo puede usarse en un canal de ticket.", ephemeral=True)
            return
        
        # Verificar si el ticket está abierto
        if ticket_data["status"] != TicketStatus.OPEN.value:
            await ctx.send("❌ No se pueden eliminar usuarios de un ticket cerrado.", ephemeral=True)
            return
        
        # Comprobar permisos
        author = ctx.author
        settings = self.get_guild_settings(ctx.guild.id)
        
        is_creator = str(author.id) == ticket_data["user_id"]
        is_support = False
        is_admin = False
        
        # Verificar roles
        if settings.get("support_role_id") and ctx.guild.get_role(int(settings["support_role_id"])) in author.roles:
            is_support = True
        
        if settings.get("admin_role_id") and ctx.guild.get_role(int(settings["admin_role_id"])) in author.roles:
            is_admin = True
        
        if not (is_creator or is_support or is_admin):
            await ctx.send("❌ No tienes permisos para eliminar usuarios de este ticket.", ephemeral=True)
            return
        
        # No permitir eliminar al creador del ticket
        if str(user.id) == ticket_data["user_id"]:
            await ctx.send("❌ No puedes eliminar al creador del ticket.", ephemeral=True)
            return
        
        # Verificar si el usuario tiene acceso
        if str(user.id) not in ticket_data["participants"]:
            await ctx.send(f"❌ {user.mention} no tiene acceso a este ticket.", ephemeral=True)
            return
        
        # Eliminar permiso al usuario
        try:
            await channel.set_permissions(user, overwrite=None)
            
            # Actualizar lista de participantes
            ticket_data["participants"].remove(str(user.id))
            self.save_data()
            
            # Confirmar
            await ctx.send(f"✅ {user.mention} ha sido eliminado del ticket.")
            
        except Exception as e:
            await ctx.send(f"❌ Error al eliminar usuario: {str(e)}", ephemeral=True)
    
    @ticket.command(name="rename", description="Renombrar un ticket")
    @app_commands.describe(new_name="El nuevo nombre para el ticket (sin prefijo)")
    async def ticket_rename(self, ctx, *, new_name: str):
        """Renombrar un ticket"""
        channel = ctx.channel
        
        # Verificar si es un canal de ticket
        ticket_data = self.get_ticket_data(channel.id)
        if not ticket_data:
            await ctx.send("❌ Este comando solo puede usarse en un canal de ticket.", ephemeral=True)
            return
        
        # Verificar si el ticket está abierto
        if ticket_data["status"] != TicketStatus.OPEN.value:
            await ctx.send("❌ No se puede renombrar un ticket cerrado.", ephemeral=True)
            return
        
        # Comprobar permisos
        author = ctx.author
        settings = self.get_guild_settings(ctx.guild.id)
        
        is_support = False
        is_admin = False
        
        # Verificar roles
        if settings.get("support_role_id") and ctx.guild.get_role(int(settings["support_role_id"])) in author.roles:
            is_support = True
        
        if settings.get("admin_role_id") and ctx.guild.get_role(int(settings["admin_role_id"])) in author.roles:
            is_admin = True
        
        if not (is_support or is_admin):
            await ctx.send("❌ Solo el personal de soporte puede renombrar tickets.", ephemeral=True)
            return
        
        # Limpiar el nombre (quitar espacios, caracteres especiales)
        clean_name = new_name.strip().lower().replace(" ", "-")
        if not clean_name:
            await ctx.send("❌ El nombre no puede estar vacío.", ephemeral=True)
            return
        
        # Añadir prefijo de ticket
        new_channel_name = f"{ticket_data['ticket_id'].lower()}-{clean_name}"
        
        # Renombrar canal
        try:
            await channel.edit(name=new_channel_name)
            await ctx.send(f"✅ Ticket renombrado a `{new_channel_name}`.")
        except Exception as e:
            await ctx.send(f"❌ Error al renombrar: {str(e)}", ephemeral=True)
    
    @ticket.command(name="list", description="Listar tus tickets actuales")
    async def ticket_list(self, ctx):
        """Listar tus tickets actuales"""
        await ctx.defer(ephemeral=True)
        
        user_id = str(ctx.author.id)
        
        # Verificar si el usuario tiene tickets
        if user_id not in self.tickets_data["user_tickets"] or not self.tickets_data["user_tickets"][user_id]:
            await ctx.send("📝 No tienes tickets registrados.", ephemeral=True)
            return
        
        # Filtrar tickets activos
        active_tickets = []
        closed_tickets = []
        
        for channel_id in self.tickets_data["user_tickets"][user_id]:
            ticket_data = self.tickets_data["tickets"].get(channel_id)
            if not ticket_data:
                continue
            
            if ticket_data["status"] == TicketStatus.OPEN.value:
                active_tickets.append(ticket_data)
            else:
                closed_tickets.append(ticket_data)
        
        # Crear embed
        embed = discord.Embed(
            title="Tus Tickets",
            description=f"Tienes {len(active_tickets)} tickets activos y {len(closed_tickets)} cerrados.",
            color=discord.Color.blue()
        )
        
        # Agregar tickets activos
        if active_tickets:
            active_text = ""
            for ticket in active_tickets:
                category_name = self.tickets_data["categories"][ticket["category"]]["name"]
                channel = ctx.guild.get_channel(int(ticket["channel_id"]))
                
                if channel:
                    active_text += f"• `{ticket['ticket_id']}` [{category_name}]: {channel.mention}\n"
                else:
                    active_text += f"• `{ticket['ticket_id']}` [{category_name}]: Canal no disponible\n"
            
            embed.add_field(name="Tickets Activos", value=active_text, inline=False)
        
        # Agregar tickets cerrados recientes (últimos 5)
        if closed_tickets:
            # Ordenar por fecha de cierre, más recientes primero
            closed_tickets.sort(key=lambda t: t.get("closed_at", 0), reverse=True)
            
            closed_text = ""
            for ticket in closed_tickets[:5]:
                category_name = self.tickets_data["categories"][ticket["category"]]["name"]
                closed_date = datetime.datetime.fromtimestamp(ticket.get("closed_at", 0)).strftime("%d/%m/%Y")
                
                closed_text += f"• `{ticket['ticket_id']}` [{category_name}]: Cerrado el {closed_date}\n"
            
            embed.add_field(name="Tickets Cerrados Recientes", value=closed_text, inline=False)
        
        await ctx.send(embed=embed, ephemeral=True)
    
    @ticket.command(name="stats", description="Ver estadísticas de tickets")
    @commands.has_permissions(administrator=True)
    async def ticket_stats(self, ctx):
        """Ver estadísticas de tickets del servidor"""
        await ctx.defer()
        
        guild_id = str(ctx.guild.id)
        
        # Contar tickets
        total_tickets = 0
        open_tickets = 0
        closed_tickets = 0
        
        tickets_by_category = {}
        tickets_by_user = {}
        
        # Inicializar contadores de categorías
        for category_id in self.tickets_data["categories"]:
            tickets_by_category[category_id] = 0
        
        for channel_id, ticket_data in self.tickets_data["tickets"].items():
            if ticket_data["guild_id"] != guild_id:
                continue
            
            total_tickets += 1
            
            # Contar por estado
            if ticket_data["status"] == TicketStatus.OPEN.value:
                open_tickets += 1
            else:
                closed_tickets += 1
            
            # Contar por categoría
            category = ticket_data["category"]
            tickets_by_category[category] = tickets_by_category.get(category, 0) + 1
            
            # Contar por usuario
            user_id = ticket_data["user_id"]
            user_name = ticket_data["user_name"]
            
            if user_id not in tickets_by_user:
                tickets_by_user[user_id] = {"name": user_name, "count": 0}
            
            tickets_by_user[user_id]["count"] += 1
        
        # Crear embed
        embed = discord.Embed(
            title=f"Estadísticas de Tickets - {ctx.guild.name}",
            color=discord.Color.blue()
        )
        
        # Estadísticas generales
        embed.add_field(name="Total de Tickets", value=str(total_tickets), inline=True)
        embed.add_field(name="Tickets Abiertos", value=str(open_tickets), inline=True)
        embed.add_field(name="Tickets Cerrados", value=str(closed_tickets), inline=True)
        
        # Estadísticas por categoría
        categories_text = ""
        for category_id, count in tickets_by_category.items():
            if count > 0:
                category_name = self.tickets_data["categories"][category_id]["name"]
                categories_text += f"• **{category_name}**: {count}\n"
        
        if categories_text:
            embed.add_field(name="Tickets por Categoría", value=categories_text, inline=False)
        
        # Top usuarios
        top_users = sorted(tickets_by_user.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
        
        users_text = ""
        for user_id, data in top_users:
            users_text += f"• **{data['name']}**: {data['count']} tickets\n"
        
        if users_text:
            embed.add_field(name="Usuarios con Más Tickets", value=users_text, inline=False)
        
        # Establecer thumbnail con el icono del servidor
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        
        await ctx.send(embed=embed)
    
    @ticket.command(name="categories", description="Gestionar categorías de tickets")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        action="La acción a realizar",
        category_id="ID de la categoría (solo letras, números y guiones)",
        name="Nombre visible de la categoría",
        description="Descripción de la categoría",
        color="Color (blue, red, green, orange, purple, gold, teal)",
        emoji="Emoji para la categoría"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Listar categorías", value="list"),
        app_commands.Choice(name="Añadir categoría", value="add"),
        app_commands.Choice(name="Eliminar categoría", value="remove"),
        app_commands.Choice(name="Editar categoría", value="edit"),
        app_commands.Choice(name="Habilitar categoría", value="enable"),
        app_commands.Choice(name="Deshabilitar categoría", value="disable")
    ])
    @app_commands.choices(color=[
        app_commands.Choice(name="Azul", value="blue"),
        app_commands.Choice(name="Rojo", value="red"),
        app_commands.Choice(name="Verde", value="green"),
        app_commands.Choice(name="Naranja", value="orange"),
        app_commands.Choice(name="Morado", value="purple"),
        app_commands.Choice(name="Dorado", value="gold"),
        app_commands.Choice(name="Turquesa", value="teal")
    ])
    async def ticket_categories(
        self, ctx,
        action: str,
        category_id: typing.Optional[str] = None,
        name: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        color: typing.Optional[str] = "blue",
        emoji: typing.Optional[str] = "❓"
    ):
        """Gestionar categorías de tickets"""
        guild_id = str(ctx.guild.id)
        settings = self.get_guild_settings(guild_id)
        
        if action == "list":
            # Listar categorías
            embed = discord.Embed(
                title="Categorías de Tickets",
                description="Lista de categorías disponibles para tickets:",
                color=discord.Color.blue()
            )
            
            for cat_id, cat_data in self.tickets_data["categories"].items():
                enabled = "✅" if cat_id in settings.get("enabled_categories", []) else "❌"
                emoji = cat_data.get("emoji", "❓")
                name = cat_data.get("name", "Categoría")
                description = cat_data.get("description", "Sin descripción")
                color = cat_data.get("color", "blue")
                
                embed.add_field(
                    name=f"{enabled} {emoji} {name} (`{cat_id}`)",
                    value=f"Descripción: {description}\nColor: {color}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        elif action == "add":
            # Añadir categoría
            if not category_id:
                await ctx.send("❌ Debes proporcionar un ID para la categoría.", ephemeral=True)
                return
            
            # Validar ID
            if not category_id.replace("-", "").isalnum():
                await ctx.send("❌ El ID de categoría solo puede contener letras, números y guiones.", ephemeral=True)
                return
            
            # Verificar si ya existe
            if category_id in self.tickets_data["categories"]:
                await ctx.send("❌ Ya existe una categoría con ese ID.", ephemeral=True)
                return
            
            # Verificar nombre
            if not name:
                await ctx.send("❌ Debes proporcionar un nombre para la categoría.", ephemeral=True)
                return
            
            # Crear categoría
            self.tickets_data["categories"][category_id] = {
                "name": name,
                "description": description or "Sin descripción",
                "color": color.lower(),
                "emoji": emoji
            }
            
            # Habilitar por defecto
            if "enabled_categories" not in settings:
                settings["enabled_categories"] = []
            
            settings["enabled_categories"].append(category_id)
            
            # Guardar cambios
            self.save_data()
            
            await ctx.send(f"✅ Categoría `{category_id}` añadida correctamente.")
            
        elif action == "remove":
            # Eliminar categoría
            if not category_id:
                await ctx.send("❌ Debes proporcionar el ID de la categoría a eliminar.", ephemeral=True)
                return
            
            # Verificar si existe
            if category_id not in self.tickets_data["categories"]:
                await ctx.send("❌ No existe una categoría con ese ID.", ephemeral=True)
                return
            
            # No permitir eliminar categorías predeterminadas
            if category_id in ["general", "technical", "report"]:
                await ctx.send("❌ No puedes eliminar categorías predeterminadas.", ephemeral=True)
                return
            
            # Eliminar categoría
            del self.tickets_data["categories"][category_id]
            
            # Eliminar de habilitadas
            if "enabled_categories" in settings and category_id in settings["enabled_categories"]:
                settings["enabled_categories"].remove(category_id)
            
            # Guardar cambios
            self.save_data()
            
            await ctx.send(f"✅ Categoría `{category_id}` eliminada correctamente.")
            
        elif action == "edit":
            # Editar categoría
            if not category_id:
                await ctx.send("❌ Debes proporcionar el ID de la categoría a editar.", ephemeral=True)
                return
            
            # Verificar si existe
            if category_id not in self.tickets_data["categories"]:
                await ctx.send("❌ No existe una categoría con ese ID.", ephemeral=True)
                return
            
            # Obtener categoría actual
            category = self.tickets_data["categories"][category_id]
            
            # Actualizar valores proporcionados
            if name:
                category["name"] = name
            
            if description:
                category["description"] = description
            
            if color:
                category["color"] = color.lower()
            
            if emoji:
                category["emoji"] = emoji
            
            # Guardar cambios
            self.save_data()
            
            await ctx.send(f"✅ Categoría `{category_id}` actualizada correctamente.")
            
        elif action == "enable":
            # Habilitar categoría
            if not category_id:
                await ctx.send("❌ Debes proporcionar el ID de la categoría a habilitar.", ephemeral=True)
                return
            
            # Verificar si existe
            if category_id not in self.tickets_data["categories"]:
                await ctx.send("❌ No existe una categoría con ese ID.", ephemeral=True)
                return
            
            # Verificar si ya está habilitada
            if "enabled_categories" in settings and category_id in settings["enabled_categories"]:
                await ctx.send("❌ Esta categoría ya está habilitada.", ephemeral=True)
                return
            
            # Habilitar categoría
            if "enabled_categories" not in settings:
                settings["enabled_categories"] = []
            
            settings["enabled_categories"].append(category_id)
            
            # Guardar cambios
            self.save_data()
            
            await ctx.send(f"✅ Categoría `{category_id}` habilitada correctamente.")
            
        elif action == "disable":
            # Deshabilitar categoría
            if not category_id:
                await ctx.send("❌ Debes proporcionar el ID de la categoría a deshabilitar.", ephemeral=True)
                return
            
            # Verificar si existe
            if category_id not in self.tickets_data["categories"]:
                await ctx.send("❌ No existe una categoría con ese ID.", ephemeral=True)
                return
            
            # Verificar si está habilitada
            if "enabled_categories" not in settings or category_id not in settings["enabled_categories"]:
                await ctx.send("❌ Esta categoría ya está deshabilitada.", ephemeral=True)
                return
            
            # Deshabilitar categoría
            settings["enabled_categories"].remove(category_id)
            
            # Guardar cambios
            self.save_data()
            
            await ctx.send(f"✅ Categoría `{category_id}` deshabilitada correctamente.")
            
        else:
            await ctx.send("❌ Acción no válida.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))