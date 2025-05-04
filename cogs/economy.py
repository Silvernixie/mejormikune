import discord
from discord.ext import commands
import json
import random
import asyncio
import datetime
import os
import typing
from discord import app_commands

class Economy(commands.Cog):
    """Sistema de economía y niveles para el servidor"""
    
    def __init__(self, bot):
        self.bot = bot
        self.economy_file = "data/economy.json"
        self.data = self.load_data()
        self.xp_cooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user)
        self.bonus_rates = {
            "daily": {"min": 100, "max": 500, "cooldown": 86400},  # 24 horas
            "weekly": {"min": 500, "max": 2000, "cooldown": 604800},  # 7 días
            "work": {"min": 50, "max": 250, "cooldown": 3600},  # 1 hora
        }
        self.jobs = [
            {"name": "Camarero", "min": 50, "max": 150},
            {"name": "Programador", "min": 100, "max": 300},
            {"name": "Profesor", "min": 80, "max": 200},
            {"name": "Médico", "min": 150, "max": 350},
            {"name": "Cocinero", "min": 70, "max": 180},
            {"name": "Streamer", "min": 0, "max": 500},  # Alto riesgo, alta recompensa
            {"name": "Astronauta", "min": 200, "max": 400},
            {"name": "Artista", "min": 50, "max": 250},
        ]
        self.shop_items = [
            {"id": "role1", "name": "Rol VIP", "price": 5000, "type": "role", "role_id": None},
            {"id": "badge1", "name": "Insignia Premium", "price": 2000, "type": "badge"},
            {"id": "color1", "name": "Color personalizado", "price": 3000, "type": "color"},
            {"id": "title1", "name": "Título personalizado", "price": 4000, "type": "title"},
        ]
        
        # Iniciar tareas de fondo
        self.bg_task = self.bot.loop.create_task(self.save_data_periodically())
        
    def cog_unload(self):
        self.bg_task.cancel()
        self.save_data()
    
    def load_data(self):
        if os.path.exists(self.economy_file):
            try:
                with open(self.economy_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading economy data: {e}")
                return {}
        return {}
    
    def save_data(self):
        try:
            with open(self.economy_file, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving economy data: {e}")
    
    async def save_data_periodically(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.save_data()
            await asyncio.sleep(300)  # Guardar cada 5 minutos
    
    def get_user_data(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {
                "balance": 0,
                "bank": 0,
                "xp": 0,
                "level": 1,
                "last_daily": 0,
                "last_weekly": 0,
                "last_work": 0,
                "inventory": [],
                "badges": [],
                "job": None,
                "color": None,
                "title": None,
                "last_message": 0
            }
        return self.data[user_id]
    
    def calculate_level(self, xp):
        return int(1 + (xp / 100) ** 0.5)
    
    def calculate_xp_for_level(self, level):
        return int(100 * (level - 1) ** 2)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        bucket = self.xp_cooldown.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            return
        
        user_id = str(message.author.id)
        user_data = self.get_user_data(user_id)
        
        # Verificar si ha pasado al menos 1 minuto desde el último mensaje
        current_time = datetime.datetime.now().timestamp()
        if current_time - user_data.get("last_message", 0) < 60:
            return
        
        # Actualizar tiempo del último mensaje
        user_data["last_message"] = current_time
        
        # Añadir XP entre 15 y 25
        xp_gain = random.randint(15, 25)
        user_data["xp"] += xp_gain
        
        # Comprobar si ha subido de nivel
        new_level = self.calculate_level(user_data["xp"])
        if new_level > user_data["level"]:
            user_data["level"] = new_level
            # Recompensa por subir de nivel
            level_bonus = new_level * 50
            user_data["balance"] += level_bonus
            
            # Enviar mensaje de subida de nivel en un embed
            embed = discord.Embed(
                title="¡Subida de nivel!",
                description=f"¡{message.author.mention} ha subido al nivel {new_level}!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Bonus", value=f"+{level_bonus} monedas")
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            # Intentar enviar en el mismo canal, pero solo si tenemos permisos
            try:
                await message.channel.send(embed=embed)
            except discord.Forbidden:
                # Si no se puede enviar en el canal, intentar enviar un DM
                try:
                    await message.author.send(embed=embed)
                except:
                    pass
        
        self.save_data()
    
    @commands.hybrid_command(name="balance", aliases=["bal"], description="Muestra tu balance económico")
    async def balance(self, ctx, user: typing.Optional[discord.Member] = None):
        """Muestra tu balance económico o el de otro usuario"""
        target = user or ctx.author
        user_data = self.get_user_data(target.id)
        
        embed = discord.Embed(
            title=f"Balance de {target.display_name}",
            color=discord.Color.green()
        )
        embed.add_field(name="Cartera", value=f"{user_data['balance']} monedas", inline=True)
        embed.add_field(name="Banco", value=f"{user_data['bank']} monedas", inline=True)
        embed.add_field(name="Total", value=f"{user_data['balance'] + user_data['bank']} monedas", inline=True)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="deposit", aliases=["dep"], description="Deposita dinero en el banco")
    async def deposit(self, ctx, amount: str):
        """Deposita dinero en el banco para protegerlo de robos"""
        user_data = self.get_user_data(ctx.author.id)
        
        if amount.lower() == "all":
            amount = user_data["balance"]
        else:
            try:
                amount = int(amount)
                if amount <= 0:
                    await ctx.send("❌ La cantidad debe ser positiva.")
                    return
            except ValueError:
                await ctx.send("❌ La cantidad debe ser un número o 'all'.")
                return
        
        if amount > user_data["balance"]:
            await ctx.send("❌ No tienes suficiente dinero en la cartera.")
            return
        
        user_data["balance"] -= amount
        user_data["bank"] += amount
        self.save_data()
        
        await ctx.send(f"✅ Has depositado {amount} monedas en el banco.")
    
    @commands.hybrid_command(name="withdraw", aliases=["with"], description="Retira dinero del banco")
    async def withdraw(self, ctx, amount: str):
        """Retira dinero del banco a tu cartera"""
        user_data = self.get_user_data(ctx.author.id)
        
        if amount.lower() == "all":
            amount = user_data["bank"]
        else:
            try:
                amount = int(amount)
                if amount <= 0:
                    await ctx.send("❌ La cantidad debe ser positiva.")
                    return
            except ValueError:
                await ctx.send("❌ La cantidad debe ser un número o 'all'.")
                return
        
        if amount > user_data["bank"]:
            await ctx.send("❌ No tienes suficiente dinero en el banco.")
            return
        
        user_data["bank"] -= amount
        user_data["balance"] += amount
        self.save_data()
        
        await ctx.send(f"✅ Has retirado {amount} monedas del banco.")
    
    @commands.hybrid_command(name="daily", description="Recibe tu recompensa diaria")
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 horas de cooldown
    async def daily(self, ctx):
        """Reclama tu recompensa diaria de monedas"""
        user_data = self.get_user_data(ctx.author.id)
        current_time = datetime.datetime.now().timestamp()
        
        last_daily = user_data.get("last_daily", 0)
        time_diff = current_time - last_daily
        
        if time_diff < self.bonus_rates["daily"]["cooldown"]:
            remaining = self.bonus_rates["daily"]["cooldown"] - time_diff
            remaining_time = datetime.timedelta(seconds=int(remaining))
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"❌ Puedes reclamar tu recompensa diaria en {remaining_time}.")
            return
        
        reward = random.randint(self.bonus_rates["daily"]["min"], self.bonus_rates["daily"]["max"])
        
        # Bonus por nivel
        level_bonus = int(reward * (user_data["level"] / 50))  # 2% extra por nivel
        total_reward = reward + level_bonus
        
        user_data["balance"] += total_reward
        user_data["last_daily"] = current_time
        self.save_data()
        
        embed = discord.Embed(
            title="Recompensa Diaria",
            description=f"¡Has recibido {reward} monedas!",
            color=discord.Color.gold()
        )
        
        if level_bonus > 0:
            embed.add_field(name="Bonus por nivel", value=f"+{level_bonus} monedas", inline=False)
        
        embed.add_field(name="Total", value=f"{total_reward} monedas", inline=False)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="weekly", description="Recibe tu recompensa semanal")
    @commands.cooldown(1, 604800, commands.BucketType.user)  # 7 días de cooldown
    async def weekly(self, ctx):
        """Reclama tu recompensa semanal de monedas"""
        user_data = self.get_user_data(ctx.author.id)
        current_time = datetime.datetime.now().timestamp()
        
        last_weekly = user_data.get("last_weekly", 0)
        time_diff = current_time - last_weekly
        
        if time_diff < self.bonus_rates["weekly"]["cooldown"]:
            remaining = self.bonus_rates["weekly"]["cooldown"] - time_diff
            remaining_time = datetime.timedelta(seconds=int(remaining))
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"❌ Puedes reclamar tu recompensa semanal en {remaining_time}.")
            return
        
        reward = random.randint(self.bonus_rates["weekly"]["min"], self.bonus_rates["weekly"]["max"])
        
        # Bonus por nivel
        level_bonus = int(reward * (user_data["level"] / 25))  # 4% extra por nivel
        total_reward = reward + level_bonus
        
        user_data["balance"] += total_reward
        user_data["last_weekly"] = current_time
        self.save_data()
        
        embed = discord.Embed(
            title="Recompensa Semanal",
            description=f"¡Has recibido {reward} monedas!",
            color=discord.Color.gold()
        )
        
        if level_bonus > 0:
            embed.add_field(name="Bonus por nivel", value=f"+{level_bonus} monedas", inline=False)
        
        embed.add_field(name="Total", value=f"{total_reward} monedas", inline=False)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="work", description="Trabaja para ganar monedas")
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 hora de cooldown
    async def work(self, ctx):
        """Trabaja para ganar monedas"""
        user_data = self.get_user_data(ctx.author.id)
        current_time = datetime.datetime.now().timestamp()
        
        last_work = user_data.get("last_work", 0)
        time_diff = current_time - last_work
        
        if time_diff < self.bonus_rates["work"]["cooldown"]:
            remaining = self.bonus_rates["work"]["cooldown"] - time_diff
            remaining_time = datetime.timedelta(seconds=int(remaining))
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"❌ Puedes volver a trabajar en {remaining_time}.")
            return
        
        # Si el usuario no tiene un trabajo, se le asigna uno aleatorio temporalmente
        if not user_data.get("job"):
            job = random.choice(self.jobs)
        else:
            # Encontrar el trabajo del usuario
            job = next((j for j in self.jobs if j["name"] == user_data["job"]), random.choice(self.jobs))
        
        reward = random.randint(job["min"], job["max"])
        
        # Bonus por nivel
        level_bonus = int(reward * (user_data["level"] / 100))  # 1% extra por nivel
        total_reward = reward + level_bonus
        
        user_data["balance"] += total_reward
        user_data["last_work"] = current_time
        self.save_data()
        
        # Mensaje de trabajo aleatorio
        work_messages = [
            f"Trabajaste como {job['name']} y ganaste {reward} monedas.",
            f"Tu jefe quedó impresionado con tu trabajo como {job['name']} y te pagó {reward} monedas.",
            f"Completaste un turno como {job['name']} y recibiste {reward} monedas.",
            f"Trabajaste duro como {job['name']} y ganaste {reward} monedas.",
        ]
        
        embed = discord.Embed(
            title="Trabajo Completado",
            description=random.choice(work_messages),
            color=discord.Color.blue()
        )
        
        if level_bonus > 0:
            embed.add_field(name="Bonus por nivel", value=f"+{level_bonus} monedas", inline=False)
        
        embed.add_field(name="Total", value=f"{total_reward} monedas", inline=False)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="rob", description="Intenta robar monedas a otro usuario")
    @commands.cooldown(1, 7200, commands.BucketType.user)  # 2 horas de cooldown
    async def rob(self, ctx, target: discord.Member):
        """Intenta robar monedas a otro usuario"""
        if target.id == ctx.author.id:
            await ctx.send("❌ No puedes robarte a ti mismo.")
            return
        
        if target.bot:
            await ctx.send("❌ No puedes robar a un bot.")
            return
        
        user_data = self.get_user_data(ctx.author.id)
        target_data = self.get_user_data(target.id)
        
        # Requisito mínimo para intentar robar
        if user_data["balance"] < 200:
            await ctx.send("❌ Necesitas al menos 200 monedas en tu cartera para intentar robar.")
            return
        
        # El objetivo debe tener al menos 100 monedas
        if target_data["balance"] < 100:
            await ctx.send("❌ No vale la pena robar a alguien con tan poco dinero.")
            return
        
        # Probabilidad de éxito: 40% base + 0.5% por cada nivel del ladrón - 0.5% por cada nivel del objetivo
        success_rate = 40 + (user_data["level"] * 0.5) - (target_data["level"] * 0.5)
        success_rate = max(10, min(success_rate, 75))  # No menos del 10% ni más del 75%
        
        if random.random() * 100 < success_rate:
            # Robo exitoso: entre 10% y 30% del balance del objetivo
            steal_percent = random.uniform(0.1, 0.3)
            amount = int(target_data["balance"] * steal_percent)
            
            target_data["balance"] -= amount
            user_data["balance"] += amount
            
            embed = discord.Embed(
                title="¡Robo Exitoso!",
                description=f"Has robado {amount} monedas de {target.mention}!",
                color=discord.Color.green()
            )
        else:
            # Robo fallido: multa de entre 100 y 300 monedas
            fine = min(user_data["balance"], random.randint(100, 300))
            user_data["balance"] -= fine
            
            embed = discord.Embed(
                title="¡Robo Fallido!",
                description=f"¡Te han atrapado intentando robar a {target.mention}!",
                color=discord.Color.red()
            )
            embed.add_field(name="Multa", value=f"-{fine} monedas", inline=False)
        
        self.save_data()
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="shop", description="Muestra la tienda")
    async def shop(self, ctx):
        """Muestra los artículos disponibles en la tienda"""
        embed = discord.Embed(
            title="Tienda",
            description="Compra artículos con tus monedas.",
            color=discord.Color.blue()
        )
        
        for item in self.shop_items:
            embed.add_field(
                name=f"{item['name']} - {item['price']} monedas",
                value=f"Tipo: {item['type'].capitalize()}\nID: `{item['id']}`",
                inline=False
            )
        
        embed.set_footer(text="Usa /buy <id> para comprar un artículo.")
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="buy", description="Compra un artículo de la tienda")
    async def buy(self, ctx, item_id: str):
        """Compra un artículo de la tienda usando su ID"""
        user_data = self.get_user_data(ctx.author.id)
        
        # Buscar el artículo en la tienda
        item = next((i for i in self.shop_items if i["id"] == item_id), None)
        
        if not item:
            await ctx.send("❌ Artículo no encontrado. Usa /shop para ver los artículos disponibles.")
            return
        
        # Verificar si el usuario tiene suficiente dinero
        if user_data["balance"] < item["price"]:
            await ctx.send(f"❌ No tienes suficiente dinero. Necesitas {item['price']} monedas.")
            return
        
        # Verificar si el usuario ya tiene este artículo
        if item["id"] in [i["id"] for i in user_data.get("inventory", [])]:
            await ctx.send("❌ Ya tienes este artículo.")
            return
        
        # Procesar la compra según el tipo de artículo
        if item["type"] == "role" and item["role_id"]:
            role = ctx.guild.get_role(item["role_id"])
            if role:
                try:
                    await ctx.author.add_roles(role)
                except discord.Forbidden:
                    await ctx.send("❌ No tengo permisos para asignar ese rol.")
                    return
            else:
                await ctx.send("❌ El rol no existe en este servidor.")
                return
        
        # Actualizar el inventario del usuario
        if "inventory" not in user_data:
            user_data["inventory"] = []
        
        user_data["inventory"].append({
            "id": item["id"],
            "name": item["name"],
            "type": item["type"],
            "purchased_at": datetime.datetime.now().timestamp()
        })
        
        # Restar el precio del balance
        user_data["balance"] -= item["price"]
        self.save_data()
        
        await ctx.send(f"✅ Has comprado {item['name']} por {item['price']} monedas.")
    
    @commands.hybrid_command(name="inventory", aliases=["inv"], description="Muestra tu inventario")
    async def inventory(self, ctx, user: typing.Optional[discord.Member] = None):
        """Muestra tu inventario o el de otro usuario"""
        target = user or ctx.author
        user_data = self.get_user_data(target.id)
        
        if not user_data.get("inventory"):
            if target == ctx.author:
                await ctx.send("❌ No tienes ningún artículo en tu inventario.")
            else:
                await ctx.send(f"❌ {target.display_name} no tiene ningún artículo en su inventario.")
            return
        
        embed = discord.Embed(
            title=f"Inventario de {target.display_name}",
            color=discord.Color.blue()
        )
        
        for item in user_data["inventory"]:
            purchase_date = datetime.datetime.fromtimestamp(item.get("purchased_at", 0)).strftime("%d/%m/%Y")
            embed.add_field(
                name=item["name"],
                value=f"Tipo: {item['type'].capitalize()}\nComprado: {purchase_date}",
                inline=True
            )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="level", aliases=["lvl"], description="Muestra tu nivel y experiencia")
    async def level(self, ctx, user: typing.Optional[discord.Member] = None):
        """Muestra tu nivel y experiencia o los de otro usuario"""
        target = user or ctx.author
        user_data = self.get_user_data(target.id)
        
        current_level = user_data["level"]
        current_xp = user_data["xp"]
        xp_for_current_level = self.calculate_xp_for_level(current_level)
        xp_for_next_level = self.calculate_xp_for_level(current_level + 1)
        xp_needed = xp_for_next_level - xp_for_current_level
        xp_progress = current_xp - xp_for_current_level
        
        progress_percent = int((xp_progress / xp_needed) * 100) if xp_needed > 0 else 100
        
        # Crear una barra de progreso
        bar_length = 20
        filled_length = int(bar_length * progress_percent / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        embed = discord.Embed(
            title=f"Nivel de {target.display_name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Nivel", value=str(current_level), inline=True)
        embed.add_field(name="XP Total", value=str(current_xp), inline=True)
        embed.add_field(name="Progreso", value=f"{progress_percent}%", inline=True)
        embed.add_field(name="Progreso al siguiente nivel", value=f"{bar} {xp_progress}/{xp_needed}", inline=False)
        
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="leaderboard", aliases=["lb"], description="Muestra la tabla de clasificación")
    async def leaderboard(self, ctx, category: str = "level"):
        """Muestra la tabla de clasificación por nivel o riqueza"""
        valid_categories = ["level", "money", "xp"]
        
        if category.lower() not in valid_categories:
            await ctx.send(f"❌ Categoría no válida. Usa: {', '.join(valid_categories)}")
            return
        
        # Filtrar solo los usuarios que son miembros del servidor actual
        server_member_ids = [str(member.id) for member in ctx.guild.members]
        server_data = {user_id: data for user_id, data in self.data.items() if user_id in server_member_ids}
        
        if category.lower() == "level":
            sorted_users = sorted(server_data.items(), key=lambda x: x[1]["level"], reverse=True)
            title = "Tabla de Clasificación - Niveles"
            value_key = "level"
            emoji = "🏆"
        elif category.lower() == "money":
            sorted_users = sorted(server_data.items(), key=lambda x: x[1]["balance"] + x[1].get("bank", 0), reverse=True)
            title = "Tabla de Clasificación - Riqueza"
            value_key = ["balance", "bank"]
            emoji = "💰"
        else:  # xp
            sorted_users = sorted(server_data.items(), key=lambda x: x[1]["xp"], reverse=True)
            title = "Tabla de Clasificación - Experiencia"
            value_key = "xp"
            emoji = "✨"
        
        embed = discord.Embed(
            title=title,
            color=discord.Color.gold()
        )
        
        # Limitar a los 10 mejores
        for i, (user_id, data) in enumerate(sorted_users[:10], 1):
            user = ctx.guild.get_member(int(user_id))
            if not user:
                continue
            
            if isinstance(value_key, list):
                value = sum(data.get(k, 0) for k in value_key)
                display_value = f"{value} monedas"
            else:
                value = data.get(value_key, 0)
                display_value = f"Nivel {value}" if value_key == "level" else f"{value} XP" if value_key == "xp" else f"{value} monedas"
            
            embed.add_field(
                name=f"{i}. {user.display_name}",
                value=f"{emoji} {display_value}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="pay", description="Paga monedas a otro usuario")
    async def pay(self, ctx, user: discord.Member, amount: int):
        """Transfiere monedas a otro usuario"""
        if user.bot:
            await ctx.send("❌ No puedes pagar a un bot.")
            return
            
        if user.id == ctx.author.id:
            await ctx.send("❌ No puedes pagarte a ti mismo.")
            return
            
        if amount <= 0:
            await ctx.send("❌ La cantidad debe ser positiva.")
            return
            
        sender_data = self.get_user_data(ctx.author.id)
            
        if sender_data["balance"] < amount:
            await ctx.send("❌ No tienes suficiente dinero en tu cartera.")
            return
            
        receiver_data = self.get_user_data(user.id)
            
        # Realizar la transferencia
        sender_data["balance"] -= amount
        receiver_data["balance"] += amount
        self.save_data()
            
        await ctx.send(f"✅ Has pagado {amount} monedas a {user.mention}.")
    
    @commands.hybrid_command(name="job", description="Muestra o cambia tu trabajo")
    async def job(self, ctx, job_choice: typing.Optional[str] = None):
        """Muestra o cambia tu trabajo actual"""
        user_data = self.get_user_data(ctx.author.id)
        
        if not job_choice:
            # Mostrar el trabajo actual y la lista de trabajos disponibles
            embed = discord.Embed(
                title="Trabajos Disponibles",
                color=discord.Color.blue()
            )
            
            current_job = user_data.get("job", "Desempleado")
            embed.add_field(name="Tu trabajo actual", value=current_job, inline=False)
            
            jobs_list = "\n".join([f"• {job['name']} - {job['min']}-{job['max']} monedas" for job in self.jobs])
            embed.add_field(name="Trabajos disponibles", value=jobs_list, inline=False)
            embed.set_footer(text="Usa /job <nombre> para cambiar de trabajo")
            
            await ctx.send(embed=embed)
            return
        
        # Buscar el trabajo por nombre
        job = next((j for j in self.jobs if j["name"].lower() == job_choice.lower()), None)
        
        if not job:
            await ctx.send(f"❌ Trabajo no encontrado. Usa /job para ver los trabajos disponibles.")
            return
        
        # Cambiar de trabajo
        user_data["job"] = job["name"]
        self.save_data()
        
        await ctx.send(f"✅ Ahora trabajas como {job['name']}.")

async def setup(bot):
    await bot.add_cog(Economy(bot))