from datetime import datetime
import animec
import discord
import waifuim
import random
from collections import deque
from discord.ext import commands


class Anime(
    commands.Cog,
    command_attrs={
        'cooldown': commands.CooldownMapping.from_cooldown(
            1, 10, commands.BucketType.user
        )
    },
):
    """
    Comandos relacionados a cosas de anime.

    Cooldown: 10s per command
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.waifu = waifuim.WaifuAioClient()
        # Almacenar las últimas imágenes mostradas para evitar repeticiones (aumentado para mayor variedad)
        self.recent_waifu_images = deque(maxlen=50)
        self.recent_maid_images = deque(maxlen=50)
        # Tags adicionales para aumentar la variabilidad
        self.waifu_alt_tags = ['waifu', 'mori-calliope', 'raiden-shogun', 'oppai', 'selfies', 'uniform']
        self.maid_alt_tags = ['maid', 'marin-kitagawa', 'waifu', 'uniform']

    @commands.hybrid_command(aliases=['anisearch', 'animesearch'],
                             description="Búsqueda rápida de un anime. "
                                         "Asegúrate de escribir bien el nombre de lo que buscas.")
    # @commands.is_nsfw()
    async def search(self, ctx: commands.Context, *, name):
        async with ctx.typing():
            try:
                anime = animec.Anime(name)
            except:
                await ctx.send(
                    embed=discord.Embed(
                        description='<:notlikethis:868575058283597904> No encontré el anime que estás buscando.',
                        color=discord.Color.red(),
                    )
                )
                return
        if anime.is_nsfw():
            await ctx.send(
                embed=discord.Embed(
                    description='🔞 No puedes buscar animes nsfw con este comando.',
                    color=discord.Color.red(),
                )
            )
        else:
            embed = discord.Embed(
                title=f'{anime.title_jp} / {anime.title_english}',
                url=anime.url,
                description=f'{anime.description[:300]}...',
                color=discord.Color.random(),
            )
            # embed.add_field(name="#️⃣ Episodios:", value=(anime.episodes))
            embed.add_field(name='👉 Clasificación:', value=str(anime.rating))
            # embed.add_field(name="📊 Posición:", value=str(anime.ranked))
            embed.add_field(name='🔎 Estado:', value=str(anime.status))
            embed.add_field(
                name='🏷️ Géneros:',
                value=', '.join((anime.genres)) or 'No tiene géneros.',
            )
            embed.add_field(name='📺 Tipo:', value=str(anime.type))

            embed.set_thumbnail(url=anime.poster)
            await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=['anichar', 'animecharacter'],
                             description="Búsqueda rápida de un personaje de anime."
                                         "Asegúrate de escribir bien el nombre de lo que buscas.")
    async def character(self, ctx: commands.Context, *, name):
        async with ctx.typing():
            try:
                char = animec.Charsearch(name)
            except:
                await ctx.send(
                    embed=discord.Embed(
                        description='<:notlikethis:868575058283597904> No encontré al personaje que estás buscando.',
                        color=discord.Color.red(),
                    )
                )
                return
            embed = discord.Embed(
                title=char.title, url=char.url, color=discord.Color.random()
            )
            embed.set_image(url=char.image_url)
            embed.set_footer(text=', '.join(list(char.references.keys())[:2]))
            await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=['animenews'], description="Las noticias más nuevas del mundo del anime.")
    async def aninews(self, ctx: commands.Context, amount: int = 3):
        news = animec.Aninews(amount)
        links = news.links
        titles = news.titles
        descriptions = news.description

        embed = discord.Embed(
            title='Noticias más recientes de anime',
            color=discord.Color.random(),
            timestamp=datetime.utcnow(),
        )
        embed.set_thumbnail(url=news.images[0])
        embed.set_footer(
            text='Powered by Animec',
            icon_url='https://animec.readthedocs.io/en/latest/_static/animec.png',
        )

        for i in range(amount):
            embed.add_field(
                name=f'{i + 1}) {titles[i]}',
                value=f'{descriptions[i][:200]}...\n[Link]({links[i]})',
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='waifu', description="Imágenes aleatorias de waifus. ✨")
    async def waifu(self, ctx: commands.Context):
        # Excluir imágenes recientes para evitar repeticiones
        excluded_files = list(self.recent_waifu_images) if self.recent_waifu_images else None
        
        # Parámetros adicionales para aumentar la aleatoriedad
        order_options = ['RANDOM', 'FAVORITES', 'UPLOADED_AT']
        selected_order = random.choice(order_options)
        
        # Seleccionar tags aleatorios para mayor variedad
        selected_tags = [random.choice(self.waifu_alt_tags)]
        # Ocasionalmente añadir un segundo tag para más variedad (25% de probabilidad)
        if random.random() < 0.25:
            second_tag = random.choice([tag for tag in self.waifu_alt_tags if tag != selected_tags[0]])
            selected_tags.append(second_tag)
        
        # Orientaciones posibles para más variedad
        orientation_options = [None, 'PORTRAIT', 'LANDSCAPE']
        selected_orientation = random.choice(orientation_options)
        
        try:
            waifu = await self.waifu.search(
                included_tags=selected_tags, 
                excluded_tags=None,
                excluded_files=excluded_files,
                is_nsfw=False,
                order_by=selected_order,
                orientation=selected_orientation,
                many=False,
                full=True
            )
            
            # Guardar la imagen en el historial reciente
            if hasattr(waifu, 'file') and waifu.file:
                self.recent_waifu_images.append(waifu.file)
            elif hasattr(waifu, 'signature') and waifu.signature:
                self.recent_waifu_images.append(waifu.signature)
            
            # Añadir un identificador único para depuración y seguimiento
            unique_id = random.randint(1000, 9999)
            
            embed = discord.Embed(color=discord.Color.random())
            embed.set_image(url=waifu.url)
            embed.set_footer(text=f'✨ Tags: {", ".join(selected_tags)} | ID: {unique_id}\nAnime: {waifu.source if hasattr(waifu, "source") else "Unknown"}')
            await ctx.reply(embed=embed)
            
        except Exception as e:
            # Si hay un error, intentar con parámetros más simples
            fallback_tag = random.choice(self.waifu_alt_tags)
            waifu = await self.waifu.search(included_tags=[fallback_tag], is_nsfw=False)
            embed = discord.Embed(color=discord.Color.random())
            embed.set_image(url=waifu.url)
            embed.set_footer(text=f'✨ Tag: {fallback_tag}\nAnime: Unknown')
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name='maid', description="Imágenes aleatorias de maids. 🎀")
    async def maid(self, ctx: commands.Context):
        # Excluir imágenes recientes para evitar repeticiones
        excluded_files = list(self.recent_maid_images) if self.recent_maid_images else None
        
        # Parámetros adicionales para aumentar la aleatoriedad
        order_options = ['RANDOM', 'FAVORITES', 'UPLOADED_AT']
        selected_order = random.choice(order_options)
        
        # Seleccionar tags aleatorios para mayor variedad
        selected_tags = [random.choice(self.maid_alt_tags)]
        # Ocasionalmente añadir un segundo tag para más variedad (25% de probabilidad)
        if random.random() < 0.25:
            second_tag = random.choice([tag for tag in self.maid_alt_tags if tag != selected_tags[0]])
            selected_tags.append(second_tag)
        
        # Orientaciones posibles para más variedad
        orientation_options = [None, 'PORTRAIT', 'LANDSCAPE']
        selected_orientation = random.choice(orientation_options)
        
        try:
            maid = await self.waifu.search(
                included_tags=selected_tags, 
                excluded_tags=None,
                excluded_files=excluded_files,
                is_nsfw=False,
                order_by=selected_order,
                orientation=selected_orientation,
                many=False,
                full=True
            )
            
            # Guardar la imagen en el historial reciente
            if hasattr(maid, 'file') and maid.file:
                self.recent_maid_images.append(maid.file)
            elif hasattr(maid, 'signature') and maid.signature:
                self.recent_maid_images.append(maid.signature)
            
            # Añadir un identificador único para depuración y seguimiento
            unique_id = random.randint(1000, 9999)
            
            embed = discord.Embed(color=discord.Color.random())
            embed.set_image(url=maid.url)
            embed.set_footer(text=f'🎀 Tags: {", ".join(selected_tags)} | ID: {unique_id}\nAnime: {maid.source if hasattr(maid, "source") else "Unknown"}')
            await ctx.reply(embed=embed)
            
        except Exception as e:
            # Si hay un error, intentar con parámetros más simples
            fallback_tag = random.choice(self.maid_alt_tags)
            maid = await self.waifu.search(included_tags=[fallback_tag], is_nsfw=False)
            embed = discord.Embed(color=discord.Color.random())
            embed.set_image(url=maid.url)
            embed.set_footer(text=f'🎀 Tag: {fallback_tag}\nAnime: Unknown')
            await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Anime(bot))
