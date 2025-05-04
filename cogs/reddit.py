import random
import aiohttp
import discord
from discord.ext import commands
import typing as t
from collections import deque
import json
from aiohttp import ContentTypeError  # Importación explícita para usar en el manejo de errores


# Diccionario para almacenar las últimas URLs mostradas por subreddit
recent_posts = {}

async def get_sub_images(subreddit) -> t.Tuple[discord.Embed, discord.ui.View]:
    # Inicializar el deque para este subreddit si no existe
    if subreddit not in recent_posts:
        recent_posts[subreddit] = deque(maxlen=50)  # Almacenar hasta 50 posts recientes
    
    # Obtener posts del subreddit
    posts = []
    excluded_urls = list(recent_posts[subreddit]) if recent_posts[subreddit] else []
    
    # Parámetros para aumentar la variabilidad
    sort_options = ['hot', 'new', 'top', 'rising']
    time_options = ['hour', 'day', 'week', 'month', 'year', 'all']
    
    # Seleccionar parámetros aleatorios para más variedad
    selected_sort = random.choice(sort_options)
    selected_time = random.choice(time_options) if selected_sort == 'top' else ''
    limit_param = f"?sort={selected_sort}&limit=100"
    
    # Añadir parámetro de tiempo si es necesario
    if selected_time:
        limit_param += f"&t={selected_time}"
    
    # User-Agent actualizado y más detallado - más aleatorio para evitar bloqueos
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Intentar con varias URLs para aumentar las posibilidades de éxito
    urls_to_try = [
        f'https://www.reddit.com/r/{subreddit}/{selected_sort}.json{limit_param}',
        f'https://old.reddit.com/r/{subreddit}/hot.json?limit=100',
        f'https://www.reddit.com/r/{subreddit}/top.json?t=week&limit=100',
        f'https://www.reddit.com/r/{subreddit}.json?limit=100'
    ]
    
    # Intentar cada URL hasta encontrar posts
    for reddit_url in urls_to_try:
        if posts:  # Si ya tenemos posts, no seguir intentando
            break
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(reddit_url, headers=headers, allow_redirects=True, timeout=10) as response:
                    if response.status == 200:
                        try:
                            # Intentar decodificar JSON independientemente del content-type
                            data = await response.json(content_type=None)
                            
                            # Procesar los posts
                            if 'data' in data and 'children' in data['data']:
                                for i in data['data']['children']:
                                    # Filtrar solo posts con imágenes y que no estén en el historial
                                    if 'data' in i and i['data'].get('url') and i['data']['url'] not in excluded_urls:
                                        # Verificar que la URL termina con una extensión de imagen común
                                        url = i['data']['url'].lower()
                                        is_image = any(url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) or 'imgur.com' in url or 'i.redd.it' in url
                                        
                                        # También comprobar si hay una URL de preview disponible para casos donde la URL principal no es una imagen
                                        has_preview = False
                                        preview_url = None
                                        
                                        if 'preview' in i['data'] and 'images' in i['data']['preview'] and i['data']['preview']['images']:
                                            image_data = i['data']['preview']['images'][0]
                                            if 'source' in image_data and 'url' in image_data['source']:
                                                preview_url = image_data['source']['url'].replace('&amp;', '&')
                                                has_preview = True
                                        
                                        # Si es una imagen directa o tiene preview, agregarla
                                        if is_image or has_preview:
                                            post_data = i['data'].copy()
                                            # Si no es una imagen directa pero tiene preview, usar esa URL
                                            if not is_image and has_preview:
                                                post_data['original_url'] = post_data['url']  # Guardar la URL original
                                                post_data['url'] = preview_url  # Usar la URL de la preview
                                            posts.append(post_data)
                            
                        except json.JSONDecodeError:
                            print(f"JSON decode error with {reddit_url}. Trying next URL...")
                            continue
                    else:
                        print(f"HTTP error {response.status} with {reddit_url}. Trying next URL...")
                        continue
        
        except (aiohttp.ClientError, ContentTypeError, asyncio.TimeoutError) as e:
            print(f"Network error with {reddit_url}: {str(e)}. Trying next URL...")
            continue
    
    # Si no hay posts, probar con subreddits alternativos
    if not posts and subreddit in ['Animemes', 'goodanimemes', 'AnimeFunny', 'anime_irl']:
        # Lista ampliada de subreddits de anime con memes
        alt_anime_subs = ['Animemes', 'goodanimemes', 'AnimeFunny', 'anime_irl', 
                          'animememes', 'wholesomeanimemes', 'AnimeNoContext',
                          'weebmemes', 'animemebank', 'EliteWeebs']
        
        # Excluir el subreddit actual
        alt_subs = [s for s in alt_anime_subs if s.lower() != subreddit.lower()]
        
        if alt_subs:
            # Intentar con un subreddit alternativo
            alt_subreddit = random.choice(alt_subs)
            print(f"No posts found in r/{subreddit}, trying r/{alt_subreddit} instead...")
            return await get_sub_images(alt_subreddit)
    
    if not posts:
        # Si aún no hay posts, enviar un mensaje de error personalizado con sugerencias
        alt_suggestions = ""
        if subreddit == "AnimeFunny":
            alt_suggestions = "\n\nPrueba con estos comandos en su lugar:\n`animeme` - Memes de anime de varios subreddits\n`waifu` - Imágenes de waifus\n`maid` - Imágenes de maids"
        
        embed = discord.Embed(
            title="No se encontraron imágenes",
            description=f"No se encontraron imágenes en r/{subreddit}. Intenta con otro subreddit.{alt_suggestions}",
            color=discord.Color.orange()
        )
        view = discord.ui.View()
        return embed, view
    
    # Seleccionar un post aleatorio
    post = random.choice(posts)

    # Guardar la URL en el historial reciente
    recent_posts[subreddit].append(post['url'])
    
    # Crear un identificador único para seguimiento
    unique_id = random.randint(1000, 9999)
    
    # Crear el embed con la información del post
    embed = discord.Embed(color=discord.Color.random())  # Color aleatorio para más variedad
    embed.title = f"{post['title']}"
    embed.set_image(url=post['url'])
    
    # Añadir la URL original si se usó una preview
    permalink = post['permalink']
    if 'original_url' in post:
        footer_text = f"r/{subreddit} | {post['score']} votos | {post['num_comments']} comentarios | ID: {unique_id}"
    else:
        footer_text = f"r/{subreddit} | {post['score']} votos | {post['num_comments']} comentarios | ID: {unique_id}"
        
    embed.set_footer(text=footer_text)
    
    view = discord.ui.View()
    btn = discord.ui.Button(style=discord.ButtonStyle.url, url=('https://reddit.com' + permalink),
                          label="Ver post original")
    view.add_item(btn)
    return embed, view

# Función auxiliar para solicitudes de fallback a Reddit
async def fallback_reddit_request(subreddit, headers, posts, excluded_urls):
    fallback_url = f'https://www.reddit.com/r/{subreddit}.json?limit=50'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(fallback_url, headers=headers) as fallback_response:
                if fallback_response.status == 200:
                    try:
                        data = await fallback_response.json(content_type=None)
                        if 'data' in data and 'children' in data['data']:
                            for i in data['data']['children']:
                                if i['data'].get('url') and i['data']['url'] not in excluded_urls:
                                    url = i['data']['url'].lower()
                                    if any(url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) or 'imgur.com' in url or 'i.redd.it' in url:
                                        posts.append(i['data'])
                    except:
                        # Silenciar errores del fallback, se manejará después
                        pass
    except:
        # Silenciar errores del fallback, se manejará después
        pass


class Reddit(
    commands.GroupCog,
    group_name="reddit",
    command_attrs={
        'cooldown': commands.CooldownMapping.from_cooldown(
            1, 5, commands.BucketType.user
        )
    },
):
    """
    Comandos referentes a subreddits.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Lista de subreddits alternativos para aumentar la variedad
        self.alt_subreddits = {
            'hmmm': ['hmmm', 'hmm', 'Hmmmmm', 'hmmmm'],
            'animemes': ['animemes', 'Animemes', 'goodanimemes', 'AnimeFunny', 'anime_irl', 'wholesomeanimemes'],
            'antimeme': ['antimeme', 'bonehurtingjuice', 'speedoflobsters'],
            'greentext': ['greentext', '4chan', 'classic4chan'],
            'SpanishMeme': ['SpanishMeme', 'yo_elvr', 'LatinoPeopleTwitter', 'memesmexico'],
            'wholesomememes': ['wholesomememes', 'MadeMeSmile', 'wholesome', 'wholesomegifs']
        }

    # Comandos que envían memes

    # Construcción para comando nya>meme

    # Construcción para comando nya>animeme
    @commands.hybrid_command(name='animeme', description="Enviaré un meme otaku de r/animemes")
    async def animeme(self, ctx: commands.Context):
        async with ctx.typing():
            # Seleccionar un subreddit aleatorio de la lista de alternativas para mayor variedad
            selected_subreddit = random.choice(self.alt_subreddits['animemes'])
            embed, view = await get_sub_images(selected_subreddit)
            await ctx.send(embed=embed, view=view)

    # Construcción para comando nya>antimeme
    @commands.hybrid_command(name='antimeme', description="Kappa")
    async def antimeme(self, ctx: commands.Context):
        async with ctx.typing():
            # Seleccionar un subreddit aleatorio de la lista de alternativas para mayor variedad
            selected_subreddit = random.choice(self.alt_subreddits['antimeme'])
            embed, view = await get_sub_images(selected_subreddit)
            await ctx.send(embed=embed, view=view)

    # Construcción para comando nya>hmmm
    @commands.hybrid_command(name='hmmm', description="Hmmm...")
    async def hmmm(self, ctx: commands.Context):
        async with ctx.typing():
            # Seleccionar un subreddit aleatorio de la lista de alternativas para mayor variedad
            selected_subreddit = random.choice(self.alt_subreddits['hmmm'])
            embed, view = await get_sub_images(selected_subreddit)
            await ctx.send(embed=embed, view=view)

    # Construcción para comando nya>chantext
    @commands.hybrid_command(name='chantext', description="Extractos de 4chan en r/greentext")
    async def chantext(self, ctx: commands.Context):
        async with ctx.typing():
            # Seleccionar un subreddit aleatorio de la lista de alternativas para mayor variedad
            selected_subreddit = random.choice(self.alt_subreddits['greentext'])
            embed, view = await get_sub_images(selected_subreddit)
            await ctx.send(embed=embed, view=view)

    # Construcción para comando nya>hispameme
    @commands.command(name='hispameme', description="Memes hispanos")
    async def hispameme(self, ctx: commands.Context):
        async with ctx.typing():
            # Seleccionar un subreddit aleatorio de la lista de alternativas para mayor variedad
            selected_subreddit = random.choice(self.alt_subreddits['SpanishMeme'])
            embed, view = await get_sub_images(selected_subreddit)
            await ctx.send(embed=embed, view=view)

    # Construcción para comando nya>wholesome
    @commands.command(name='wholesome', description="Un poquito del lado bueno de internet.")
    async def wholesome(self, ctx: commands.Context):
        async with ctx.typing():
            # Seleccionar un subreddit aleatorio de la lista de alternativas para mayor variedad
            selected_subreddit = random.choice(self.alt_subreddits['wholesomememes'])
            embed, view = await get_sub_images(selected_subreddit)
            await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Reddit(bot))