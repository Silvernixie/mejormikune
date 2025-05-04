import os
import random
from typing import Optional, Dict, List, Any

import discord
from discord.ext.commands import (
    AutoShardedBot,
    MinimalHelpCommand,
    when_mentioned_or,
    Command,
    Cog,
)
import difflib


def get_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""

    # Notice how you can use spaces in prefixes. Try to keep them simple though.
    prefixes = ['nya>', 'nya', '>>', f'{os.environ["PREFIX"]}']

    # If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
    return when_mentioned_or(*prefixes)(bot, message)


class Bot(AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix=get_prefix, *args, **kwargs)

    # Eliminamos el método setup_hook para evitar la carga automática duplicada
    # La carga de extensiones ahora se manejará exclusivamente desde main.py
    
    async def on_message(self, msg):
        if not self.is_ready() or msg.author.bot or not msg.guild:
            return

        await self.process_commands(msg)


# Vista personalizada para botones de paginación en el comando de ayuda
class HelpView(discord.ui.View):
    """Vista personalizada para paginación de comandos de ayuda con estilo Nekotina."""
    
    def __init__(self, help_command, pages, timeout=60):
        super().__init__(timeout=timeout)
        self.help_command = help_command
        self.pages = pages  # Lista de embeds de páginas
        self.current_page = 0
        self.total_pages = len(pages)
        self.update_buttons()
        
    def update_buttons(self):
        """Actualiza el estado de los botones según la página actual."""
        # Deshabilitar botones de anterior si estamos en la primera página
        self.first_page.disabled = self.prev_page.disabled = (self.current_page == 0)
        # Deshabilitar botones de siguiente si estamos en la última página
        self.next_page.disabled = self.last_page.disabled = (self.current_page == self.total_pages - 1)
        
    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.secondary, custom_id='first_page')
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir a la primera página."""
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @discord.ui.button(emoji='◀️', style=discord.ButtonStyle.primary, custom_id='prev_page')
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir a la página anterior."""
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @discord.ui.button(emoji='🌸', style=discord.ButtonStyle.danger, custom_id='close')
    async def close_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cerrar el menú de ayuda."""
        await interaction.message.delete()
    
    @discord.ui.button(emoji='▶️', style=discord.ButtonStyle.primary, custom_id='next_page')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir a la página siguiente."""
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.secondary, custom_id='last_page')
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir a la última página."""
        self.current_page = self.total_pages - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    async def on_timeout(self):
        """Desactiva los botones cuando expira el tiempo."""
        for item in self.children:
            item.disabled = True
        # No podemos editar el mensaje aquí ya que no tenemos referencia directa


class HelpCommand(MinimalHelpCommand):
    """Comando de ayuda con estilo Nekotina - visual mejorado y organización elegante."""
    
    # Paleta de colores estilo Nekotina
    COLORS = {
        'default': 0xF5A9B8,  # Rosa principal (Nekotina)
        'economy': 0xFFC0CB,  # Rosa económico
        'economia': 0xFFC0CB,  # Rosa económico (español)
        'anime': 0xFFB6C1,    # Rosa suave anime
        'funny': 0xFAB9D1,    # Rosa diversión
        'general': 0xFFDFE9,  # Rosa claro general
        'img': 0xFCB4E2,      # Rosa imagen
        'owner': 0xD8A0D8,    # Lavanda propietario
        'reddit': 0xE2A9F3,   # Lila Reddit
        'rol': 0xF7D1F8,      # Rosa suave roles
        'utils': 0xF8E0F1,    # Rosa muy claro utils
        'games': 0xFFD1DC,    # Rosa juegos
        'moderation': 0xF0BBEF, # Rosa moderación
        'music': 0xFFB7DD,    # Rosa música
        'ai': 0xFFC3E1,       # Rosa IA
    }
    
    # Emojis mejorados para cada categoría
    CATEGORY_EMOJIS = {
        'economy': '💖',
        'economia': '🐰',
        'anime': '🌸',
        'funny': '😊',
        'general': '✨',
        'img': '🎀',
        'owner': '👑',
        'reddit': '💝',
        'rol': '💫',
        'utils': '💕',
        'error_handler': '💢',
        'games': '🎮',
        'moderation': '🛡️',
        'music': '🎵',
        'ai': '🤖',
    }
    
    # Descripciones mejoradas para cada categoría
    CATEGORY_DESCRIPTIONS = {
        'economy': 'Sistema económico y monedas virtuales para comprar artículos exclusivos.',
        'economia': 'Sistema económico de conejos virtuales con tienda, banco, propiedades y más.',
        'anime': 'Todo lo relacionado con anime, manga y la cultura japonesa.',
        'funny': 'Comandos divertidos para pasar un buen rato con tus amigos.',
        'general': 'Utilidades generales para gestionar y mejorar tu servidor.',
        'img': 'Manipulación de imágenes y generación de contenido visual.',
        'owner': 'Comandos administrativos exclusivos para el propietario del bot.',
        'reddit': 'Obtén contenido interesante y actualizado desde Reddit.',
        'rol': 'Sistema de roles, permisos y gestión de usuarios en el servidor.',
        'utils': 'Herramientas útiles para diversas funciones y necesidades.',
        'error_handler': 'Sistema inteligente de manejo y reporte de errores.',
        'games': 'Juegos interactivos para divertirte junto a otros usuarios.',
        'moderation': 'Comandos de moderación para administrar el servidor de manera efectiva.',
        'music': 'Sistema de música para reproducir tus canciones favoritas.',
        'ai': 'Funcionalidades de inteligencia artificial para interactuar de forma avanzada.',
    }
    
    # Ejemplos para comandos comunes con formato estilo Nekotina
    COMMAND_EXAMPLES = {
        'work': '>>work',
        'daily': '>>daily',
        'balance': '>>balance\n>>balance @usuario',
        'shop': '>>shop',
        'buy': '>>buy vip',
        'help': '>>help\n>>help economy',
        'mine': '>>mine',
        'resources': '>>resources',
        'upgrade-pickaxe': '>>upgrade-pickaxe',
        'profile': '>>profile',
        'inventory': '>>inventory',
        'bank': '>>bank',
        'bank deposit': '>>bank deposit 1000\n>>bank deposit all',
        'bank withdraw': '>>bank withdraw 500\n>>bank withdraw all',
        'bank transfer': '>>bank transfer @usuario 1000',
        'bank loan': '>>bank loan 5000',
        'bank payloan': '>>bank payloan 1000\n>>bank payloan all',
        'properties': '>>properties',
        'properties my': '>>properties my',
        'properties buy': '>>properties buy small_hutch',
        'properties collect': '>>properties collect',
        'properties sell': '>>properties sell small_hutch',
    }
    
    NEWS = '💗 ¡Nuevo estilo inspirado en ADY! 💗\n🌸 ¡Sistema de económico y comandos de minería mejorados! 🌸'
    
    CUTE_SEPARATORS = ['•──────────•°•❀•°•──────────•', 
                       '┊          ┊',
                       '┊ ˚₊· ͟͟͞͞➳❥ ┊',
                       '╰── ⋅ ⋅ ────╯']

    # Comandos agrupados por categoría para mejor organización
    COMMAND_CATEGORIES = {
        'economia': {
            'Básicos': ['daily', 'balance', 'profile', 'inventory'],
            'Banco': ['bank', 'bank deposit', 'bank withdraw', 'bank transfer', 'bank loan', 'bank payloan'],
            'Propiedades': ['properties', 'properties my', 'properties buy', 'properties collect', 'properties sell'],
            'Tienda': ['shop', 'buy', 'sell']
        }
    }
    
    # Mapeo de alias para cogs (ayuda a reconocer nombres alternativos)
    COG_ALIASES = {
        'economy': 'Economia',
        'economía': 'Economia',
        'eco': 'Economia',
        'money': 'Economia',
        'dinero': 'Economia',
        'conejos': 'Economia',
        'banco': 'Economia',
        'bank': 'Economia',
        'properties': 'Economia',
        'propiedades': 'Economia',
    }

    # Lista de cogs que deben usar el formato compacto (estilo Nekotina)
    COMPACT_STYLE_COGS = ['Economia']
    
    def get_command_signature(self, command):
        """Devuelve la firma del comando con un formato mejorado estilo Nekotina."""
        return f'```ansi\n\u001b[0;38;5;218m{self.context.clean_prefix}{command.qualified_name}\u001b[0m \u001b[0;38;5;225m{command.signature}\u001b[0m\n```'
    
    def get_example(self, command):
        """Obtiene ejemplos de uso para un comando con formato mejorado."""
        if command.qualified_name in self.COMMAND_EXAMPLES:
            return f"```ansi\n\u001b[0;38;5;218m{self.COMMAND_EXAMPLES[command.qualified_name]}\u001b[0m\n```"
        return None
    
    def get_category_emoji(self, category_name: str) -> str:
        """Obtiene el emoji correspondiente a una categoría."""
        return self.CATEGORY_EMOJIS.get(category_name.lower(), '🎀')
    
    def get_category_color(self, category_name: str) -> int:
        """Obtiene el color correspondiente a una categoría."""
        return self.COLORS.get(category_name.lower(), self.COLORS['default'])
    
    def get_category_description(self, category_name: str) -> str:
        """Obtiene la descripción de una categoría."""
        return self.CATEGORY_DESCRIPTIONS.get(category_name.lower(), 'Comandos especiales para mejorar tu experiencia.')
    
    def format_command_name(self, command: Command) -> str:
        """Formatea el nombre de un comando con estilo Nekotina."""
        return f"`{command.qualified_name}`"
    
    def format_command_list(self, commands: List[Command], heading: Optional[str] = None) -> str:
        """Formatea una lista de comandos con estilo Nekotina."""
        if not commands:
            return "No hay comandos disponibles en esta categoría."
            
        command_list = []
        for command in commands:
            name = self.format_command_name(command)
            short_doc = command.short_doc or "Sin descripción"
            command_list.append(f"❥ {name} • {short_doc}")
            
        formatted = "\n".join(command_list)
        if heading:
            return f"**{heading}**\n{formatted}"
        return formatted
    
    def footer(self):
        """Devuelve el texto del pie de página con estilo Nekotina."""
        return f'✧･ﾟ: *✧･ﾟ Usa {self.context.clean_prefix}{self.invoked_with} [comando] para más info ･ﾟ*:･ﾟ✧'
    
    def get_random_tip(self) -> str:
        """Devuelve un consejo aleatorio con emojis cute."""
        tips = [
            "💖 ¿Sabías que puedes usar >>daily para reclamar monedas gratis cada día?",
            "✨ Prueba >>mine para conseguir recursos valiosos que puedes vender.",
            "🎀 Mejora tu pico con >>upgrade-pickaxe para obtener más recursos.",
            "💫 ¡Usa >>profile para ver todas tus estadísticas!",
            "🌸 El comando >>buy te permite comprar objetos de la tienda.",
            "💕 ¡Prueba >>gamble para apostar tus monedas y ganar más!",
            "✨ Recuerda que puedes guardar tus monedas en el banco con >>bank deposit.",
            "💖 Usa >>inventory para ver los objetos que tienes.",
            "🎀 ¡Puedes pescar con >>fish para obtener tesoros del mar!",
            "🐰 Compra propiedades con >>properties buy para conseguir ingresos pasivos.",
            "🏦 El banco te paga intereses diarios por tus ahorros automáticamente.",
            "🏘️ Recoge los ingresos de tus propiedades con >>properties collect.",
        ]
        return random.choice(tips)

    def get_random_separator(self) -> str:
        """Devuelve un separador decorativo aleatorio estilo Nekotina."""
        return random.choice(self.CUTE_SEPARATORS)
    
    async def command_callback(self, ctx, *, command=None):
        """Sobreescribe el callback para manejar alias de cogs."""
        if command:
            # Verificar si es un alias de un cog
            command_lower = command.lower()
            if command_lower in self.COG_ALIASES:
                # Buscar el cog real
                real_cog_name = self.COG_ALIASES[command_lower]
                found_cog = None
                
                # Buscar el cog entre los disponibles
                for cog in self.context.bot.cogs.values():
                    if cog.qualified_name.lower() == real_cog_name.lower():
                        found_cog = cog
                        break
                
                if found_cog:
                    # Mostrar ayuda del cog encontrado
                    if found_cog.qualified_name in self.COMPACT_STYLE_COGS:
                        return await self.send_compact_cog_help(found_cog)
                    else:
                        return await self.send_cog_help(found_cog)
        
        # Si no es un alias o no se encontró, continuar con el comportamiento normal
        return await super().command_callback(ctx, command=command)

    async def send_compact_cog_help(self, cog):
        """Envía la ayuda de un cog en formato compacto al estilo Nekotina."""
        # Obtener color y emoji de la categoría
        cog_name = cog.qualified_name
        color = self.get_category_color(cog_name)
        emoji = self.get_category_emoji(cog_name)
        
        # Filtrar comandos visibles
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        visible_commands = [cmd for cmd in filtered if not cmd.hidden]
        
        if not visible_commands:
            return await self.send_error_message(f"No hay comandos disponibles en la categoría {cog_name}.")
        
        # Crear embed para el formato compacto
        embed = discord.Embed(
            title=f"{emoji} Comandos de {cog_name}",
            color=color
        )
        
        # Añadir descripción
        description = self.get_category_description(cog_name)
        embed.description = f"{description}\nAyuda detallada sobre un comando: `{self.context.clean_prefix}help <comando>`"
        
        # Formatear comandos en modo compacto (similar a Nekotina)
        command_names = []
        for cmd in visible_commands:
            # Para comandos de grupo, agregar el comando principal y sus subcomandos
            if hasattr(cmd, 'commands') and len(cmd.commands) > 0:
                command_names.append(cmd.name)
                # Agregar subcomandos con el formato "grupo comando"
                for subcmd in cmd.commands:
                    if not subcmd.hidden:
                        command_names.append(f"{cmd.name} {subcmd.name}")
            else:
                command_names.append(cmd.name)
        
        # Ordenar alfabéticamente
        command_names.sort()
        
        # Formato compacto multicolumna
        commands_text = "           ".join(command_names)
        
        # Agregar campo con todos los comandos
        embed.add_field(
            name="📖 Comandos",
            value=f"```{commands_text}```",
            inline=False
        )
        
        # Footer personalizado
        embed.set_footer(text=f"Para ayuda adicional, usa {self.context.clean_prefix}help [comando] • {len(command_names)} comandos disponibles")
        
        # Enviar el embed sin vista (ya que no hay páginas)
        await self.get_destination().send(embed=embed)
    
    async def send_bot_help(self, mapping):
        """Envía el menú principal de ayuda con estilo Nekotina y paginación."""
        # Preparar la página inicial (información y estadísticas)
        main_embed = discord.Embed(color=self.COLORS['default'])
        
        # Configurar autor y título con estilo kawaii
        main_embed.set_author(
            name=f'✧･ﾟ: * ✧ Menú de Ayuda ✧ *:･ﾟ✧',
            icon_url='https://cdn.discordapp.com/attachments/829223734559637545/859941157944557588/headAsset_214x-8.png',
        )
        
        # Separador decorativo
        separator = self.get_random_separator()
        
        # Descripción con noticias y estilo mejorado
        main_embed.description = (
            f"### 💗 Novedades 💗\n"
            f"{self.NEWS}\n\n"
            f"{separator}\n\n"
            f"### ✨ Información\n"
            f"> **Prefijos:** `>>` `nya>` `nya`\n"
            f"> **Comandos:** {len(set(self.context.bot.walk_commands()))}\n"
            f"> **Servidores:** {len(self.context.bot.guilds)}\n\n"
            f"{separator}\n\n"
            f"### 💭 Consejo\n"
            f"> {self.get_random_tip()}\n\n"
            f"*Para información detallada de un comando, usa `{self.context.clean_prefix}help [comando]`*\n\n"
            f"*Usa los botones de navegación para explorar las categorías de comandos*"
        )
        
        # Imagen de banner estilo Nekotina
        main_embed.set_image(
            url='https://cdn.discordapp.com/attachments/829223734559637545/866011691123736606/cherry.png'
        )
        
        # Footer con estilo Nekotina
        main_embed.set_footer(text=f"Página 1/{len(mapping) + 1} • {self.footer()}")
        
        # Crear una lista de páginas, empezando con la página principal
        pages = [main_embed]
        
        # Organizar los cogs para crear páginas individuales para cada categoría
        filtered_cogs = {}
        for cog, cmds in mapping.items():
            if not cog or not cmds:
                continue
                
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                cog_name = getattr(cog, "qualified_name", "Otros")
                filtered_cogs[cog_name] = filtered
        
        # Crear páginas para cada categoría
        page_num = 2  # Empezamos en la página 2 porque la 1 es la principal
        total_pages = len(filtered_cogs) + 1  # +1 por la página principal
        
        for cog_name, commands in sorted(filtered_cogs.items()):
            # Crear un nuevo embed para cada categoría
            color = self.get_category_color(cog_name)
            emoji = self.get_category_emoji(cog_name)
            
            embed = discord.Embed(
                title=f"{emoji} Categoría: {cog_name} {emoji}",
                description=f"{self.get_random_separator()}\n{self.get_category_description(cog_name)}\n{self.get_random_separator()}",
                color=color
            )
            
            # Mostrar los comandos disponibles
            visible_commands = [cmd for cmd in commands if not cmd.hidden]
            
            if not visible_commands:
                embed.add_field(
                    name="❌ Sin comandos disponibles",
                    value="No hay comandos que puedas usar en esta categoría.",
                    inline=False
                )
            else:
                # Formatear los comandos de manera atractiva y clara
                for cmd in visible_commands:
                    value = cmd.short_doc or "✧ Sin descripción"
                    embed.add_field(
                        name=f"❥ {self.context.clean_prefix}{cmd.qualified_name} {cmd.signature}",
                        value=f"┊ {value}",
                        inline=False
                    )
            
            # Footer con estilo Nekotina
            embed.set_footer(text=f"Página {page_num}/{total_pages} • {self.footer()}")
            
            # Añadir a la lista de páginas
            pages.append(embed)
            page_num += 1
        
        # Enviar mensaje con la vista de paginación
        view = HelpView(self, pages)
        await self.get_destination().send(embed=pages[0], view=view)
    
    async def send_cog_help(self, cog):
        """Envía información de categoría con estilo Nekotina y paginación."""
        # Comprobar si debemos usar el estilo compacto para este cog
        if cog.qualified_name in self.COMPACT_STYLE_COGS:
            return await self.send_compact_cog_help(cog)
            
        # Obtener color y emoji de la categoría
        cog_name = cog.qualified_name
        color = self.get_category_color(cog_name)
        emoji = self.get_category_emoji(cog_name)
        
        # Crear embed para la categoría con estilo Nekotina
        embed = discord.Embed(
            title=f"{emoji} ┊ Categoría: {cog_name} ┊ {emoji}",
            description=f"{self.get_random_separator()}\n{self.get_category_description(cog_name)}\n{self.get_random_separator()}",
            color=color
        )
        
        # Filtrar y organizar comandos
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        
        # Si no hay comandos disponibles
        if not filtered:
            embed.add_field(
                name="❌ Sin comandos disponibles",
                value="No hay comandos que puedas usar en esta categoría.")
            await self.get_destination().send(embed=embed)
            return
        
        # Comprobar si tenemos categorías predefinidas para este cog
        has_predefined_categories = cog_name.lower() in self.COMMAND_CATEGORIES
        
        # Preparar páginas de comandos
        pages = []
        cmds_per_page = 5 if not has_predefined_categories else 10  # Más comandos por página si usamos categorías
        visible_commands = [cmd for cmd in filtered if not cmd.hidden]
        
        if not visible_commands:
            embed.add_field(
                name="❌ Sin comandos disponibles",
                value="No hay comandos visibles que puedas usar en esta categoría.")
            embed.set_footer(text=self.footer())
            await self.get_destination().send(embed=embed)
            return
        
        # Página principal con la descripción
        main_embed = embed.copy()
        
        # Usar categorías predefinidas si existen para este cog
        if has_predefined_categories:
            # Obtener categorías para este cog
            categories = self.COMMAND_CATEGORIES[cog_name.lower()]
            
            # Crear un diccionario para agrupar comandos
            category_commands = {category: [] for category in categories}
            other_commands = []
            
            # Clasificar comandos en sus categorías
            for cmd in visible_commands:
                categorized = False
                for category, command_names in categories.items():
                    if cmd.qualified_name in command_names:
                        category_commands[category].append(cmd)
                        categorized = True
                        break
                
                # Si no encaja en ninguna categoría, ponerlo en otros
                if not categorized:
                    other_commands.append(cmd)
            
            # Añadir categorías a la página principal
            for category_name, category_cmds in category_commands.items():
                if category_cmds:
                    main_embed.add_field(
                        name=f"⭐ {category_name}",
                        value=self.format_command_list(category_cmds),
                        inline=False
                    )
            
            # Añadir comandos sin categoría específica
            if other_commands:
                main_embed.add_field(
                    name="⭐ Otros Comandos",
                    value=self.format_command_list(other_commands),
                    inline=False
                )
                
            # Solo añadir nota si hay comandos
            if any(category_commands.values()) or other_commands:
                main_embed.add_field(
                    name="✧ Nota",
                    value=f"Usa `{self.context.clean_prefix}help [comando]` para ver detalles específicos.",
                    inline=False
                )
        else:
            # Añadir los primeros comandos a la página principal (método estándar)
            for cmd in visible_commands[:cmds_per_page]:
                value = cmd.short_doc or "✧ Sin descripción"
                main_embed.add_field(
                    name=f"❥ {self.context.clean_prefix}{cmd.qualified_name} {cmd.signature}",
                    value=f"┊ {value}",
                    inline=False
                )
            
            # Añadir nota de uso con estilo Nekotina
            main_embed.add_field(
                name="✧ Nota",
                value=f"Usa `{self.context.clean_prefix}help [comando]` para ver detalles específicos.",
                inline=False
            )
        
        # Añadir la primera página
        pages.append(main_embed)
        
        # Si hay más comandos y no estamos usando categorías predefinidas, crear páginas adicionales
        if len(visible_commands) > cmds_per_page and not has_predefined_categories:
            # Crear páginas adicionales
            for i in range(cmds_per_page, len(visible_commands), cmds_per_page):
                page_embed = discord.Embed(
                    title=f"{emoji} ┊ Categoría: {cog_name} (Continuación) ┊ {emoji}",
                    description=f"Comandos adicionales de la categoría `{cog_name}`",
                    color=color
                )
                
                # Añadir comandos a esta página
                for cmd in visible_commands[i:i+cmds_per_page]:
                    value = cmd.short_doc or "✧ Sin descripción"
                    page_embed.add_field(
                        name=f"❥ {self.context.clean_prefix}{cmd.qualified_name} {cmd.signature}",
                        value=f"┊ {value}",
                        inline=False
                    )
                
                # Añadir esta página a la lista
                pages.append(page_embed)
        
        # Actualizar los footers con información de páginas
        for i, page in enumerate(pages):
            page.set_footer(text=f"Página {i+1}/{len(pages)} • {self.footer()}")
        
        # Mostrar con paginación si hay múltiples páginas
        if len(pages) > 1:
            view = HelpView(self, pages)
            await self.get_destination().send(embed=pages[0], view=view)
        else:
            # Si solo hay una página, no necesitamos la vista
            await self.get_destination().send(embed=pages[0])
    
    async def send_command_help(self, command):
        """Envía información de comando detallada con estilo Nekotina."""
        # Obtener la categoría y estilo
        cog = command.cog
        cog_name = getattr(cog, "qualified_name", "Otros") if cog else "Otros"
        color = self.get_category_color(cog_name)
        emoji = self.get_category_emoji(cog_name)
        
        # Crear embed para el comando con estilo Nekotina
        embed = discord.Embed(
            title=f"{emoji} ┊ Comando: {command.qualified_name} ┊ {emoji}",
            description=command.help or f"✧ Sin descripción detallada disponible.",
            color=color
        )
        
        # Separador decorativo
        separator = self.get_random_separator()
        
        # Añadir información con estilo Nekotina
        embed.add_field(
            name="✧ Sintaxis",
            value=self.get_command_signature(command),
            inline=False
        )
        
        # Añadir categoría con estilo Nekotina
        embed.add_field(
            name="✧ Categoría",
            value=f"{self.get_category_emoji(cog_name)} {cog_name}",
            inline=True
        )
        
        # Añadir cooldown si existe con estilo Nekotina
        if command._buckets and command._buckets._cooldown:
            cooldown_text = f"{command._buckets._cooldown.rate} uso(s) cada {command._buckets._cooldown.per:.0f} segundos"
            embed.add_field(
                name="✧ Cooldown",
                value=cooldown_text,
                inline=True
            )
        
        # Añadir aliases si existen con estilo Nekotina
        if command.aliases:
            aliases_text = ", ".join(f"`{alias}`" for alias in command.aliases)
            embed.add_field(
                name="✧ Aliases",
                value=aliases_text,
                inline=True
            )
        
        # Añadir ejemplo con estilo Nekotina
        example = self.get_example(command)
        if example:
            embed.add_field(
                name="✧ Ejemplo",
                value=example,
                inline=False
            )
        
        # Añadir nota decorativa
        embed.add_field(
            name=separator,
            value="*✧ Este comando forma parte del sistema MIKUNE ✧*",
            inline=False
        )
        
        # Footer con estilo Nekotina
        embed.set_footer(text=self.footer())
        await self.get_destination().send(embed=embed)
    
    async def send_group_help(self, group):
        """Envía información de grupo de comandos con estilo Nekotina y paginación."""
        # Obtener la categoría y estilo
        cog = group.cog
        cog_name = getattr(cog, "qualified_name", "Otros") if cog else "Otros"
        color = self.get_category_color(cog_name)
        emoji = self.get_category_emoji(cog_name)
        
        # Crear el embed principal para la información del grupo
        main_embed = discord.Embed(
            title=f"{emoji} ┊ Grupo: {group.qualified_name} ┊ {emoji}",
            description=group.help or f"✧ Sin descripción detallada disponible.",
            color=color
        )
        
        # Añadir información con estilo Nekotina
        main_embed.add_field(
            name="✧ Sintaxis",
            value=self.get_command_signature(group),
            inline=False
        )
        
        # Añadir categoría con estilo Nekotina
        main_embed.add_field(
            name="✧ Categoría",
            value=f"{self.get_category_emoji(cog_name)} {cog_name}",
            inline=True
        )
        
        # Añadir cooldown si existe con estilo Nekotina
        if group._buckets and group._buckets._cooldown:
            cooldown_text = f"{group._buckets._cooldown.rate} uso(s) cada {group._buckets._cooldown.per:.0f} segundos"
            main_embed.add_field(
                name="✧ Cooldown",
                value=cooldown_text,
                inline=True
            )
        
        # Añadir aliases si existen con estilo Nekotina
        if group.aliases:
            aliases_text = ", ".join(f"`{alias}`" for alias in group.aliases)
            main_embed.add_field(
                name="✧ Aliases",
                value=aliases_text,
                inline=True
            )
        
        # Ejemplo si existe
        example = self.get_example(group)
        if example:
            main_embed.add_field(
                name="✧ Ejemplo",
                value=example,
                inline=False
            )
        
        # Separador decorativo
        main_embed.add_field(
            name=self.get_random_separator(),
            value="**Subcomandos disponibles:**",
            inline=False
        )
        
        # Filtrar subcomandos
        filtered = await self.filter_commands(group.commands, sort=True)
        
        # Página principal con información del grupo
        pages = [main_embed]
        
        # Si hay subcomandos, crear página principal y luego páginas adicionales
        if filtered:
            # Añadir subcomandos en la página principal
            for command in filtered[:5]:  # Mostrar los primeros 5 en página principal
                value = command.short_doc or "✧ Sin descripción"
                main_embed.add_field(
                    name=f"❥ {self.context.clean_prefix}{command.qualified_name} {command.signature}",
                    value=f"┊ {value}",
                    inline=False
                )
            
            # Si hay más de 5 subcomandos, crear páginas adicionales
            if len(filtered) > 5:
                # Crear páginas adicionales con más subcomandos, 5 por página
                for i in range(0, len(filtered[5:]), 5):
                    # Clonar estilo del embed principal
                    embed = discord.Embed(
                        title=f"{emoji} ┊ Grupo: {group.qualified_name} (Continuación) ┊ {emoji}",
                        description=f"Subcomandos adicionales del grupo `{group.qualified_name}`",
                        color=color
                    )
                    
                    # Añadir subcomandos en esta página
                    for command in filtered[5+i:5+i+5]:
                        value = command.short_doc or "✧ Sin descripción"
                        embed.add_field(
                            name=f"❥ {self.context.clean_prefix}{command.qualified_name} {command.signature}",
                            value=f"┊ {value}",
                            inline=False
                        )
                    
                    # Añadir a la lista de páginas
                    pages.append(embed)
        else:
            # No hay subcomandos
            main_embed.add_field(
                name="❌ Sin subcomandos disponibles",
                value="Este grupo no tiene subcomandos que puedas usar."
            )
        
        # Actualizar los footers con información de páginas
        for i, embed in enumerate(pages):
            embed.set_footer(text=f"Página {i+1}/{len(pages)} • {self.footer()}")
        
        # Enviar mensaje con la vista de paginación si hay múltiples páginas
        if len(pages) > 1:
            view = HelpView(self, pages)
            await self.get_destination().send(embed=pages[0], view=view)
        else:
            # Si solo hay una página, no necesitamos la vista
            await self.get_destination().send(embed=pages[0])
    
    async def send_error_message(self, error):
        """Envía un mensaje de error con estilo Nekotina."""
        original_error = str(error)
        
        # Verificar si el error se refiere a un comando no encontrado que podría ser un cog
        if "No command called" in original_error:
            # Extraer el nombre del comando
            command_name = original_error.split("No command called ")[1].strip('" .').lower()
            
            # Verificar si podría ser un alias de cog
            if command_name in self.COG_ALIASES:
                real_cog_name = self.COG_ALIASES[command_name]
                
                # Buscar el cog
                for cog in self.context.bot.cogs.values():
                    if cog.qualified_name.lower() == real_cog_name.lower():
                        # Redirigir a la ayuda del cog
                        return await self.send_cog_help(cog)
            
            # Mostrar sugerencias para comandos parecidos
            command_names = [cmd.name for cmd in self.context.bot.commands]
            closest_matches = difflib.get_close_matches(command_name, command_names, n=3, cutoff=0.6)
            
            embed = discord.Embed(
                title="✧ Comando no encontrado ✧",
                description=f"No se encontró ningún comando llamado `{command_name}`.\n\n{self.get_random_separator()}",
                color=self.COLORS['default']
            )
            
            if closest_matches:
                suggestions = "\n".join([f"• `{self.context.clean_prefix}{match}`" for match in closest_matches])
                embed.add_field(
                    name="✧ ¿Quisiste decir...?",
                    value=suggestions,
                    inline=False
                )
            
            # Sugerir ver categorías para comandos tipo "economia"
            if command_name.lower() in ['economia', 'economy', 'eco', 'bank', 'properties']:
                embed.add_field(
                    name="✧ Categoría relacionada",
                    value=f"Prueba `{self.context.clean_prefix}help Economia` para ver todos los comandos económicos.",
                    inline=False
                )
            elif command_name.lower() in ['anime', 'manga']:
                embed.add_field(
                    name="✧ Categoría relacionada",
                    value=f"Prueba `{self.context.clean_prefix}help Anime` para ver todos los comandos de anime.",
                    inline=False
                )
            elif command_name.lower() in ['fun', 'funny', 'meme']:
                embed.add_field(
                    name="✧ Categoría relacionada",
                    value=f"Prueba `{self.context.clean_prefix}help Funny` para ver todos los comandos divertidos.",
                    inline=False
                )
            
            embed.add_field(
                name="✧ Lista completa",
                value=f"Usa `{self.context.clean_prefix}help` para ver todos los comandos disponibles.",
                inline=False
            )
            
            return await self.get_destination().send(embed=embed)
        
        # Error estándar
        embed = discord.Embed(
            title="✧ Error ✧",
            description=f"{str(error)}\n\n{self.get_random_separator()}",
            color=self.COLORS['default']
        )
        embed.add_field(
            name="✧ Sugerencia",
            value=f"Usa `{self.context.clean_prefix}help` para ver todos los comandos disponibles.",
            inline=False
        )
        await self.get_destination().send(embed=embed)
