import discord
import json
import random
import asyncio
import math
import time
from discord.ext import commands
from datetime import datetime, timedelta

class Economia(commands.Cog):
    """🐰 Sistema económico para gestionar tus conejos virtuales"""

    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self.economy_file = 'data/economy.json'
        self.load_data()
        # Items para la tienda
        self.shop_items = {
            "carrot": {"name": "🥕 Zanahoria", "price": 50, "description": "Una zanahoria fresca para alimentar a tus conejos", "type": "consumible"},
            "carrot_seeds": {"name": "🌱 Semillas de zanahoria", "price": 30, "description": "Plántalas para cultivar zanahorias", "type": "semilla"},
            "water": {"name": "💧 Regadera", "price": 100, "description": "Riega tus cultivos para que crezcan más rápido", "type": "herramienta"},
            "rabbit_house": {"name": "🏠 Casa de conejo", "price": 500, "description": "Un hogar acogedor para tus conejos", "type": "mejora"},
            "bunny_hat": {"name": "🎩 Sombrero de conejo", "price": 300, "description": "Un sombrero elegante para tu perfil", "type": "cosmético"},
            "golden_carrot": {"name": "🥕✨ Zanahoria dorada", "price": 1000, "description": "Una zanahoria especial que aumenta tus ganancias", "type": "boost"},
            "fishing_rod": {"name": "🎣 Caña de pescar", "price": 750, "description": "Te permite pescar y ganar premios", "type": "herramienta"},
            "lucky_clover": {"name": "🍀 Trébol de la suerte", "price": 600, "description": "Aumenta tus probabilidades de éxito", "type": "boost"},
            "mystery_box": {"name": "📦 Caja misteriosa", "price": 800, "description": "Contiene una sorpresa aleatoria", "type": "consumible"},
            "thief_mask": {"name": "🎭 Máscara de ladrón", "price": 1200, "description": "Te permite robar conejos (con riesgo)", "type": "herramienta"},
            "mining_pick": {"name": "⛏️ Pico de minería", "price": 850, "description": "Te permite extraer minerales valiosos", "type": "herramienta"},
            "carrot_soup": {"name": "🍲 Sopa de zanahoria", "price": 150, "description": "Recupera energía y reduce cooldowns", "type": "consumible"},
            "business_license": {"name": "📜 Licencia de negocio", "price": 2500, "description": "Permite abrir un negocio propio", "type": "especial"},
            "property_deed": {"name": "📝 Escritura de propiedad", "price": 5000, "description": "Documento para adquirir propiedades", "type": "especial"},
            "bank_certificate": {"name": "🏛️ Certificado bancario", "price": 3000, "description": "Otorga beneficios en operaciones bancarias", "type": "especial"},
            "investment_bond": {"name": "💼 Bono de inversión", "price": 2000, "description": "Genera intereses pasivos con el tiempo", "type": "inversión"},
            "carrot_factory": {"name": "🏭 Fábrica de zanahorias", "price": 8000, "description": "Genera zanahorias pasivamente", "type": "inversión"},
            "rabbit_insurance": {"name": "📊 Seguro de conejos", "price": 1500, "description": "Protege tus conejos de robos y pérdidas", "type": "seguro"}
        }
        # Loot para cajas y aventuras
        self.loot_table = {
            "common": ["carrot", "water", "carrot_seeds", "carrot_soup"],
            "uncommon": ["bunny_hat", "fishing_rod", "lucky_clover", "mining_pick"],
            "rare": ["rabbit_house", "golden_carrot", "mystery_box", "rabbit_insurance"],
            "legendary": ["diamond_carrot", "royal_bunny", "magic_hutch", "carrot_factory", "property_deed"]
        }
        # Trabajos para el comando job
        self.jobs = {
            "granjero": {"description": "Cultiva zanahorias y cuida conejos", "min_pay": 80, "max_pay": 200, "cooldown": 30, "skill": "agricultura"},
            "cocinero": {"description": "Prepara deliciosos platillos para conejos", "min_pay": 100, "max_pay": 220, "cooldown": 35, "skill": "cocina"},
            "veterinario": {"description": "Cuida la salud de los conejos", "min_pay": 150, "max_pay": 300, "cooldown": 45, "skill": "medicina"},
            "entrenador": {"description": "Entrena conejos para competiciones", "min_pay": 120, "max_pay": 250, "cooldown": 40, "skill": "entrenamiento"},
            "explorador": {"description": "Busca recursos raros para conejos", "min_pay": 200, "max_pay": 400, "cooldown": 60, "skill": "exploración"},
            "minero": {"description": "Extrae minerales valiosos para conejos", "min_pay": 180, "max_pay": 350, "cooldown": 50, "skill": "minería"},
            "científico": {"description": "Investiga nuevas tecnologías para conejos", "min_pay": 250, "max_pay": 450, "cooldown": 75, "skill": "ciencia"},
            "pescador": {"description": "Pesca alimentos para conejos", "min_pay": 120, "max_pay": 280, "cooldown": 40, "skill": "pesca"},
            "carpintero": {"description": "Construye casas y muebles para conejos", "min_pay": 160, "max_pay": 320, "cooldown": 45, "skill": "construcción"},
            "herrero": {"description": "Forja herramientas y equipo para conejos", "min_pay": 170, "max_pay": 340, "cooldown": 50, "skill": "herrería"},
            "abogado": {"description": "Resuelve disputas legales entre conejos", "min_pay": 300, "max_pay": 500, "cooldown": 90, "skill": "leyes"},
            "banquero": {"description": "Administra las finanzas de los conejos", "min_pay": 280, "max_pay": 480, "cooldown": 80, "skill": "finanzas"}
        }
        # Propiedades disponibles
        self.properties = {
            "small_hutch": {"name": "🏠 Pequeña madriguera", "price": 10000, "description": "Una pequeña madriguera acogedora", "income": 100, "collection_time": 24},
            "medium_hutch": {"name": "🏡 Madriguera mediana", "price": 25000, "description": "Una madriguera de tamaño mediano con jardín", "income": 250, "collection_time": 24},
            "large_hutch": {"name": "🏘️ Madriguera grande", "price": 50000, "description": "Una espaciosa madriguera para conejos", "income": 500, "collection_time": 24},
            "carrot_farm": {"name": "🚜 Granja de zanahorias", "price": 75000, "description": "Una granja que produce zanahorias", "income": 800, "collection_time": 24},
            "carrot_shop": {"name": "🏪 Tienda de zanahorias", "price": 100000, "description": "Una tienda que vende zanahorias", "income": 1200, "collection_time": 24},
            "carrot_restaurant": {"name": "🍽️ Restaurante de zanahorias", "price": 150000, "description": "Un restaurante especializado en zanahorias", "income": 1800, "collection_time": 24},
            "rabbit_hotel": {"name": "🏨 Hotel para conejos", "price": 200000, "description": "Un lujoso hotel para conejos viajeros", "income": 2500, "collection_time": 24},
            "carrot_factory": {"name": "🏭 Fábrica de zanahorias", "price": 300000, "description": "Una fábrica que procesa zanahorias", "income": 3500, "collection_time": 24},
            "carrot_theme_park": {"name": "🎡 Parque temático de zanahorias", "price": 500000, "description": "Un parque temático con atracciones de zanahorias", "income": 5000, "collection_time": 24}
        }
        # Configuraciones del banco y préstamos
        self.bank_config = {
            "interest_rate": 0.02,  # 2% de interés diario en ahorros
            "loan_interest_rate": 0.05,  # 5% de interés diario en préstamos
            "min_loan": 1000,  # Préstamo mínimo
            "max_loan_multiplier": 2,  # Máximo préstamo = 2x balance total
            "loan_duration_days": 7,  # Duración préstamos en días
            "transfer_fee_percent": 0.01  # 1% de comisión en transferencias
        }

    def load_data(self):
        try:
            with open(self.economy_file, 'r') as f:
                self.economy = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.economy = {}
            self.save_data()

    def save_data(self):
        with open(self.economy_file, 'w') as f:
            json.dump(self.economy, f, indent=4)

    def ensure_user(self, user_id):
        """Asegura que el usuario exista en la base de datos con todos los campos requeridos"""
        if str(user_id) not in self.economy:
            self.economy[str(user_id)] = {
                "balance": 0,
                "bank": 0,
                "last_daily": None,
                "inventory": {},
                "farm": {
                    "plots": 0,
                    "crops": {},
                    "last_watered": None
                },
                "stats": {
                    "worked": 0,
                    "commands_used": 0,
                    "gambles_won": 0,
                    "gambles_lost": 0,
                    "stolen": 0,
                    "stolen_from": 0,
                    "crimes_succeeded": 0,
                    "crimes_failed": 0
                },
                "pets": {},
                "level": 1,
                "xp": 0,
                "job": None,
                "streak": {
                    "daily": 0,
                    "last_claim": None
                },
                "perks": {},
                "last_rob": None,
                "last_crime": None,
                "last_adventure": None,
                "last_fish": None,
                "last_hunt": None,
                "last_weekly": None,
                "last_monthly": None,
                "last_interest": None,
                "properties": {},
                "loans": [],
                "job_skills": {},
                "business": None,
                "last_property_collection": {}
            }
            self.save_data()
        
        # Asegurar que los usuarios existentes tengan todos los campos nuevos
        user_data = self.economy[str(user_id)]
        required_fields = {
            "inventory": {},
            "farm": {
                "plots": 0,
                "crops": {},
                "last_watered": None
            },
            "stats": {
                "worked": 0,
                "commands_used": 0,
                "gambles_won": 0,
                "gambles_lost": 0,
                "stolen": 0,
                "stolen_from": 0,
                "crimes_succeeded": 0,
                "crimes_failed": 0
            },
            "pets": {},
            "level": 1,
            "xp": 0,
            "job": None,
            "streak": {
                "daily": 0,
                "last_claim": None
            },
            "perks": {},
            "last_rob": None,
            "last_crime": None,
            "last_adventure": None,
            "last_fish": None,
            "last_hunt": None,
            "last_weekly": None,
            "last_monthly": None,
            "last_interest": None,
            "properties": {},
            "loans": [],
            "job_skills": {},
            "business": None,
            "last_property_collection": {}
        }
        
        updated = False
        for field, default_value in required_fields.items():
            if field not in user_data:
                user_data[field] = default_value
                updated = True
            elif isinstance(default_value, dict):
                for subfield, subvalue in default_value.items():
                    if subfield not in user_data[field]:
                        user_data[field][subfield] = subvalue
                        updated = True
        
        if updated:
            self.save_data()
            
        return user_data

    def add_xp(self, user_id, amount):
        """Añade XP al usuario y gestiona la subida de nivel"""
        user_data = self.ensure_user(user_id)
        user_data["xp"] += amount
        
        # Calcular el XP necesario para el siguiente nivel (fórmula: 100 * nivel actual)
        xp_needed = 100 * user_data["level"]
        
        # Comprobar si el usuario ha subido de nivel
        if user_data["xp"] >= xp_needed:
            user_data["level"] += 1
            user_data["xp"] -= xp_needed
            self.save_data()
            return True, user_data["level"]
        
        self.save_data()
        return False, 0
    
    def get_cooldown_remaining(self, user_id, cooldown_type, cooldown_time):
        """Obtiene el tiempo restante de un cooldown en segundos"""
        current_time = datetime.utcnow()
        
        if cooldown_type in self.cooldowns and user_id in self.cooldowns[cooldown_type]:
            last_time = self.cooldowns[cooldown_type][user_id]
            time_diff = current_time - last_time
            
            if time_diff < cooldown_time:
                remaining = cooldown_time - time_diff
                return remaining.total_seconds()
        
        return 0
    
    def format_time(self, seconds):
        """Formatea segundos en un string legible de tiempo"""
        if seconds < 60:
            return f"{int(seconds)}s"
        
        minutes, seconds = divmod(seconds, 60)
        if minutes < 60:
            return f"{int(minutes)}m {int(seconds)}s"
        
        hours, minutes = divmod(minutes, 60)
        if hours < 24:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            
        days, hours = divmod(hours, 24)
        return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
        
    def add_item_to_inventory(self, user_id, item_id, amount=1):
        """Añade un item al inventario del usuario"""
        user_data = self.ensure_user(user_id)
        
        if "inventory" not in user_data:
            user_data["inventory"] = {}
            
        if item_id in user_data["inventory"]:
            user_data["inventory"][item_id] += amount
        else:
            user_data["inventory"][item_id] = amount
            
        self.save_data()
        
    def calculate_interest(self, user_id):
        """Calcula y aplica el interés diario de la cuenta bancaria"""
        user_data = self.ensure_user(user_id)
        current_time = datetime.utcnow()
        last_interest = user_data.get("last_interest")
        
        # Si nunca ha recibido interés o ha pasado más de un día
        if not last_interest or (current_time - datetime.fromisoformat(last_interest)) >= timedelta(days=1):
            # Calcular interés (solo si tiene dinero en el banco)
            if user_data["bank"] > 0:
                interest_amount = math.floor(user_data["bank"] * self.bank_config["interest_rate"])
                user_data["bank"] += interest_amount
                user_data["last_interest"] = current_time.isoformat()
                self.save_data()
                return interest_amount
            else:
                user_data["last_interest"] = current_time.isoformat()
                self.save_data()
                
        return 0
        
    def get_loan_info(self, user_id):
        """Obtiene información sobre los préstamos del usuario"""
        user_data = self.ensure_user(user_id)
        current_time = datetime.utcnow()
        
        active_loans = []
        repaid_loans = []
        overdue_loans = []
        total_debt = 0
        
        for loan in user_data.get("loans", []):
            loan_amount = loan["amount"]
            interest = loan["interest"]
            start_date = datetime.fromisoformat(loan["start_date"])
            due_date = datetime.fromisoformat(loan["due_date"])
            status = loan["status"]
            
            # Calcular interés acumulado
            days_passed = (current_time - start_date).days
            current_debt = loan_amount + (loan_amount * interest * days_passed)
            
            # Actualizar deuda total
            if status == "active":
                total_debt += current_debt
                
                # Verificar si está vencido
                if current_time > due_date:
                    overdue_loans.append({
                        "original": loan_amount,
                        "current": current_debt,
                        "due_date": due_date.isoformat(),
                        "days_overdue": (current_time - due_date).days
                    })
                else:
                    active_loans.append({
                        "original": loan_amount,
                        "current": current_debt,
                        "due_date": due_date.isoformat(),
                        "days_remaining": (due_date - current_time).days
                    })
            elif status == "repaid":
                repaid_loans.append({
                    "original": loan_amount,
                    "paid": loan.get("paid_amount", loan_amount),
                    "date": loan.get("repaid_date", "Desconocido")
                })
                
        return {
            "active": active_loans,
            "overdue": overdue_loans,
            "repaid": repaid_loans,
            "total_debt": total_debt
        }
        
    def can_afford_property(self, user_id, property_id):
        """Verifica si el usuario puede comprar una propiedad"""
        user_data = self.ensure_user(user_id)
        
        # Verificar si la propiedad existe
        if property_id not in self.properties:
            return False, "La propiedad no existe"
            
        property_info = self.properties[property_id]
        property_price = property_info["price"]
        
        # Verificar si ya tiene la propiedad
        if property_id in user_data.get("properties", {}):
            return False, "Ya posees esta propiedad"
            
        # Verificar si tiene suficiente dinero
        total_money = user_data["balance"] + user_data["bank"]
        if total_money < property_price:
            return False, f"No tienes suficientes conejos. Necesitas {property_price} y tienes {total_money}"
            
        # Verificar si tiene escritura de propiedad
        has_deed = "property_deed" in user_data.get("inventory", {}) and user_data["inventory"]["property_deed"] > 0
        if not has_deed:
            return False, "Necesitas una Escritura de Propiedad para comprar bienes raíces"
            
        return True, "Puedes comprar esta propiedad"
        
    def collect_property_income(self, user_id):
        """Recoge los ingresos de todas las propiedades del usuario"""
        user_data = self.ensure_user(user_id)
        current_time = datetime.utcnow()
        
        if not user_data.get("properties"):
            return 0, []
            
        total_income = 0
        collected_properties = []
        
        for property_id, property_data in user_data["properties"].items():
            last_collection = user_data.get("last_property_collection", {}).get(property_id)
            property_info = self.properties.get(property_id)
            
            if not property_info:
                continue
                
            collection_hours = property_info["collection_time"]
            
            if not last_collection or (current_time - datetime.fromisoformat(last_collection)) >= timedelta(hours=collection_hours):
                income = property_info["income"]
                total_income += income
                collected_properties.append({
                    "name": property_info["name"],
                    "income": income
                })
                
                # Actualizar tiempo de colección
                if "last_property_collection" not in user_data:
                    user_data["last_property_collection"] = {}
                user_data["last_property_collection"][property_id] = current_time.isoformat()
                
        # Añadir ingresos al balance
        if total_income > 0:
            user_data["balance"] += total_income
            self.save_data()
            
        return total_income, collected_properties

    # COMANDOS BANCARIOS
    
    @commands.group(name="bank", aliases=["banco", "banking"], invoke_without_command=True)
    async def bank(self, ctx):
        """🏦 Gestiona tus conejos en el banco"""
        user_id = str(ctx.author.id)
        user_data = self.ensure_user(ctx.author.id)
        
        # Calcular interés ganado
        interest_earned = self.calculate_interest(ctx.author.id)
        
        # Obtener información de préstamos
        loan_info = self.get_loan_info(ctx.author.id)
        
        # Crear embed
        embed = discord.Embed(
            title="🏦 Cuenta Bancaria",
            description=f"Información de tu cuenta bancaria",
            color=discord.Color.blue()
        )
        
        # Datos básicos
        embed.add_field(
            name="💰 Saldo",
            value=f"Conejos en Banco: {user_data['bank']:,}\n"
                  f"Conejos en Mano: {user_data['balance']:,}\n"
                  f"Total: {user_data['bank'] + user_data['balance']:,}",
            inline=False
        )
        
        # Interés ganado
        if interest_earned > 0:
            embed.add_field(
                name="💸 Interés Ganado",
                value=f"¡Has ganado {interest_earned} conejos de interés hoy!",
                inline=False
            )
        else:
            next_interest = "mañana" if user_data.get("last_interest") else "hoy"
            embed.add_field(
                name="💸 Interés",
                value=f"Tasa: {self.bank_config['interest_rate']*100}% diario\n"
                      f"Próximo interés: {next_interest}",
                inline=False
            )
        
        # Préstamos activos
        if loan_info["active"] or loan_info["overdue"]:
            loans_text = ""
            
            for loan in loan_info["active"]:
                loans_text += f"• {loan['original']:,} (Deuda actual: {math.floor(loan['current']):,})\n"
                loans_text += f"  Vence en: {loan['days_remaining']} días\n"
                
            for loan in loan_info["overdue"]:
                loans_text += f"• ⚠️ {loan['original']:,} (Deuda actual: {math.floor(loan['current']):,})\n"
                loans_text += f"  **VENCIDO** hace {loan['days_overdue']} días\n"
                
            embed.add_field(
                name="📝 Préstamos Activos",
                value=loans_text or "No tienes préstamos activos",
                inline=False
            )
            
            embed.add_field(
                name="💸 Deuda Total",
                value=f"{math.floor(loan_info['total_debt']):,} conejos",
                inline=False
            )
        
        # Comandos bancarios disponibles
        embed.add_field(
            name="🔍 Comandos Disponibles",
            value="• `bank deposit [cantidad/all]` - Depositar conejos\n"
                  "• `bank withdraw [cantidad/all]` - Retirar conejos\n"
                  "• `bank transfer [usuario] [cantidad]` - Transferir conejos\n"
                  "• `bank loan [cantidad]` - Solicitar un préstamo\n"
                  "• `bank payloan [cantidad/all]` - Pagar un préstamo",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @bank.command(name="deposit", aliases=["depositar"])
    async def bank_deposit(self, ctx, amount: str = None):
        """💵 Deposita conejos de tu balance a tu cuenta bancaria"""
        user_id = str(ctx.author.id)
        user_data = self.ensure_user(ctx.author.id)
        
        # Verificar parámetros
        if amount is None:
            return await ctx.send("❌ Uso correcto: `bank deposit [cantidad/all]`")
        
        # Verificar cantidad
        if amount.lower() == "all" or amount.lower() == "todo":
            amount = user_data["balance"]
        else:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send("❌ Por favor, introduce un número válido o 'all'/'todo'.")
        
        if amount <= 0:
            return await ctx.send("❌ La cantidad debe ser mayor que 0.")
        
        if amount > user_data["balance"]:
            return await ctx.send(f"❌ No tienes suficientes conejos. Solo tienes {user_data['balance']:,} conejos en mano.")
        
        # Transferir conejos
        user_data["balance"] -= amount
        user_data["bank"] += amount
        self.save_data()
        
        # Mensaje de confirmación
        embed = discord.Embed(
            title="🏦 Depósito Realizado",
            description=f"Has depositado {amount:,} conejos en tu cuenta bancaria",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Balance Actual",
            value=f"Conejos en mano: {user_data['balance']:,}\n"
                  f"Conejos en banco: {user_data['bank']:,}",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @bank.command(name="withdraw", aliases=["retirar"])
    async def bank_withdraw(self, ctx, amount: str = None):
        """💸 Retira conejos de tu cuenta bancaria a tu balance"""
        user_id = str(ctx.author.id)
        user_data = self.ensure_user(ctx.author.id)
        
        # Verificar parámetros
        if amount is None:
            return await ctx.send("❌ Uso correcto: `bank withdraw [cantidad/all]`")
        
        # Verificar cantidad
        if amount.lower() == "all" or amount.lower() == "todo":
            amount = user_data["bank"]
        else:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send("❌ Por favor, introduce un número válido o 'all'/'todo'.")
        
        if amount <= 0:
            return await ctx.send("❌ La cantidad debe ser mayor que 0.")
        
        if amount > user_data["bank"]:
            return await ctx.send(f"❌ No tienes suficientes conejos en el banco. Solo tienes {user_data['bank']:,} conejos depositados.")
        
        # Transferir conejos
        user_data["bank"] -= amount
        user_data["balance"] += amount
        self.save_data()
        
        # Mensaje de confirmación
        embed = discord.Embed(
            title="💸 Retiro Realizado",
            description=f"Has retirado {amount:,} conejos de tu cuenta bancaria",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Balance Actual",
            value=f"Conejos en mano: {user_data['balance']:,}\n"
                  f"Conejos en banco: {user_data['bank']:,}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @bank.command(name="transfer", aliases=["transferir", "enviar"])
    async def bank_transfer(self, ctx, member: discord.Member, amount: int):
        """💌 Transfiere conejos de tu cuenta bancaria a otro usuario"""
        if member.bot:
            return await ctx.send("❌ No puedes transferir conejos a un bot.")
        
        if member.id == ctx.author.id:
            return await ctx.send("❌ No puedes transferirte conejos a ti mismo.")
        
        if amount <= 0:
            return await ctx.send("❌ La cantidad debe ser mayor que 0.")
        
        sender_id = str(ctx.author.id)
        recipient_id = str(member.id)
        
        sender_data = self.ensure_user(ctx.author.id)
        recipient_data = self.ensure_user(member.id)
        
        # Verificar si tiene suficientes conejos en el banco
        if sender_data["bank"] < amount:
            return await ctx.send("❌ No tienes suficientes conejos en tu cuenta bancaria.")
        
        # Calcular comisión de transferencia
        fee_percent = self.bank_config["transfer_fee_percent"]
        
        # Descuento si tiene certificado bancario
        has_certificate = "bank_certificate" in sender_data.get("inventory", {}) and sender_data["inventory"]["bank_certificate"] > 0
        if has_certificate:
            fee_percent = fee_percent / 2  # Reducir la comisión a la mitad
        
        fee = math.floor(amount * fee_percent)
        amount_after_fee = amount - fee
        
        # Transferir conejos
        sender_data["bank"] -= amount
        recipient_data["bank"] += amount_after_fee
        self.save_data()
        
        # Mensaje de confirmación
        embed = discord.Embed(
            title="🏦 Transferencia Bancaria",
            description=f"Has transferido conejos a {member.display_name}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Detalles",
            value=f"Cantidad enviada: {amount:,} conejos\n"
                  f"Comisión bancaria: {fee:,} conejos ({fee_percent*100}%)\n"
                  f"Cantidad recibida: {amount_after_fee:,} conejos",
            inline=False
        )
        
        if has_certificate:
            embed.add_field(
                name="📜 Beneficio",
                value="¡Tu Certificado Bancario ha reducido la comisión!",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @bank.command(name="loan", aliases=["prestamo", "préstamo"])
    async def bank_loan(self, ctx, amount: str = None):
        """💰 Solicita un préstamo bancario"""
        user_id = str(ctx.author.id)
        user_data = self.ensure_user(ctx.author.id)
        
        # Verificar parámetros
        if amount is None:
            return await ctx.send("❌ Uso correcto: `bank loan [cantidad]`")
        
        # Convertir cantidad a un número
        try:
            amount = int(amount)
        except ValueError:
            return await ctx.send("❌ Por favor, introduce un número válido para la cantidad.")
        
        # Comprobar si la cantidad es válida
        if amount < self.bank_config["min_loan"]:
            return await ctx.send(f"❌ El préstamo mínimo es de {self.bank_config['min_loan']} conejos.")
        
        # Comprobar si tiene préstamos vencidos
        loan_info = self.get_loan_info(ctx.author.id)
        if loan_info["overdue"]:
            return await ctx.send("❌ No puedes solicitar un préstamo mientras tengas préstamos vencidos.")
        
        # Calcular límite de préstamo (2x balance total)
        total_balance = user_data["balance"] + user_data["bank"]
        max_loan = total_balance * self.bank_config["max_loan_multiplier"]
        
        # Comprobar límite
        if amount > max_loan:
            return await ctx.send(f"❌ Tu límite de préstamo es de {math.floor(max_loan):,} conejos (2x tu balance total).")
        
        # Verificar deuda total actual
        if loan_info["total_debt"] + amount > max_loan:
            remaining_capacity = max_loan - loan_info["total_debt"]
            if remaining_capacity <= 0:
                return await ctx.send("❌ Ya has alcanzado tu límite de préstamos.")
            else:
                return await ctx.send(f"❌ Solo puedes pedir {math.floor(remaining_capacity):,} conejos más debido a tu deuda actual.")
        
        # Crear el préstamo
        current_time = datetime.utcnow()
        due_date = current_time + timedelta(days=self.bank_config["loan_duration_days"])
        
        new_loan = {
            "amount": amount,
            "interest": self.bank_config["loan_interest_rate"],
            "start_date": current_time.isoformat(),
            "due_date": due_date.isoformat(),
            "status": "active"
        }
        
        if "loans" not in user_data:
            user_data["loans"] = []
            
        user_data["loans"].append(new_loan)
        user_data["balance"] += amount  # El préstamo va directo al balance
        self.save_data()
        
        # Mensaje de confirmación
        embed = discord.Embed(
            title="🏦 Préstamo Aprobado",
            description=f"Has recibido un préstamo de {amount:,} conejos",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📝 Detalles",
            value=f"Cantidad: {amount:,} conejos\n"
                  f"Interés diario: {self.bank_config['loan_interest_rate']*100}%\n"
                  f"Fecha de vencimiento: <t:{int(due_date.timestamp())}:F>\n"
                  f"Días para pagar: {self.bank_config['loan_duration_days']}",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Advertencia",
            value="Si no pagas antes de la fecha de vencimiento, tu crédito se verá afectado y podrías enfrentar penalizaciones.",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @bank.command(name="payloan", aliases=["pagarprestamo", "pagarpréstamo"])
    async def bank_payloan(self, ctx, amount: str = None):
        """📝 Paga tus préstamos pendientes"""
        user_id = str(ctx.author.id)
        user_data = self.ensure_user(ctx.author.id)
        
        # Verificar parámetros
        if amount is None:
            return await ctx.send("❌ Uso correcto: `bank payloan [cantidad/all]`")
            
        # Obtener información de préstamos
        loan_info = self.get_loan_info(ctx.author.id)
        total_debt = loan_info["total_debt"]
        
        if not loan_info["active"] and not loan_info["overdue"]:
            return await ctx.send("🎉 No tienes préstamos pendientes.")
        
        # Calcular cantidad a pagar
        if amount.lower() == "all" or amount.lower() == "todo":
            amount = total_debt
        else:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send("❌ Por favor, introduce un número válido o 'all'/'todo'.")
        
        if amount <= 0:
            return await ctx.send("❌ La cantidad debe ser mayor que 0.")
        
        if amount > total_debt:
            amount = total_debt  # Limitar al total de la deuda
        
        # Verificar si tiene suficientes fondos
        if user_data["balance"] < amount:
            return await ctx.send(f"❌ No tienes suficientes conejos. Necesitas {math.floor(amount):,} conejos.")
        
        # Procesar el pago
        user_data["balance"] -= math.floor(amount)
        remaining = amount
        
        # Pagar préstamos vencidos primero, luego activos
        paid_loans = 0
        
        # Convertir user_data["loans"] a una lista si no lo es
        if not isinstance(user_data["loans"], list):
            user_data["loans"] = []
        
        # Procesar todos los préstamos activos
        for loan in user_data["loans"]:
            if loan["status"] != "active":
                continue
                
            loan_amount = loan["amount"]
            interest = loan["interest"]
            start_date = datetime.fromisoformat(loan["start_date"])
            
            # Calcular deuda actual
            days_passed = (datetime.utcnow() - start_date).days
            current_debt = loan_amount + (loan_amount * interest * days_passed)
            
            if remaining >= current_debt:
                # Pago completo
                loan["status"] = "repaid"
                loan["repaid_date"] = datetime.utcnow().isoformat()
                loan["paid_amount"] = current_debt
                remaining -= current_debt
                paid_loans += 1
            else:
                # Pago parcial (reducir capital)
                reduction = remaining / (1 + (interest * days_passed))
                loan["amount"] -= reduction
                remaining = 0
                break
        
        self.save_data()
        
        # Mensaje de confirmación
        embed = discord.Embed(
            title="💰 Pago de Préstamo",
            description=f"Has pagado {math.floor(amount - remaining):,} conejos de tu deuda",
            color=discord.Color.green()
        )
        
        if paid_loans > 0:
            embed.add_field(
                name="🎉 Préstamos Completados",
                value=f"Has pagado completamente {paid_loans} préstamo(s)",
                inline=False
            )
        
        # Verificar deuda restante
        new_loan_info = self.get_loan_info(ctx.author.id)
        if new_loan_info["total_debt"] > 0:
            embed.add_field(
                name="📝 Deuda Restante",
                value=f"{math.floor(new_loan_info['total_debt']):,} conejos",
                inline=False
            )
        else:
            embed.add_field(
                name="🎊 ¡Felicidades!",
                value="¡Has pagado toda tu deuda!",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    # COMANDOS DE PROPIEDADES
    
    @commands.group(name="properties", aliases=["propiedades", "inmuebles"], invoke_without_command=True)
    async def properties(self, ctx):
        """🏘️ Sistema de propiedades inmobiliarias para obtener ingresos pasivos"""
        # Mostrar propiedades disponibles para comprar
        embed = discord.Embed(
            title="🏘️ Propiedades Inmobiliarias",
            description="Propiedades disponibles para comprar:",
            color=discord.Color.blue()
        )
        
        # Organizar por precio
        sorted_properties = sorted(self.properties.items(), key=lambda x: x[1]["price"])
        
        for prop_id, prop_data in sorted_properties:
            embed.add_field(
                name=f"{prop_data['name']} - {prop_data['price']:,} conejos",
                value=f"ID: `{prop_id}`\n"
                      f"{prop_data['description']}\n"
                      f"Ingreso: {prop_data['income']:,} conejos cada {prop_data['collection_time']}h",
                inline=False
            )
        
        embed.set_footer(text="Usa 'properties buy [id]' para comprar una propiedad")
        return await ctx.send(embed=embed)
    
    @properties.command(name="my", aliases=["mis"])
    async def properties_my(self, ctx):
        """📋 Muestra tus propiedades inmobiliarias"""
        user_id = str(ctx.author.id)
        user_data = self.ensure_user(ctx.author.id)
        
        # Mostrar propiedades del usuario
        if not user_data.get("properties"):
            return await ctx.send("🏠 No tienes propiedades. Usa `properties list` para ver las disponibles.")
        
        embed = discord.Embed(
            title=f"🏘️ Propiedades de {ctx.author.display_name}",
            description="Tus propiedades inmobiliarias:",
            color=discord.Color.green()
        )
        
        total_income = 0
        for prop_id, prop_data in user_data["properties"].items():
            if prop_id in self.properties:
                property_info = self.properties[prop_id]
                
                # Calcular tiempo para siguiente colección
                next_collection = "Disponible ahora"
                last_collection = user_data.get("last_property_collection", {}).get(prop_id)
                
                if last_collection:
                    last_time = datetime.fromisoformat(last_collection)
                    next_time = last_time + timedelta(hours=property_info["collection_time"])
                    
                    if datetime.utcnow() < next_time:
                        time_left = next_time - datetime.utcnow()
                        next_collection = self.format_time(time_left.total_seconds())
                
                embed.add_field(
                    name=property_info["name"],
                    value=f"{property_info['description']}\n"
                          f"Ingreso: {property_info['income']:,} conejos cada {property_info['collection_time']}h\n"
                          f"Próxima colección: {next_collection}",
                    inline=False
                )
                
                total_income += property_info["income"]
        
        embed.add_field(
            name="💰 Ingresos Totales",
            value=f"{total_income:,} conejos por ciclo de colección",
            inline=False
        )
        
        embed.set_footer(text="Usa 'properties collect' para recoger tus ingresos")
        return await ctx.send(embed=embed)
        
    @properties.command(name="buy")
    async def properties_buy(self, ctx, property_id=None):
        """🛒 Compra una propiedad inmobiliaria"""
        user_id = str(ctx.author.id)
        user_data = self.ensure_user(ctx.author.id)
        
        # Comprar una propiedad
        if not property_id:
            return await ctx.send("❌ Debes especificar el ID de la propiedad que quieres comprar. Usa `properties list` para ver las disponibles.")
        
        if property_id not in self.properties:
            return await ctx.send(f"❌ La propiedad con ID \"{property_id}\" no existe.")
        
        # Verificar si puede comprar
        can_buy, reason = self.can_afford_property(ctx.author.id, property_id)
        
        if not can_buy:
            return await ctx.send(f"❌ No puedes comprar esta propiedad: {reason}")
        
        # Comprar la propiedad
        property_info = self.properties[property_id]
        property_price = property_info["price"]
        
        # Primero usar balance en mano
        if user_data["balance"] >= property_price:
            user_data["balance"] -= property_price
        else:
            # Usar parte del balance y parte del banco
            remaining = property_price - user_data["balance"]
            user_data["balance"] = 0
            user_data["bank"] -= remaining
        
        # Consumir la escritura de propiedad
        user_data["inventory"]["property_deed"] -= 1
        if user_data["inventory"]["property_deed"] <= 0:
            del user_data["inventory"]["property_deed"]
        
        # Añadir propiedad
        if "properties" not in user_data:
            user_data["properties"] = {}
        
        user_data["properties"][property_id] = {
            "purchased_at": datetime.utcnow().isoformat()
        }
        
        self.save_data()
        
        embed = discord.Embed(
            title="🏠 Propiedad Adquirida",
            description=f"¡Felicidades! Has comprado {property_info['name']}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Detalles",
            value=f"Precio: {property_price:,} conejos\n"
                  f"Ingreso: {property_info['income']:,} conejos cada {property_info['collection_time']}h",
            inline=False
        )
        
        embed.add_field(
            name="📝 Información",
            value="Puedes recoger los ingresos con `properties collect`\n"
                  "Ver tus propiedades con `properties my`",
            inline=False
        )
        
        return await ctx.send(embed=embed)
        
    @properties.command(name="collect")
    async def properties_collect(self, ctx):
        """💵 Recoge los ingresos de tus propiedades"""
        user_id = str(ctx.author.id)
        user_data = self.ensure_user(ctx.author.id)
        
        # Recoger ingresos de propiedades
        if not user_data.get("properties"):
            return await ctx.send("❌ No tienes propiedades para recoger ingresos.")
        
        income, collected = self.collect_property_income(ctx.author.id)
        
        if not collected:
            return await ctx.send("⏱️ No hay ingresos disponibles para recoger todavía.")
        
        embed = discord.Embed(
            title="💰 Ingresos de Propiedades",
            description=f"Has recogido {income:,} conejos de tus propiedades",
            color=discord.Color.gold()
        )
        
        for prop in collected:
            embed.add_field(
                name=prop["name"],
                value=f"Ingresos: {prop['income']:,} conejos",
                inline=False
            )
        
        return await ctx.send(embed=embed)
        
    @properties.command(name="sell")
    async def properties_sell(self, ctx, property_id=None):
        """💸 Vende una de tus propiedades"""
        user_id = str(ctx.author.id)
        user_data = self.ensure_user(ctx.author.id)
        
        # Vender una propiedad (recuperar un % del valor)
        if not property_id:
            return await ctx.send("❌ Debes especificar el ID de la propiedad que quieres vender.")
        
        if "properties" not in user_data or property_id not in user_data["properties"]:
            return await ctx.send("❌ No posees esta propiedad.")
        
        property_info = self.properties.get(property_id)
        if not property_info:
            return await ctx.send("❌ Esta propiedad ya no está disponible.")
        
        # Vender por el 70% del valor
        sell_price = math.floor(property_info["price"] * 0.7)
        
        # Remover propiedad
        del user_data["properties"][property_id]
        if property_id in user_data.get("last_property_collection", {}):
            del user_data.get("last_property_collection")[property_id]
        
        # Añadir dinero
        user_data["balance"] += sell_price
        
        self.save_data()
        
        embed = discord.Embed(
            title="🏠 Propiedad Vendida",
            description=f"Has vendido {property_info['name']} por {sell_price:,} conejos (70% del valor original)",
            color=discord.Color.orange()
        )
        
        return await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economia(bot))