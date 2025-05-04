import os
from typing import Union
import discord
from asyncdagpi import Client, ImageFeatures
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Verificar que la API key existe
DAGPI_KEY = os.environ.get('DAGPI')
if not DAGPI_KEY:
    print("⚠️ Advertencia: La API key de DAGPI no está configurada en el archivo .env")
    DAGPI_KEY = "missingkey"  # Valor temporal para prevenir errores iniciales

dagpi = Client(DAGPI_KEY)

# Definimos una clase InteractionView importable directamente aquí para evitar dependencias circulares
class InteractionView(discord.ui.View):
    def __init__(self, cog, action_type, author, target, timeout=60):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.action_type = action_type
        self.author = author
        self.target = target
        
    @discord.ui.button(label="Corresponder", style=discord.ButtonStyle.success, emoji="💖")
    async def correspond_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Solo el usuario objetivo puede interactuar con los botones
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("¡No puedes usar este botón! No es para ti.", ephemeral=True)
        
        # Desactivar todos los botones
        for child in self.children:
            child.disabled = True
        
        # Actualizar el mensaje
        await interaction.response.edit_message(view=self)
        
        # Para bonk específicamente
        if self.action_type == "bonk":
            embed = discord.Embed(color=discord.Colour.random())
            embed.description = f'🏏 **¡CONTRA-BONK!** {interaction.user.name} ha devuelto el bonk a {self.author.name}\n{self.author.mention}'
            embed.set_image(url="https://media.tenor.com/CrmEU2LKix8AAAAC/bonk-anime.gif")
            embed.set_footer(text='')
            await interaction.followup.send(embed=embed)
            
            # Eliminar la acción pendiente si existe el cog Rol
            rol_cog = interaction.client.get_cog('Rol')
            if rol_cog and interaction.user.id in rol_cog.pending_actions:
                del rol_cog.pending_actions[interaction.user.id]
            
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
        
        # Enviar mensaje de rechazo genérico
        embed = discord.Embed(
            description=f'💔 **{interaction.user.name}** ha rechazado la acción de **{self.author.name}**\n{self.author.mention}',
            color=discord.Colour.random(),
        )
        embed.set_image(url="https://i.pinimg.com/originals/d7/34/58/d73458acf4e49214f89ee53ce4c1a089.gif")
        embed.set_footer(text='')
        await interaction.followup.send(embed=embed)
        
        # Eliminar la acción pendiente si existe el cog Rol
        rol_cog = interaction.client.get_cog('Rol')
        if rol_cog and interaction.user.id in rol_cog.pending_actions:
            del rol_cog.pending_actions[interaction.user.id]

class Image(
    commands.Cog,
    command_attrs={
        'cooldown': commands.CooldownMapping.from_cooldown(
            1, 10, commands.BucketType.user
        )
    },
):
    """
    Filtros y modificadores divertidos de imágenes. ¡Descubre cada uno de ellos!
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dagpi = dagpi  # Initialize the dagpi client as a class attribute

    @commands.hybrid_command(description='Checa el perfil de un usuario.', aliases=['av'])
    async def avatar(
            self, ctx, member: Union[discord.Member, discord.User] = None
    ):
        if not member or member == ctx.author:
            member = ctx.author
        avatar = str(member.avatar.replace(static_format='png', size=1024))
        embed = discord.Embed(
            title=f'Foto de perfil de {member.display_name}',
            color=ctx.author.color,
        )
        embed.set_image(url=avatar)
        embed.set_footer(text=f'Solicitado por {ctx.message.author}')
        await ctx.reply(embed=embed)

    @commands.hybrid_command(description="Censura el perfil de otro, porque sí.")
    async def pixel(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            # Get smaller avatar size (128x128)
            avatar_url = str(member.avatar.replace(size=128))
            img_pxl = await dagpi.image_process(
                ImageFeatures.pixel(), avatar_url
            )
            file_pxl = discord.File(
                fp=img_pxl.image, filename=f'pixel.{img_pxl.format}'
            )
            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://pixel.{img_pxl.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_pxl, embed=embed)

    @commands.hybrid_command(description="Hazle un patpat a un miembro.")
    async def pet(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_ptpt = await dagpi.image_process(
                ImageFeatures.petpet(), member.avatar.url
            )
            file_ptpt = discord.File(
                fp=img_ptpt.image, filename=f'pet.{img_ptpt.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://pet.{img_ptpt.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_ptpt, embed=embed)

    @commands.hybrid_command(description="URSS")
    async def urss(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_urss = await dagpi.image_process(
                ImageFeatures.communism(), member.avatar.url
            )
            file_urss = discord.File(
                fp=img_urss.image, filename=f'urss.{img_urss.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://urss.{img_urss.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_urss, embed=embed)

    @commands.hybrid_command(description="Analiza los colores de la foto de perfil de alguien.")
    async def colors(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_clrs = await dagpi.image_process(
                ImageFeatures.colors(), member.avatar.url
            )
            file_clrs = discord.File(
                fp=img_clrs.image, filename=f'colors.{img_clrs.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://colors.{img_clrs.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_clrs, embed=embed)

    @commands.hybrid_command(description="#Pride")
    async def gay(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            # Get smaller avatar size (128x128)
            avatar_url = str(member.avatar.replace(size=128))
            img_gy = await dagpi.image_process(
                ImageFeatures.gay(), avatar_url
            )
            file_gy = discord.File(
                fp=img_gy.image, filename=f'gay.{img_gy.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://gay.{img_gy.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_gy, embed=embed)

    @commands.hybrid_command(description="Para mandar a cualquiera a la carcel")
    async def jail(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            # Get smaller avatar size (128x128)
            avatar_url = str(member.avatar.replace(size=128))
            img_jl = await dagpi.image_process(
                ImageFeatures.jail(), avatar_url
            )
            file_jl = discord.File(
                fp=img_jl.image, filename=f'jail.{img_jl.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://jail.{img_jl.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_jl, embed=embed)

    @commands.hybrid_command(description="¿Alguien anda horny? ¡BONK! A la cárcel de los horny")
    async def bonk(self, ctx: commands.Context, member: discord.Member = None):
        if member == ctx.author:
            message = '¡No puedes darte bonk a tí mismo!\nPero puedo darte uno si quieres ( ͡° ͜ʖ ͡°)🏏'
            return await ctx.reply(message)
        elif not member:
            return await ctx.reply('¡Primero necesitas etiquetar a alguien para mandar a la horny jail!')

        embed = discord.Embed(color=ctx.author.color)
        embed.description = f'🏏 **¡BONK!** {ctx.author.name} ha enviado a {member.name} a la horny jail'
        embed.set_image(url="https://media.tenor.com/CrmEU2LKix8AAAAC/bonk-anime.gif")
        embed.set_footer(
            text=f'Solicitado por {ctx.message.author}',
            icon_url=member.avatar.url,
        )
        
        # Verificar si existe el cog Rol y añadir la acción pendiente
        rol_cog = self.bot.get_cog('Rol')
        if rol_cog and hasattr(rol_cog, 'pending_actions'):
            try:
                rol_cog.pending_actions[member.id] = {
                    "type": "bonk",
                    "author": ctx.author.name,
                    "author_id": ctx.author.id
                }
                
                # Usar nuestra propia implementación de InteractionView
                view = InteractionView(self, "bonk", ctx.author, member)
                return await ctx.reply(embed=embed, view=view)
            except Exception as e:
                print(f"Error al usar el cog Rol: {e}")
                # Continuar con la implementación alternativa
        
        # Implementación alternativa si el cog Rol no está disponible o falla
        embed.description += f'\n*{member.mention} puede usar `{ctx.prefix}correspond` para devolver el bonk o `{ctx.prefix}reject` para huir*'
        await ctx.reply(embed=embed)

    @commands.hybrid_command(description="Borra a alguien de la existencia")
    async def delete(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_dlt = await dagpi.image_process(
                ImageFeatures.delete(), member.avatar.url
            )
            file_dlt = discord.File(
                fp=img_dlt.image, filename=f'delete.{img_dlt.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://delete.{img_dlt.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_dlt, embed=embed)

    @commands.hybrid_command(description="KABOOM!")
    async def kaboom(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            # Get smaller avatar size (128x128)
            avatar_url = str(member.avatar.replace(size=128))
            img_bmb = await dagpi.image_process(
                ImageFeatures.bomb(), avatar_url
            )
            file_bmb = discord.File(
                fp=img_bmb.image, filename=f'bomb.{img_bmb.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://bomb.{img_bmb.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_bmb, embed=embed)

    @commands.hybrid_command(description="Porque todo es más bonito con el neón")
    async def neon(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_nn = await dagpi.image_process(
                ImageFeatures.neon(), member.avatar.url
            )
            file_nn = discord.File(
                fp=img_nn.image, filename=f'neon.{img_nn.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://neon.{img_nn.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_nn, embed=embed)

    @commands.hybrid_command(description="El más buscado por la ley")
    async def wanted(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            # Get smaller avatar size (128x128)
            avatar_url = str(member.avatar.replace(size=128))
            img_wntd = await dagpi.image_process(
                ImageFeatures.wanted(), avatar_url
            )
            file_wtnd = discord.File(
                fp=img_wntd.image, filename=f'wanted.{img_wntd.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://wanted.{img_wntd.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_wtnd, embed=embed)

    @commands.hybrid_command(description="RIP")
    async def wasted(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            # Get smaller avatar size (128x128)
            avatar_url = str(member.avatar.replace(size=128))
            img_wstd = await dagpi.image_process(
                ImageFeatures.wasted(), avatar_url
            )
            file_wstd = discord.File(
                fp=img_wstd.image, filename=f'wasted.{img_wstd.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://wasted.{img_wstd.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_wstd, embed=embed)

    @commands.hybrid_command(description="Capitalismo FTW")
    async def america(self, ctx: commands.Context, member: discord.Member = None):
        if member is None:
            member = ctx.author
        async with ctx.typing():
            img_mrc = await dagpi.image_process(
                ImageFeatures.america(), member.avatar.url
            )
            file_mrc = discord.File(
                fp=img_mrc.image, filename=f'america.{img_mrc.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://america.{img_mrc.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_mrc, embed=embed)

    @commands.hybrid_command(description="Pásale un filtro invertido a esa imagen de perfil")
    async def invert(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_nvrt = await dagpi.image_process(
                ImageFeatures.invert(), member.avatar.url
            )
            file_nvrt = discord.File(
                fp=img_nvrt.image, filename=f'invert.{img_nvrt.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://invert.{img_nvrt.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_nvrt, embed=embed)

    @commands.hybrid_command(description="¿Te gustan las papas fritas?")
    async def deepfry(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_dpfr = await dagpi.image_process(
                ImageFeatures.deepfry(), member.avatar.url
            )
            file_dpfr = discord.File(
                fp=img_dpfr.image, filename=f'deepfry.{img_dpfr.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://deepfry.{img_dpfr.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_dpfr, embed=embed)

    @commands.hybrid_command(description="A S C I I")
    async def ascii(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_sc = await dagpi.image_process(
                ImageFeatures.ascii(), member.avatar.url
            )
            file_sc = discord.File(
                fp=img_sc.image, filename=f'ascii.{img_sc.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://ascii.{img_sc.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_sc, embed=embed)

    @commands.hybrid_command(description="El típico y ya conocido filtro sepia")
    async def sepia(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_sp = await dagpi.image_process(
                ImageFeatures.sepia(), member.avatar.url
            )
            file_sp = discord.File(
                fp=img_sp.image, filename=f'sepia.{img_sp.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://sepia.{img_sp.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_sp, embed=embed)

    # @commands.command()
    # async def glitch(self, ctx, member: discord.Member=None):
    #   """
    #   Cool glitch B)
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_gltch = str(member.avatar.replace(static_format="png", size=1024))
    #     img_gltch = await dagpi.image_process(ImageFeatures.glitch(), url_gltch)
    #     file_gltch = discord.File(fp=img_gltch.image,filename=f"glitch.{img_gltch.format}")

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"attachment://glitch.{img_gltch.format}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ dagpi.xyz", icon_url=member.avatar.url)
    #     await ctx.reply(file=file_gltch, embed=embed)

    @commands.hybrid_command(description="Imprime esa imagen de perfil en una fotografía")
    async def polaroid(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_plrd = await dagpi.image_process(
                ImageFeatures.polaroid(), member.avatar.url
            )
            file_plrd = discord.File(
                fp=img_plrd.image, filename=f'polaroid.{img_plrd.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://polaroid.{img_plrd.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_plrd, embed=embed)

    @commands.hybrid_command(description="¿Cómo sería si te dibujase un artista?")
    async def sketch(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_sktch = await dagpi.image_process(
                ImageFeatures.sketch(), member.avatar.url
            )
            file_sktch = discord.File(
                fp=img_sktch.image, filename=f'sketch.{img_sktch.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://sketch.{img_sktch.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_sktch, embed=embed)

    @commands.hybrid_command(description="You spin me right round, baby")
    async def spin(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_spn = await dagpi.image_process(
                ImageFeatures.spin(), member.avatar.url
            )
            file_spn = discord.File(
                fp=img_spn.image, filename=f'spin.{img_spn.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://spin.{img_spn.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_spn, embed=embed)

    # @commands.command(aliases=["snap"])
    # async def dissolve(self, ctx, member: discord.Member=None):
    #   """
    #   Thanos snap
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_dsslv = str(member.avatar.replace(static_format="png", size=1024))
    #     img_dsslv = await dagpi.image_process(ImageFeatures.dissolve(), url_dsslv)
    #     file_dsslv = discord.File(fp=img_dsslv.image,filename=f"dissolve.{img_dsslv.format}")

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"attachment://dissolve.{img_dsslv.format}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ dagpi.xyz", icon_url=member.avatar.url)
    #     await ctx.reply(file=dissolve, embed=embed)

    @commands.hybrid_command(description="Usa este con cuidado")
    async def magik(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with ctx.typing():
            img_mgk = await dagpi.image_process(
                ImageFeatures.magik(), member.avatar.url
            )
            file_mgk = discord.File(
                fp=img_mgk.image, filename=f'magik.{img_mgk.format}'
            )

            embed = discord.Embed(color=ctx.author.color)
            embed.set_image(url=f'attachment://magik.{img_mgk.format}')
            embed.set_footer(
                text=f'Solicitado por {ctx.message.author} │ dagpi.xyz',
                icon_url=member.avatar.url,
            )
            await ctx.reply(file=file_mgk, embed=embed)

    # @commands.command()
    # async def hearts(self, ctx, member: discord.Member=None):
    #   """
    #   <3
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_hrts = str(member.avatar.replace(static_format="png", size=1024))

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"https://api.devs-hub.xyz/hearts?image={url_hrts}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ api.devs-hub.xyz", icon_url=member.avatar.url)
    #     await ctx.reply(embed=embed)

    # @commands.command()
    # async def simp(self, ctx, member: discord.Member=None):
    #   """
    #   Certified simp moment
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_smp = str(member.avatar.replace(static_format="png", size=1024))

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"https://api.devs-hub.xyz/simp?image={url_smp}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ api.devs-hub.xyz", icon_url=member.avatar.url)
    #     await ctx.reply(embed=embed)

    # @commands.command()
    # async def like(self, ctx, member: discord.Member=None):
    #   """
    #   [Everyone liked that]
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_lk = str(member.avatar.replace(static_format="png", size=1024))

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"https://api.devs-hub.xyz/like?image={url_lk}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ api.devs-hub.xyz", icon_url=member.avatar.url)
    #     await ctx.reply(embed=embed)

    # @commands.command()
    # async def joke(self, ctx, member: discord.Member=None):
    #   """
    #   Joke over your head
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_jk = str(member.avatar.replace(static_format="png", size=1024))

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"https://api.devs-hub.xyz/joke-over-head?image={url_jk}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ api.devs-hub.xyz", icon_url=member.avatar.url)
    #     await ctx.reply(embed=embed)

    # @commands.command()
    # async def beautiful(self, ctx, member: discord.Member=None):
    #   """
    #   Oh this, this is beautiful
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_btfl = str(member.avatar.replace(static_format="png", size=1024))

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"https://api.devs-hub.xyz/beautiful?image={url_btfl}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ api.devs-hub.xyz", icon_url=member.avatar.url)
    #     await ctx.reply(embed=embed)

    # @commands.command()
    # async def gun(self, ctx, member: discord.Member=None):
    #   """
    #   Plomo o plata
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_gn = str(member.avatar.replace(static_format="png", size=1024))

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"https://api.popcat.xyz/gun?image={url_gn}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ Pop Cat API", icon_url=member.avatar.url)
    #     await ctx.reply(embed=embed)

    # @commands.command()
    # async def grab(self, ctx, member: discord.Member=None):
    #   """
    #   ¡Ven aquí!
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_grb = str(member.avatar.replace(static_format="png", size=1024))

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"https://api.devs-hub.xyz/grab?image={url_grb}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ api.devs-hub.xyz", icon_url=member.avatar.url)
    #     await ctx.reply(embed=embed)

    # @commands.command()
    # async def rip(self, ctx, member: discord.Member=None):
    #   """
    #   Rest in Peace
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_rp = str(member.avatar.replace(static_format="png", size=1024))

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"https://api.devs-hub.xyz/rip?image={url_rp}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ api.devs-hub.xyz", icon_url=member.avatar.url)
    #     await ctx.reply(embed=embed)

    # @commands.command()
    # async def horny(self, ctx, member: discord.Member=None):
    #   """
    #   Licencia para estar horny
    #   """
    #   if member is None:
    #     member = ctx.author
    #   async with ctx.typing():
    #     url_hrn = str(member.avatar.replace(static_format="png", size=1024))

    #     embed = discord.Embed(color=ctx.author.color)
    #     embed.set_image(url=f"https://some-random-api.ml/canvas/horny?avatar={url_hrn}")
    #     embed.set_footer(text=f"Solicitado por {ctx.message.author} │ some-random-api.ml", icon_url=member.avatar.url)
    #     await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Image(bot))
