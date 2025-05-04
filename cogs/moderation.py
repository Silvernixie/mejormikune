import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger('MIKUNE 2')

class Moderation(commands.Cog):
    """Comandos de moderación para administrar el servidor"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No se ha especificado"):
        """Expulsa a un miembro del servidor"""
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="Usuario expulsado",
                description=f"{member.mention} ha sido expulsado\nRazón: {reason}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("No tengo permisos para expulsar a este usuario.")
        except Exception as e:
            logger.error(f"Error al expulsar: {e}")
            await ctx.send(f"Error al expulsar al usuario: {e}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No se ha especificado"):
        """Banea a un miembro del servidor"""
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="Usuario baneado",
                description=f"{member.mention} ha sido baneado\nRazón: {reason}",
                color=discord.Color.dark_red()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("No tengo permisos para banear a este usuario.")
        except Exception as e:
            logger.error(f"Error al banear: {e}")
            await ctx.send(f"Error al banear al usuario: {e}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Borra un número específico de mensajes"""
        if amount <= 0:
            return await ctx.send("El número debe ser mayor que 0.")
        
        if amount > 100:
            amount = 100
            
        try:
            deleted = await ctx.channel.purge(limit=amount+1)  # +1 para incluir el comando
            msg = await ctx.send(f"Se han borrado {len(deleted)-1} mensajes.")
            await asyncio.sleep(3)
            await msg.delete()
        except Exception as e:
            logger.error(f"Error al borrar mensajes: {e}")
            await ctx.send(f"Error al borrar mensajes: {e}")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: int, *, reason="No se ha especificado"):
        """Pone a un usuario en timeout (en minutos)"""
        try:
            until = datetime.now(timezone.utc) + timedelta(minutes=duration)
            await member.timeout(until, reason=reason)
            embed = discord.Embed(
                title="Usuario silenciado",
                description=f"{member.mention} ha sido silenciado por {duration} minutos\nRazón: {reason}",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("No tengo permisos para silenciar a este usuario.")
        except Exception as e:
            logger.error(f"Error al silenciar: {e}")
            await ctx.send(f"Error al silenciar al usuario: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
