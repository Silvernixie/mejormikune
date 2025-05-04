import os
from os import getpid

import discord
from discord.ext import commands
from psutil import Process


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.snipes = {}

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx: commands.Context, name: str):
        """Carga un cog"""
        try:
            await self.bot.load_extension(f'cogs.{name}')
        except Exception as e:
            await ctx.reply(
                f'<:nope:846611758445625364> **`ERROR:`** {type(e).__name__} - {e}',
            )
        else:
            await ctx.reply(
                f'<:okay:846612389046386689> **`OKAY:`** He cargado __{name}__ correctamente.',
            )

    @commands.command(name='unload')
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, name: str):
        """Descarga un cog"""
        try:
            await self.bot.unload_extension(f'cogs.{name}')
        except Exception as e:
            await ctx.reply(
                f'<:nope:846611758445625364> **`ERROR:`** {type(e).__name__} - {e}',
            )
        else:
            await ctx.reply(
                f'<:okay:846612389046386689> **`OKAY:`** He descargado __{name}__ correctamente.',
            )

    @commands.command(name='reload')
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, name: str):
        """Recarga un cog"""
        try:
            try:
                # Intenta descargar primero (podría fallar si no está cargado)
                await self.bot.unload_extension(f'cogs.{name}')
            except commands.ExtensionNotLoaded:
                # Si no está cargado, solo intentamos cargarlo directamente
                await ctx.reply(
                    f'<:nope:846611758445625364> **`INFO:`** El cog {name} no estaba cargado. Intentando cargarlo...',
                )
            
            # Cargar el cog
            await self.bot.load_extension(f'cogs.{name}')
        except Exception as e:
            await ctx.reply(
                f'<:nope:846611758445625364> **`ERROR:`** {type(e).__name__} - {e}',
            )
        else:
            await ctx.reply(
                f'<:okay:846612389046386689> **`OKAY:`** He cargado __{name}__ correctamente.',
            )

    @commands.command(name='rall')
    @commands.is_owner()
    async def rall(self, ctx: commands.Context):
        """Recarga todos los cogs"""
        cogs = []
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.bot.unload_extension(f'cogs.{filename[:-3]}')
                    await self.bot.load_extension(f'cogs.{filename[:-3]}')

                    cogs.append(f'{filename}')
                except Exception as error:
                    await ctx.reply(
                        f'<:nope:846611758445625364> Nope: {filename}: {error}',
                        mention_author=False,
                    )
        await ctx.reply(
            f'<:okay:846612389046386689> Recargué los siguientes cogs:\n {cogs}'
        )

    @commands.command()
    @commands.is_owner()
    async def memory(self, ctx: commands.Context):
        await ctx.send(
            f'Estoy usando **{round(Process(getpid()).memory_info().rss/1024/1024, 2)} MB** en mi servidor.'
        )

    # https://vcokltfre.dev/tutorial/09-snipe/
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        self.bot.snipes[message.channel.id] = message

    @commands.command(name='snipe')
    @commands.is_owner()
    async def snipe(self, ctx: commands.Context, *, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        try:
            msg = self.bot.snipes[channel.id]
        except KeyError:
            return await ctx.send('Nothing to snipe!')
        # one liner, dont complain
        await ctx.send(
            embed=discord.Embed(
                description=msg.content, color=msg.author.color
            ).set_author(
                name=str(msg.author), icon_url=str(msg.author.avatar.url)
            )
        )

    @commands.command()
    @commands.is_owner()
    async def serverlist(self, ctx: commands.Context):
        guilds = [guild.name for guild in self.bot.guilds]
        member_count = [guild.member_count for guild in self.bot.guilds]
        serverlist = dict(zip(guilds, member_count))
        output = '\n'.join(f'{k} ({v})' for k, v in serverlist.items())
        servers = discord.Embed(
            title=f'Servers ({len(guilds)})',
            description=output,
            colour=0xFBF9FA,
        )
        await ctx.send(embed=servers)

    @commands.command(name="logout", aliases=['close', 'stopbot'])
    @commands.is_owner()
    async def logout(self, ctx):
        await ctx.send('Okay, hora de reiniciar 💤💤💤')
        await self.bot.close()

    @commands.command(name="sync")
    @commands.is_owner()
    async def _sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
        embed = discord.Embed(
            title="Sincronizado!",
            description="El arbol de commandos se ha sincronizado exitosamente",
            colour=0xFBF9FA,
        )
        await ctx.send(embed=embed)

    @commands.command(name="diagnose", aliases=["diagnostico", "check"])
    @commands.is_owner()
    async def diagnose(self, ctx: commands.Context):
        """Diagnostica qué cogs están cargados y sus comandos disponibles"""
        # Crear un embed para el diagnóstico
        embed = discord.Embed(
            title="📊 Diagnóstico de Cogs",
            description="Información sobre los cogs cargados y sus comandos",
            color=0x00FFFF
        )
        
        # Lista de cogs esperados
        expected_cogs = ['anime', 'economy', 'error_handler', 'funny', 'general', 
                         'img', 'owner', 'reddit', 'rol', 'utils']
        
        # Mostrar cogs cargados
        loaded_cogs = []
        for name, cog in self.bot.cogs.items():
            loaded_cogs.append(name)
            
            # Contar comandos en cada cog
            cog_commands = list(cog.get_commands())
            command_count = len(cog_commands)
            
            # Lista de nombres de comandos para mostrar
            command_names = [f"`{cmd.name}`" for cmd in cog_commands]
            command_list = ", ".join(command_names) if command_names else "Ninguno"
            
            # Añadir campo al embed
            embed.add_field(
                name=f"✅ {name} ({command_count} comandos)",
                value=f"Comandos: {command_list}",
                inline=False
            )
        
        # Verificar si hay cogs esperados que no están cargados
        missing_cogs = [cog for cog in expected_cogs if cog.title() not in loaded_cogs and cog not in loaded_cogs]
        if missing_cogs:
            embed.add_field(
                name="❌ Cogs no cargados",
                value=", ".join([f"`{cog}`" for cog in missing_cogs]),
                inline=False
            )
        
        # Información adicional
        embed.add_field(
            name="📝 Información",
            value=f"Total de cogs cargados: **{len(loaded_cogs)}/{len(expected_cogs)}**\n"
                  f"Total de comandos: **{len(list(self.bot.commands))}**",
            inline=False
        )
        
        embed.set_footer(text="Para recargar un cog, usa el comando >>reload <nombre_cog>")
        
        await ctx.send(embed=embed)
        
        # Si economy está en los cogs faltantes, dar recomendaciones específicas
        if "economy" in missing_cogs:
            economy_help = discord.Embed(
                title="💰 Problema con el Cog de Economía",
                description="El cog de economía no está cargado correctamente. Aquí hay algunas recomendaciones:",
                color=0xFF0000
            )
            economy_help.add_field(
                name="1. Intentar recargar manualmente",
                value="Usa el comando `>>reload economy` para intentar recargarlo",
                inline=False
            )
            economy_help.add_field(
                name="2. Verificar errores",
                value="Revisa la consola del bot para ver si hay errores específicos del cog de economía",
                inline=False
            )
            economy_help.add_field(
                name="3. Comprobar el archivo",
                value="Verifica que el archivo `economy.py` existe y tiene los permisos correctos",
                inline=False
            )
            economy_help.add_field(
                name="4. Asegurar dependencias",
                value="El cog podría necesitar módulos externos. Verifica que todas las dependencias estén instaladas",
                inline=False
            )
            
            await ctx.send(embed=economy_help)

async def setup(bot):
    await bot.add_cog(Owner(bot))
