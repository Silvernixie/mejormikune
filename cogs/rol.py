import aiohttp
import discord
from discord.ext import commands
import typing as t
from asyncdagpi import ImageFeatures
import os
import json
from asyncdagpi import Client
from dotenv import load_dotenv

load_dotenv()

# Ruta al archivo JSON para almacenar datos de interacciones
INTERACTIONS_FILE = 'data/interactions.json'

# Asegurar que el directorio data existe
os.makedirs(os.path.dirname(INTERACTIONS_FILE), exist_ok=True)

# Cargar o crear el archivo de interacciones
def load_interactions():
    try:
        with open(INTERACTIONS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Guardar datos de interacciones
def save_interactions(data):
    with open(INTERACTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Clase personalizada para los botones de interacción
class InteractionView(discord.ui.View):
    def __init__(self, cog, action_type, author, target, timeout=60):
        super().__init__(timeout=timeout)  # Los botones expiran tras 1 minuto
        self.cog = cog
        self.action_type = action_type
        self.author = author
        self.target = target
        
    @discord.ui.button(label="Corresponder", style=discord.ButtonStyle.success, emoji="💖")
    async def correspond_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Solo el usuario objetivo puede interactuar con los botones
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("¡No puedes usar este botón! No es para ti.", ephemeral=True)
        
        # Simular el comando correspond
        action = {
            "type": self.action_type,
            "author": self.author.name,
            "author_id": self.author.id
        }
        
        # Obtener el recuento y aumentarlo
        count = self.cog.increment_interaction(self.action_type, str(self.target.id), str(self.author.id))
        count_text = self.cog.get_interaction_text(self.action_type, count)
        
        # Desactivar todos los botones
        for child in self.children:
            child.disabled = True
        
        # Actualizar el mensaje
        await interaction.response.edit_message(view=self)
        
        # Enviar la respuesta correspondiente según el tipo de acción
        if self.action_type == "kiss":
            async with self.cog.session.get(
                'https://nekos.best/api/v2/kiss?amount=1'
            ) as r:
                data = await r.json()
                kiss = data['results'][0]['url']
                embed = discord.Embed(
                    description=f'💖 **{interaction.user.name}** correspondió el beso de **{self.author.name}**\n{count_text}\n{self.author.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=kiss)
                embed.set_footer(text='')
                await interaction.followup.send(embed=embed)
                
        elif self.action_type == "hug":
            async with self.cog.session.get(
                'https://api.waifu.pics/sfw/hug'
            ) as r:
                data = await r.json()
                hug = data['url']
                embed = discord.Embed(
                    description=f'🤗 ¡**{interaction.user.name}** correspondió el abrazo de **{self.author.name}**!\n{count_text}\n{self.author.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=hug)
                embed.set_footer(text='')
                await interaction.followup.send(embed=embed)
                
        elif self.action_type == "pat":
            async with self.cog.session.get(
                'https://nekos.best/api/v2/pat?amount=1'
            ) as r:
                data = await r.json()
                pat = data['results'][0]['url']
                embed = discord.Embed(
                    description=f'❣️ **{interaction.user.name}** correspondió los pat-pats de **{self.author.name}**\n{count_text}\n{self.author.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=pat)
                embed.set_footer(text='')
                await interaction.followup.send(embed=embed)
                
        elif self.action_type == "cuddle":
            async with self.cog.session.get(
                'https://nekos.best/api/v2/cuddle?amount=1'
            ) as r:
                data = await r.json()
                cuddle = data['results'][0]['url']
                embed = discord.Embed(
                    description=f'💞 **{interaction.user.name}** correspondió el cariño de **{self.author.name}**\n{count_text}\n{self.author.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=cuddle)
                embed.set_footer(text='')
                await interaction.followup.send(embed=embed)
                
        elif self.action_type == "tickle":
            async with self.cog.session.get(
                'https://nekos.best/api/v2/tickle?amount=1'
            ) as r:
                data = await r.json()
                tickle = data['results'][0]['url']
                embed = discord.Embed(
                    description=f'🤣 ¡**{interaction.user.name}** le devolvió las cosquillas a **{self.author.name}**!\n{count_text}\n{self.author.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=tickle)
                embed.set_footer(text='')
                await interaction.followup.send(embed=embed)
                
        elif self.action_type == "poke":
            async with self.cog.session.get(
                'https://api.waifu.pics/sfw/poke'
            ) as r:
                data = await r.json()
                poke = data['url']
                embed = discord.Embed(
                    description=f'👉 ¡**{interaction.user.name}** también molestó a **{self.author.name}**!\n{count_text}\n{self.author.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=poke)
                embed.set_footer(text='')
                await interaction.followup.send(embed=embed)
                
        elif self.action_type == "handhold":
            async with self.cog.session.get(
                'https://api.waifu.pics/sfw/handhold'
            ) as r:
                data = await r.json()
                hand = data['url']
                embed = discord.Embed(
                    description=f'😳 ¡**{interaction.user.name}** también tomó la mano de **{self.author.name}**!\n{count_text}\n{self.author.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=hand)
                embed.set_footer(text='')
                await interaction.followup.send(embed=embed)
                
        elif self.action_type == "highfive":
            async with self.cog.session.get(
                'https://api.waifu.pics/sfw/highfive'
            ) as r:
                data = await r.json()
                five = data['url']
                embed = discord.Embed(
                    description=f'🖐️ ¡**{interaction.user.name}** devolvió el high five a **{self.author.name}**!\n{count_text}\n{self.author.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=five)
                embed.set_footer(text='')
                await interaction.followup.send(embed=embed)
                
        elif self.action_type == "feed":
            async with self.cog.session.get(
                'https://nekos.best/api/v2/feed?amount=1'
            ) as r:
                data = await r.json()
                feed = data['results'][0]['url']
                embed = discord.Embed(
                    description=f'🥄 ¡**{interaction.user.name}** también alimentó a **{self.author.name}**!\n{count_text}\n{self.author.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=feed)
                embed.set_footer(text='')
                await interaction.followup.send(embed=embed)
                
        elif self.action_type == "bonk":
            embed = discord.Embed(color=discord.Colour.random())
            embed.description = f'🏏 **¡CONTRA-BONK!** {interaction.user.name} ha devuelto el bonk a {self.author.name}\n{self.author.mention}'
            embed.set_image(url="https://media.tenor.com/CrmEU2LKix8AAAAC/bonk-anime.gif")
            embed.set_footer(text='')
            await interaction.followup.send(embed=embed)
        
        # Eliminar la acción pendiente
        if interaction.user.id in self.cog.pending_actions:
            del self.cog.pending_actions[interaction.user.id]
            
    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.danger, emoji="💔")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Solo el usuario objetivo puede interactuar con los botones
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("¡No puedes usar este botón! No es para ti.", ephemeral=True)
        
        # Desactivar todos los botones
        for child in self.children:
            child.disabled = True
        
        # Actualizar el mensaje
        await interaction.response.edit_message(view=self)
        
        # Enviar mensaje de rechazo
        async with interaction.client.http._HTTPClient__session.get(
            'https://api.waifu.pics/sfw/cry'
        ) as r:
            data = await r.json()
            cry = data['url']
            embed = discord.Embed(
                description=f'💔 **{interaction.user.name}** ha rechazado la acción de **{self.author.name}**\n{self.author.mention}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=cry)
            embed.set_footer(text='')
            await interaction.followup.send(embed=embed)
        
        # Eliminar la acción pendiente
        if interaction.user.id in self.cog.pending_actions:
            del self.cog.pending_actions[interaction.user.id]

class Rol(
    commands.Cog,
    command_attrs={
        'cooldown': commands.CooldownMapping.from_cooldown(
            1, 5, commands.BucketType.user
        ),
        'hidden': False
    },
):
    """
    Reacciones de anime para rol y cosas divertidas.
    Ten en cuenta que para algunos comandos tendrás que etiquetar a otros ||o puedes probar y no hacerlo para ver que pasa||.

    Comandos disponibles:
    - correspond/corresponder: Corresponde a la última acción recibida
    - reject/rechazar: Rechaza la última acción recibida
    - kiss: Envía un beso a alguien
    - hug: Envía un abrazo a alguien
    - bite/ñam: Muerde a alguien
    - dance/party: Baila solo o con alguien
    - pat/headpat: Da pat-pats a alguien
    - cuddle: Abraza cariñosamente a alguien
    - tickle: Haz cosquillas a alguien
    - poke: Molesta a alguien
    - handhold: Toma de la mano a alguien
    - highfive: Choca los cinco con alguien
    - feed: Alimenta a alguien

    Cooldown: 5s por comando
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.pending_actions = {} # Almacenar acciones pendientes con {user_id: {"type": action_type, "author": author_name, "author_id": author_id}}
        self.dagpi = Client(os.environ['DAGPI'])
        self.interactions_data = load_interactions()

    def get_interaction_count(self, interaction_type: str, user1_id: str, user2_id: str):
        """Obtener el conteo de interacciones entre dos usuarios"""
        pair_id = f"{min(user1_id, user2_id)}-{max(user1_id, user2_id)}"
        if interaction_type not in self.interactions_data:
            self.interactions_data[interaction_type] = {}
        return self.interactions_data[interaction_type].get(pair_id, 0)

    def increment_interaction(self, interaction_type: str, user1_id: str, user2_id: str):
        """Incrementar el conteo de interacciones entre dos usuarios"""
        pair_id = f"{min(user1_id, user2_id)}-{max(user1_id, user2_id)}"
        if interaction_type not in self.interactions_data:
            self.interactions_data[interaction_type] = {}
        self.interactions_data[interaction_type][pair_id] = self.interactions_data[interaction_type].get(pair_id, 0) + 1
        save_interactions(self.interactions_data)
        return self.interactions_data[interaction_type][pair_id]

    def get_interaction_text(self, interaction_type: str, count: int) -> str:
        """Obtener el texto personalizado para cada tipo de interacción"""
        texts = {
            "kiss": f"¡Se han besado **{count}** veces!",
            "hug": f"¡Se han abrazado **{count}** veces!",
            "pat": f"¡Le ha dado pat-pats **{count}** veces!",
            "cuddle": f"¡Se han mimado **{count}** veces!",
            "tickle": f"¡Se han hecho cosquillas **{count}** veces!",
            "poke": f"¡Se han molestado **{count}** veces!",
            "handhold": f"¡Se han tomado de las manos **{count}** veces!",
            "highfive": f"¡Han chocado los cinco **{count}** veces!",
            "feed": f"¡Se han alimentado **{count}** veces!"
        }
        return texts.get(interaction_type, "")

    @commands.hybrid_command(name='correspond', aliases=['corresponder'], description="Corresponde a la última acción que te hicieron")
    async def correspond(self, ctx: commands.Context):
        if ctx.author.id not in self.pending_actions:
            return await ctx.reply("No tienes ninguna acción pendiente para corresponder 😔")
        
        action = self.pending_actions[ctx.author.id]
        original_user = self.bot.get_user(action['author_id'])
        if not original_user:
            original_user = await self.bot.fetch_user(action['author_id'])
        
        # Incrementar el conteo al corresponder
        count = self.increment_interaction(action["type"], str(ctx.author.id), str(action['author_id']))
        count_text = self.get_interaction_text(action["type"], count)

        if action["type"] == "kiss":
            async with ctx.typing() and self.session.get(
                'https://nekos.best/api/v2/kiss?amount=1'
            ) as r:
                data = await r.json()
                kiss = data['results'][0]['url']
                embed = discord.Embed(
                    description=f'💖 **{ctx.author.name}** correspondió el beso de **{action["author"]}**\n{count_text}\n{original_user.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=kiss)
                embed.set_footer(text='')
                await ctx.send(embed=embed)

        elif action["type"] == "hug":
            async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/hug'
            ) as r:
                data = await r.json()
                hug = data['url']
                embed = discord.Embed(
                    description=f'🤗 ¡**{ctx.author.name}** correspondió el abrazo de **{action["author"]}**!\n{count_text}\n{original_user.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=hug)
                embed.set_footer(text='')
                await ctx.send(embed=embed)

        elif action["type"] == "pat":
            async with ctx.typing() and self.session.get(
                'https://nekos.best/api/v2/pat?amount=1'
            ) as r:
                data = await r.json()
                pat = data['results'][0]['url']
                embed = discord.Embed(
                    description=f'❣️ **{ctx.author.name}** correspondió los pat-pats de **{action["author"]}**\n{count_text}\n{original_user.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=pat)
                embed.set_footer(text='')
                await ctx.send(embed=embed)

        elif action["type"] == "cuddle":
            async with ctx.typing() and self.session.get(
                'https://nekos.best/api/v2/cuddle?amount=1'
            ) as r:
                data = await r.json()
                cuddle = data['results'][0]['url']
                embed = discord.Embed(
                    description=f'💞 **{ctx.author.name}** correspondió el cariño de **{action["author"]}**\n{count_text}\n{original_user.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=cuddle)
                embed.set_footer(text='')
                await ctx.send(embed=embed)

        elif action["type"] == "bonk":
            embed = discord.Embed(color=discord.Colour.random())
            embed.description = f'🏏 **¡CONTRA-BONK!** {ctx.author.name} ha devuelto el bonk a {action["author"]}\n{original_user.mention}'
            embed.set_image(url="https://media.tenor.com/CrmEU2LKix8AAAAC/bonk-anime.gif")
            embed.set_footer(text=f'Solicitado por {ctx.author}')
            await ctx.send(embed=embed)

        elif action["type"] == "tickle":
            async with ctx.typing() and self.session.get(
                'https://nekos.best/api/v2/tickle?amount=1'
            ) as r:
                data = await r.json()
                tickle = data['results'][0]['url']
                embed = discord.Embed(
                    description=f'🤣 ¡**{ctx.author.name}** le devolvió las cosquillas a **{action["author"]}**!\n{count_text}\n{original_user.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=tickle)
                embed.set_footer(text='')
                await ctx.send(embed=embed)

        elif action["type"] == "poke":
            async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/poke'
            ) as r:
                data = await r.json()
                poke = data['url']
                embed = discord.Embed(
                    description=f'👉 ¡**{ctx.author.name}** también molestó a **{action["author"]}**!\n{count_text}\n{original_user.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=poke)
                embed.set_footer(text='')
                await ctx.send(embed=embed)

        elif action["type"] == "handhold":
            async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/handhold'
            ) as r:
                data = await r.json()
                hand = data['url']
                embed = discord.Embed(
                    description=f'😳 ¡**{ctx.author.name}** también tomó la mano de **{action["author"]}**!\n{count_text}\n{original_user.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=hand)
                embed.set_footer(text='')
                await ctx.send(embed=embed)

        elif action["type"] == "highfive":
            async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/highfive'
            ) as r:
                data = await r.json()
                five = data['url']
                embed = discord.Embed(
                    description=f'🖐️ ¡**{ctx.author.name}** devolvió el high five a **{action["author"]}**!\n{count_text}\n{original_user.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=five)
                embed.set_footer(text='')
                await ctx.send(embed=embed)

        elif action["type"] == "feed":
            async with ctx.typing() and self.session.get(
                'https://nekos.best/api/v2/feed?amount=1'
            ) as r:
                data = await r.json()
                feed = data['results'][0]['url']
                embed = discord.Embed(
                    description=f'🥄 ¡**{ctx.author.name}** también alimentó a **{action["author"]}**!\n{count_text}\n{original_user.mention}',
                    color=discord.Colour.random(),
                )
                embed.set_image(url=feed)
                embed.set_footer(text='')
                await ctx.send(embed=embed)

        # Eliminar la acción una vez correspondida
        del self.pending_actions[ctx.author.id]

    @commands.hybrid_command(name='reject', aliases=['rechazar'], description="Rechaza la última acción que te hicieron")
    async def reject(self, ctx: commands.Context):
        if ctx.author.id not in self.pending_actions:
            return await ctx.reply("No tienes ninguna acción pendiente para rechazar 😔")
        
        action = self.pending_actions[ctx.author.id]
        # Obtener el usuario original usando el ID
        original_user = self.bot.get_user(action['author_id'])
        if not original_user:
            original_user = await self.bot.fetch_user(action['author_id'])
        
        async with ctx.typing() and self.session.get(
            'https://api.waifu.pics/sfw/cry'
        ) as r:
            data = await r.json()
            cry = data['url']
            embed = discord.Embed(
                description=f'💔 **{ctx.author.name}** ha rechazado la acción de **{action["author"]}**\n{original_user.mention}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=cry)
            embed.set_footer(text='')
            await ctx.send(embed=embed)

        # Eliminar la acción una vez rechazada
        del self.pending_actions[ctx.author.id]

    @commands.hybrid_command(name='kiss', description="¿Son pareja? A ver, bésense")
    async def kiss(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes besarte a tí mismo!\nA no ser que uses algún espejo o algo parecido (￣▽￣*)ゞ'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
            'https://nekos.best/api/v2/kiss?amount=1'
        ) as r:
            data = await r.json()
            kiss = data['results'][0]['url']
            
            # Incrementar el conteo
            count = self.increment_interaction("kiss", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("kiss", count)
            
            embed = discord.Embed(
                description=f'💖 **{ctx.author.name}** ha besado a **{member.name}**~\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=kiss)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "kiss", 
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "kiss", ctx.author, member)
            await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='hug', description="¡Abrazos virtuales!")
    async def hug(self, ctx: commands.Context, member: discord.Member = None):
        if member == ctx.author:
            message = '¡No puedes abrazarte a tí mismo!\nAunque puedo darte un abrazo si quieres ヽ(・∀・)ﾉ'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/hug'
        ) as r:
            data = await r.json()
            hug = data['url']

            # Incrementar el conteo
            count = self.increment_interaction("hug", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("hug", count)

            embed = discord.Embed(
                description=f'🤗 ¡**{ctx.author.name}** ha abrazado a **{member.name}**!\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=hug)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "hug", 
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "hug", ctx.author, member)
            await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='bite', aliases=['ñam'], description="Ñam ñam ñam~")
    async def bite(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes morderte a tí mismo!\nY yo no tengo ganas de morder a nadie (´Д｀υ)'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/bite'
        ) as r:
            data = await r.json()
            bite = data['url']
            embed = discord.Embed(
                description=f'😏 ¡**{ctx.author.name}** ha mordido a **{member.name}**!',
                color=discord.Colour.random(),
            )
            embed.set_image(url=f'{bite}')
            embed.set_footer(text='')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='dance', aliases=['party'], description="¡Esto hay que celebrarlo!")
    async def dance(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/dance'
        ) as r:
            data = await r.json()
            dance = data['url']
            if not member or member == ctx.author:
                desc = f'🎉 ¡**{ctx.author.name}** se ha puesto a bailar!'
            else:
                desc = f'🎊 ¡**{ctx.author.name}** y **{member.name}** están bailando juntos!'
            embed = discord.Embed(
                description=f'{desc}', color=discord.Colour.random()
            )
            embed.set_image(url=f'{dance}')
            embed.set_footer(text='')
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='pat', aliases=['headpat'], description="¿Alguien se merece unos pat-pat?")
    async def pat(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes darte pat-pats a tí mismo!\nPero puede darme unos a mí (o´▽`o)'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://nekos.best/api/v2/pat?amount=1'
        ) as r:
            data = await r.json()
            pat = data['results'][0]['url']

            # Incrementar el conteo
            count = self.increment_interaction("pat", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("pat", count)

            embed = discord.Embed(
                description=f'❣️ **{ctx.author.name}** le ha dado unos pat-pats a **{member.name}**\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=pat)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "pat", 
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "pat", ctx.author, member)
            await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='cuddle', description="Abrazos pero con más cariño~")
    async def cuddle(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes darte cariños a tí mismo!\nPero puede darme unos a mí (o´▽`o)'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://nekos.best/api/v2/cuddle?amount=1'
        ) as r:
            data = await r.json()
            cuddle = data['results'][0]['url']

            # Incrementar el conteo
            count = self.increment_interaction("cuddle", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("cuddle", count)

            embed = discord.Embed(
                description=f'💞 **{ctx.author.name}** abraza con mucho cariño a **{member.name}**\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=cuddle)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "cuddle", 
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "cuddle", ctx.author, member)
            await ctx.send(embed=embed, view=view)
            
    @commands.hybrid_command(name='tickle', description="¡Hora de las cosquillas!")
    async def tickle(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes hacerte cosquillas a tí mismo!\nPero puedo hacerte unas si quieres (≧▽≦)'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://nekos.best/api/v2/tickle?amount=1'
        ) as r:
            data = await r.json()
            tickle = data['results'][0]['url']

            # Incrementar el conteo
            count = self.increment_interaction("tickle", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("tickle", count)

            embed = discord.Embed(
                description=f'🤣 ¡**{ctx.author.name}** le ha hecho cosquillas a **{member.name}**!\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=tickle)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "tickle", 
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "tickle", ctx.author, member)
            await ctx.send(embed=embed, view=view)
            
    @commands.hybrid_command(name='poke', description="Molesta a alguien con un toque")
    async def poke(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes molestarte a tí mismo!\nPero puedo molestarte yo si quieres (￣ω￣)'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/poke'
        ) as r:
            data = await r.json()
            poke = data['url']

            # Incrementar el conteo
            count = self.increment_interaction("poke", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("poke", count)

            embed = discord.Embed(
                description=f'👉 ¡**{ctx.author.name}** ha molestado a **{member.name}**!\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=poke)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "poke", 
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "poke", ctx.author, member)
            await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='slap', description="Porque a veces alguien necesita una cachetada (con cariño)")
    async def slap(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = (
                '¡No puedes pegarte a tí mismo!\nA no ser que te guste...'
            )
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
            'https://nekos.best/api/v2/slap?amount=1'
        ) as r:
            data = await r.json()
            slap = data['results'][0]['url']
            embed = discord.Embed(
                description=f'💢 **{ctx.author.name}** ha cacheteado a **{member.name}**',
                color=discord.Colour.random(),
            )
            embed.set_image(url=slap)
            embed.set_footer(text='')
            await ctx.send(embed=embed)
            
    @commands.hybrid_command(name='handhold', description="Toma la mano de alguien... ¡Qué atrevido!")
    async def handhold(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes tomarte de la mano a tí mismo!\nPero puedo tomar tu mano si quieres (⁄ ⁄•⁄ω⁄•⁄ ⁄)'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/handhold'
        ) as r:
            data = await r.json()
            hand = data['url']

            # Incrementar el conteo
            count = self.increment_interaction("handhold", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("handhold", count)

            embed = discord.Embed(
                description=f'😳 ¡**{ctx.author.name}** ha tomado la mano de **{member.name}**!\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=hand)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "handhold", 
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "handhold", ctx.author, member)
            await ctx.send(embed=embed, view=view)
            
    @commands.hybrid_command(name='highfive', description="¡Choca esos cinco!")
    async def highfive(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes chocar los cinco contigo mismo!\nPero puedo chocarlos yo contigo ✋'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/highfive'
        ) as r:
            data = await r.json()
            five = data['url']

            # Incrementar el conteo
            count = self.increment_interaction("highfive", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("highfive", count)

            embed = discord.Embed(
                description=f'🖐️ ¡**{ctx.author.name}** ha chocado los cinco con **{member.name}**!\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=five)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "highfive", 
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "highfive", ctx.author, member)
            await ctx.send(embed=embed, view=view)
            
    @commands.hybrid_command(name='feed', description="Alimenta a alguien con cariño")
    async def feed(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes alimentarte a tí mismo!\nPero puedo darte de comer yo si quieres 🍙'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://nekos.best/api/v2/feed?amount=1'
        ) as r:
            data = await r.json()
            feed = data['results'][0]['url']

            # Incrementar el conteo
            count = self.increment_interaction("feed", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("feed", count)

            embed = discord.Embed(
                description=f'🥄 ¡**{ctx.author.name}** ha alimentado a **{member.name}**!\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=feed)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "feed", 
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "feed", ctx.author, member)
            await ctx.send(embed=embed, view=view)
            
    @commands.hybrid_command(name='blush', aliases=['sonrojar'], description="Te has sonrojado... ¿Qué pasó?")
    async def blush(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/blush'
        ) as r:
            data = await r.json()
            blush = data['url']
            if not member or member == ctx.author:
                desc = f'😳 **{ctx.author.name}** se ha sonrojado'
            else:
                desc = f'😳 **{ctx.author.name}** se ha sonrojado por culpa de **{member.name}**'
            embed = discord.Embed(
                description=desc,
                color=discord.Colour.random(),
            )
            embed.set_image(url=blush)
            embed.set_footer(text='')
            await ctx.send(embed=embed)
            
    @commands.hybrid_command(name='cry', aliases=['llorar'], description="A veces hay que desahogarse...")
    async def cry(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/cry'
        ) as r:
            data = await r.json()
            cry = data['url']
            if not member or member == ctx.author:
                desc = f'😢 **{ctx.author.name}** está llorando'
            else:
                desc = f'😢 **{ctx.author.name}** está llorando por culpa de **{member.name}**'
            embed = discord.Embed(
                description=desc,
                color=discord.Colour.random(),
            )
            embed.set_image(url=cry)
            embed.set_footer(text='')
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='poke', description="¿Quieres llamar la atención de alguien?")
    async def poke(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes molestarte a tí mismo!'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/poke'
        ) as r:
            data = await r.json()
            poke = data['url']

            # Incrementar el conteo
            count = self.increment_interaction("poke", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("poke", count)

            embed = discord.Embed(
                description=f'👉 **{ctx.author.name}** está molestando a **{member.name}**\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=poke)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "poke",
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "poke", ctx.author, member)
            await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='blush', description="Rojo como tomate")
    async def blush(self, ctx: commands.Context):
        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/blush'
        ) as r:
            data = await r.json()
            blush = data['url']
            embed = discord.Embed(
                description=f'😳 **{ctx.author.name}** se ha puesto rojo como tomate',
                color=discord.Colour.random(),
            )
            embed.set_image(url=blush)
            embed.set_footer(text='')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='cry', aliases=['sad'], description=":(")
    async def cry(self, ctx: commands.Context):
        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/cry'
        ) as r:
            data = await r.json()
            cry = data['url']
            embed = discord.Embed(
                description=f'😭 **{ctx.author.name}** está llorando. Que alguien le consuele :(',
                color=discord.Colour.random(),
            )
            embed.set_image(url=cry)
            embed.set_footer(text='')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='feed', description="¿Quién tiene hambre?")
    async def feed(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        async with ctx.typing() and self.session.get(
                'https://nekos.best/api/v2/feed?amount=1'
        ) as r:
            data = await r.json()
            feed = data['results'][0]['url']

            if member and member != ctx.author:
                # Incrementar el conteo
                count = self.increment_interaction("feed", str(ctx.author.id), str(member.id))
                count_text = self.get_interaction_text("feed", count)

                desc = f'🥄 ¡**{ctx.author.name}** le está dando de comer a **{member.name}**!\n{count_text}'
                self.pending_actions[member.id] = {
                    "type": "feed",
                    "author": ctx.author.name,
                    "author_id": ctx.author.id
                }
                view = InteractionView(self, "feed", ctx.author, member)
                await ctx.send(embed=embed, view=view)
            else:
                desc = f'🍴 **{ctx.author.name}** está comiendo algo rico!'
            embed = discord.Embed(
                description=desc, color=discord.Colour.random()
            )
            embed.set_image(url=feed)
            embed.set_footer(text='')
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='smug', description=">;)")
    async def smug(self, ctx: commands.Context):
        async with ctx.typing() and self.session.get(
            'https://nekos.best/api/v2/smug?amount=1'
        ) as r:
            data = await r.json()
            smug = data['results'][0]['url']
            embed = discord.Embed(
                description=f'💯 **{ctx.author.name}** tiene mucha malicia',
                color=discord.Colour.random(),
            )
            embed.set_image(url=smug)
            embed.set_footer(text='')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='hi', aliases=['hola', 'hello', 'wave'], description="¡Hola a todos o a un usuario específico!")
    async def wave(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/wave'
        ) as r:
            data = await r.json()
            if member:
                description = f'👋 **{ctx.author.name}** saluda a **{member.name}**!'
            else:
                description = f'👋 **{ctx.author.name}** dice hola a todos!'
            hi = data['url']
            embed = discord.Embed(
                description=f'👋 **{ctx.author.name}** saluda a **{member.name}**!' if member else f'👋 **{ctx.author.name}** dice hola a todos!',
                color=discord.Colour.random(),
            )
            embed.set_image(url=hi)
            embed.set_footer(text='')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='yeet', description="YEET")
    async def yeet(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes hacerte yeet a tí mismo!'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/yeet'
        ) as r:
            data = await r.json()
            yeet = data['url']
            embed = discord.Embed(
                description=f'🚀 ¡**{ctx.author.name}** mandó a volar a **{member.name}**!',
                color=discord.Colour.random(),
            )
            embed.set_image(url=yeet)
            embed.set_footer(text='')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='handholding', description="[CENSORED]")
    async def handholding(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes tomar tu propia mano!\nBueno, si puedes pero ya sabes a lo que me refiero'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/handhold'
        ) as r:
            data = await r.json()
            hand = data['url']

            # Incrementar el conteo
            count = self.increment_interaction("handhold", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("handhold", count)

            embed = discord.Embed(
                description=f'😳 ¡**{ctx.author.name}** y **{member.name}** se están tomando las manos!\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=hand)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "handhold",
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "handhold", ctx.author, member)
            await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='happy', aliases=['smile'], description="¡Mira qué feliz soy!")
    async def happy(self, ctx: commands.Context):
        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/happy'
        ) as r:
            data = await r.json()
            happy = data['url']
            embed = discord.Embed(
                description=f'😊 **{ctx.author.name}** se siente muy feliz',
                color=discord.Colour.random(),
            )
            embed.set_image(url=happy)
            embed.set_footer(text='')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='wink', description=";)")
    async def wink(self, ctx: commands.Context):
        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/wink'
        ) as r:
            data = await r.json()
            wink = data['url']
            embed = discord.Embed(
                description=f'😉 **{ctx.author.name}** está intentando decir algo',
                color=discord.Colour.random(),
            )
            embed.set_image(url=wink)
            embed.set_footer(text='')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='cringe', description="C R I N G E")
    async def cringe(self, ctx: commands.Context):
        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/cringe'
        ) as r:
            data = await r.json()
            cringe = data['url']
            embed = discord.Embed(
                description=f'😒 **{ctx.author.name}** siente demasiado cringe',
                color=discord.Colour.random(),
            )
            embed.set_image(url=cringe)
            embed.set_footer(text='')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='bully', description="¿Quieres molestar a alguien?")
    async def bully(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes hacerte bullying a ti mismo!'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/bully'
        ) as r:
            data = await r.json()
            bully = data['url']
            embed = discord.Embed(
                description=f'🤭 **{ctx.author.name}** le hace bullying a **{member.name}**',
                color=discord.Colour.random(),
            )
            embed.set_image(url=bully)
            embed.set_footer(text='')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='highfive', aliases=['five'], description="¡Chócalas!")
    async def highfive(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡Necesitas chocar las manos con alguien más!'
            return await ctx.reply(message)
        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        async with ctx.typing() and self.session.get(
                'https://api.waifu.pics/sfw/highfive'
        ) as r:
            data = await r.json()
            five = data['url']

            # Incrementar el conteo
            count = self.increment_interaction("highfive", str(ctx.author.id), str(member.id))
            count_text = self.get_interaction_text("highfive", count)

            embed = discord.Embed(
                description=f'🖐️ **{ctx.author.name}** quiere chocar los cinco con **{member.name}**\n{count_text}',
                color=discord.Colour.random(),
            )
            embed.set_image(url=five)
            embed.set_footer(text='')
            self.pending_actions[member.id] = {
                "type": "highfive",
                "author": ctx.author.name,
                "author_id": ctx.author.id
            }
            view = InteractionView(self, "highfive", ctx.author, member)
            await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='bonk', description="¡Dale un bonk a alguien que se lo merece!")
    async def bonk(self, ctx: commands.Context, member: t.Optional[discord.Member] = None):
        if member == ctx.author:
            message = '¡No puedes darte un bonk a tí mismo!\nPuedo dártelo yo si quieres (￣ω￣)'
            return await ctx.reply(message)

        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien!')

        embed = discord.Embed(color=discord.Colour.random())
        embed.description = f'🏏 **¡BONK!** {ctx.author.name} ha dado un bonk a {member.name}'
        embed.set_image(url="https://media.tenor.com/CrmEU2LKix8AAAAC/bonk-anime.gif")
        embed.set_footer(text=f'Solicitado por {ctx.author}')
        
        self.pending_actions[member.id] = {
            "type": "bonk", 
            "author": ctx.author.name,
            "author_id": ctx.author.id
        }
        view = InteractionView(self, "bonk", ctx.author, member)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Rol(bot))
