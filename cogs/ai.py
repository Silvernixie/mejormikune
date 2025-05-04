import discord
from discord.ext import commands
import aiohttp
import os
import logging
import urllib.parse
import random

logger = logging.getLogger('MIKUNE 2')

class AI(commands.Cog):
    """Comandos relacionados con inteligencia artificial"""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.image_services = [
            # Servicio principal de Pollinations.ai
            lambda prompt: f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}",
            # Servicio alternativo de Lexica.art (fallback)
            lambda prompt: f"https://lexica.art/api/v1/search?q={urllib.parse.quote(prompt)}"
        ]
        self.current_service = 0  # Índice del servicio actual

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command(name="chat")
    async def chat(self, ctx, *, prompt: str):
        """Conversa con la IA"""
        async with ctx.typing():
            try:
                # Placeholder for actual API implementation
                response = f"¡Hola {ctx.author.name}! Este es un mensaje de prueba de la IA. Implementa tu propia integración con un modelo de IA aquí."
                await ctx.reply(response)
            except Exception as e:
                logger.error(f"Error en comando chat: {e}")
                await ctx.reply("Ocurrió un error al procesar tu solicitud.")

    @commands.command(name="imagen")
    async def generate_image(self, ctx, *, prompt: str):
        """Genera una imagen con IA"""
        async with ctx.typing():
            try:
                # Añadir detalles al prompt para mejor calidad
                enhanced_prompt = f"{prompt}, high quality, detailed, 4k"
                
                # Obtener URL del servicio de imágenes
                service_func = self.image_services[self.current_service]
                api_url = service_func(enhanced_prompt)
                
                # Verificar si estamos usando el servicio alternativo (Lexica)
                if self.current_service == 1:
                    # Para Lexica, necesitamos obtener la imagen de la respuesta JSON
                    async with self.session.get(api_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and data.get('images') and len(data['images']) > 0:
                                # Seleccionar una imagen aleatoria de los resultados
                                random_image = random.choice(data['images'])
                                api_url = random_image.get('src', "https://via.placeholder.com/512x512?text=Error+al+generar+imagen")
                            else:
                                raise Exception("No se encontraron imágenes")
                        else:
                            raise Exception(f"Error API: {response.status}")
                
                # Crear un embed con la imagen generada
                embed = discord.Embed(
                    title="Imagen generada con IA",
                    description=f"**Prompt:** {prompt}",
                    color=discord.Color.purple()
                )
                embed.set_image(url=api_url)
                embed.set_footer(text=f"Solicitado por {ctx.author.name}")
                
                await ctx.reply(embed=embed)
                
                # Si el comando funciona, volvemos al servicio principal para el próximo intento
                self.current_service = 0
                
            except Exception as e:
                logger.error(f"Error en comando imagen: {e}")
                
                # Si ocurre un error, cambiamos al servicio alternativo
                self.current_service = (self.current_service + 1) % len(self.image_services)
                
                # Intentamos nuevamente con el servicio alternativo si falló el principal
                if self.current_service != 0:
                    return await self.generate_image(ctx, prompt=prompt)
                else:
                    await ctx.reply("Lo siento, ocurrió un error al generar la imagen. Intenta con un prompt diferente.")

    @commands.command(name="imagine")
    async def imagine(self, ctx, *, prompt: str):
        """Alias para el comando imagen"""
        await self.generate_image(ctx, prompt=prompt)

async def setup(bot):
    await bot.add_cog(AI(bot))
