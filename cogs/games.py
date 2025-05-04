import re
import discord
import asyncio
import random
import json
import datetime
import typing as t
from discord.ext import commands


class Games(commands.Cog):
    """🎮 Diviértete con varios mini-juegos interactivos"""

    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # Almacena juegos activos por canal
        self.trivia_categories = {
            "general": "Conocimiento General",
            "ciencia": "Ciencia",
            "historia": "Historia",
            "geografia": "Geografía",
            "entretenimiento": "Entretenimiento",
            "deportes": "Deportes",
            "videojuegos": "Videojuegos",
            "anime": "Anime y Manga"
        }
        self.emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        
        # Cargar preguntas de trivia
        try:
            with open('data/trivia.json', 'r', encoding='utf-8') as f:
                self.trivia_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.trivia_data = self._generate_default_trivia()
            # Guardar datos predeterminados
            with open('data/trivia.json', 'w', encoding='utf-8') as f:
                json.dump(self.trivia_data, f, indent=2, ensure_ascii=False)

    def _generate_default_trivia(self):
        """Genera un conjunto predeterminado de preguntas para trivia"""
        return {
            "general": [
                {
                    "question": "¿Cuál es el río más largo del mundo?",
                    "options": ["Amazonas", "Nilo", "Misisipi", "Yangtsé"],
                    "answer": 0
                },
                {
                    "question": "¿Cuál es el elemento químico más abundante en la corteza terrestre?",
                    "options": ["Hierro", "Silicio", "Oxígeno", "Aluminio"],
                    "answer": 2
                },
                {
                    "question": "¿Quién escribió 'Don Quijote de la Mancha'?",
                    "options": ["Miguel de Cervantes", "Federico García Lorca", "Gabriel García Márquez", "Pablo Neruda"],
                    "answer": 0
                }
            ],
            "ciencia": [
                {
                    "question": "¿Cuál es el hueso más largo del cuerpo humano?",
                    "options": ["Húmero", "Fémur", "Tibia", "Radio"],
                    "answer": 1
                },
                {
                    "question": "¿Cuál es la velocidad de la luz?",
                    "options": ["300,000 km/s", "150,000 km/s", "200,000 km/s", "250,000 km/s"],
                    "answer": 0
                },
                {
                    "question": "¿Cuál es el planeta más grande del Sistema Solar?",
                    "options": ["Tierra", "Júpiter", "Saturno", "Neptuno"],
                    "answer": 1
                }
            ],
            "historia": [
                {
                    "question": "¿En qué año comenzó la Primera Guerra Mundial?",
                    "options": ["1914", "1916", "1918", "1920"],
                    "answer": 0
                },
                {
                    "question": "¿Quién fue el primer emperador romano?",
                    "options": ["Julio César", "Augusto", "Nerón", "Marco Aurelio"],
                    "answer": 1
                },
                {
                    "question": "¿En qué año llegó Cristóbal Colón a América?",
                    "options": ["1492", "1498", "1500", "1510"],
                    "answer": 0
                }
            ],
            "geografia": [
                {
                    "question": "¿Cuál es el país más grande del mundo por territorio?",
                    "options": ["China", "Estados Unidos", "Canadá", "Rusia"],
                    "answer": 3
                },
                {
                    "question": "¿Cuál es la capital de Australia?",
                    "options": ["Sídney", "Melbourne", "Canberra", "Brisbane"],
                    "answer": 2
                },
                {
                    "question": "¿Cuántos continentes hay en el mundo?",
                    "options": ["5", "6", "7", "8"],
                    "answer": 2
                }
            ],
            "entretenimiento": [
                {
                    "question": "¿Qué actor interpretó a Tony Stark / Iron Man en el UCM?",
                    "options": ["Chris Evans", "Chris Hemsworth", "Robert Downey Jr.", "Mark Ruffalo"],
                    "answer": 2
                },
                {
                    "question": "¿Cuál es la película más taquillera de la historia (sin ajustar por inflación)?",
                    "options": ["Avatar", "Avengers: Endgame", "Titanic", "Star Wars: El despertar de la fuerza"],
                    "answer": 1
                },
                {
                    "question": "¿Qué banda lanzó el álbum 'The Dark Side of the Moon'?",
                    "options": ["The Beatles", "Led Zeppelin", "Pink Floyd", "Queen"],
                    "answer": 2
                }
            ],
            "deportes": [
                {
                    "question": "¿Cuántos jugadores hay en un equipo de baloncesto en la cancha?",
                    "options": ["4", "5", "6", "7"],
                    "answer": 1
                },
                {
                    "question": "¿Qué país ha ganado más Copas Mundiales de Fútbol?",
                    "options": ["Alemania", "Italia", "Argentina", "Brasil"],
                    "answer": 3
                },
                {
                    "question": "¿Cuántos aros tiene la bandera olímpica?",
                    "options": ["4", "5", "6", "7"],
                    "answer": 1
                }
            ],
            "videojuegos": [
                {
                    "question": "¿Quién es el protagonista de la saga 'The Legend of Zelda'?",
                    "options": ["Zelda", "Link", "Ganondorf", "Mario"],
                    "answer": 1
                },
                {
                    "question": "¿En qué año se lanzó Minecraft?",
                    "options": ["2009", "2010", "2011", "2012"],
                    "answer": 2
                },
                {
                    "question": "¿Qué compañía desarrolló el juego 'Overwatch'?",
                    "options": ["Valve", "Epic Games", "Blizzard", "Riot Games"],
                    "answer": 2
                }
            ],
            "anime": [
                {
                    "question": "¿Quién es el protagonista de 'Naruto'?",
                    "options": ["Sasuke Uchiha", "Naruto Uzumaki", "Kakashi Hatake", "Sakura Haruno"],
                    "answer": 1
                },
                {
                    "question": "¿Cuál es el anime más largo en emisión?",
                    "options": ["One Piece", "Naruto", "Dragon Ball", "Detective Conan"],
                    "answer": 0
                },
                {
                    "question": "¿Qué estudio animó 'Kimetsu no Yaiba' (Demon Slayer)?",
                    "options": ["MAPPA", "Ufotable", "Kyoto Animation", "Bones"],
                    "answer": 1
                }
            ]
        }

    @commands.command(name="magic8ball", aliases=["bola8", "8b"])
    async def magic_8ball(self, ctx, *, question: str):
        """🔮 Pregunta a la bola mágica 8 y recibe una respuesta mística"""
        responses = [
            "Es cierto.", "Es decididamente así.", "Sin duda.", "Definitivamente sí.",
            "Puedes confiar en ello.", "Como yo lo veo, sí.", "Lo más probable.",
            "Perspectiva buena.", "Sí.", "Las señales apuntan a que sí.",
            "Respuesta confusa, intenta de nuevo.", "Pregunta de nuevo más tarde.",
            "Mejor no te lo digo ahora.", "No puedo predecirlo ahora.",
            "Concéntrate y pregunta de nuevo.", "No cuentes con ello.",
            "Mi respuesta es no.", "Mis fuentes dicen que no.", "Las perspectivas no son buenas.",
            "Muy dudoso."
        ]
        
        # Seleccionar una respuesta aleatoria
        response = random.choice(responses)
        
        # Crear un embed para la respuesta
        embed = discord.Embed(
            title="🔮 La bola mágica dice...",
            description=f"**Pregunta:** {question}\n\n**Respuesta:** {response}",
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Preguntado por {ctx.author}")
        
        await ctx.send(embed=embed)

    @commands.command(name="dado", aliases=["roll", "dice"])
    async def roll_dice(self, ctx, dice: str = "1d6"):
        """🎲 Lanza uno o varios dados. Formato: NdM (ej: 2d20 = 2 dados de 20 caras)"""
        # Verificar formato
        if not dice.lower().replace(" ", "").replace("-", "").replace("+", "").isalnum():
            await ctx.send("❌ Formato incorrecto. Usa `NdM` donde N = número de dados y M = caras.")
            return
            
        try:
            # Buscar modificador
            modifier = 0
            if "+" in dice:
                dice, mod_str = dice.split("+")
                modifier = int(mod_str)
            elif "-" in dice:
                dice, mod_str = dice.split("-")
                modifier = -int(mod_str)
                
            # Separar en cantidad y tipo de dados
            if "d" not in dice.lower():
                await ctx.send("❌ Formato incorrecto. Usa `NdM` donde N = número de dados y M = caras.")
                return
                
            num_dice, num_sides = dice.lower().split("d")
            
            # Valores predeterminados
            if num_dice == "":
                num_dice = "1"
            
            num_dice = int(num_dice)
            num_sides = int(num_sides)
            
            # Limitaciones para evitar spam o sobrecarga
            if num_dice <= 0 or num_dice > 100:
                await ctx.send("⚠️ El número de dados debe estar entre 1 y 100.")
                return
                
            if num_sides <= 1 or num_sides > 1000:
                await ctx.send("⚠️ El número de caras debe estar entre 2 y 1000.")
                return
                
            # Lanzar los dados
            results = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(results) + modifier
            
            # Crear embed con los resultados
            embed = discord.Embed(
                title=f"🎲 Resultados de {dice}",
                color=discord.Color.from_rgb(255, 165, 0)
            )
            
            # Mostrar resultados individuales si no son demasiados
            if num_dice <= 30:
                results_str = ", ".join(str(r) for r in results)
                embed.add_field(name="Tiradas", value=results_str, inline=False)
            
            # Mostrar modificador si hay
            if modifier != 0:
                sign = "+" if modifier > 0 else ""
                embed.add_field(name="Modificador", value=f"{sign}{modifier}", inline=True)
            
            embed.add_field(name="Total", value=str(total), inline=True)
            embed.set_footer(text=f"Tirado por {ctx.author}")
            
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("❌ Formato incorrecto. Usa `NdM` donde N = número de dados y M = caras.")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="trivia")
    @commands.cooldown(1, 15, commands.BucketType.channel)
    async def trivia_game(self, ctx, category: str = None):
        """📝 Juega una ronda de trivia. Puedes especificar una categoría o dejarlo en blanco para aleatorio."""
        # Verificar si hay un juego activo en este canal
        if ctx.channel.id in self.active_games:
            await ctx.send("⚠️ Ya hay un juego activo en este canal. Espera a que termine.")
            return
        
        # Seleccionar categoría
        available_categories = list(self.trivia_data.keys())
        
        if not category:
            # Categoría aleatoria
            selected_category = random.choice(available_categories)
        else:
            # Buscar categoría especificada
            selected_category = None
            for cat in available_categories:
                if cat.lower() == category.lower() or (category.lower() in cat.lower()):
                    selected_category = cat
                    break
            
            if not selected_category:
                # Mostrar categorías disponibles si no se encontró
                cats_display = ", ".join(f"`{cat}`" for cat in available_categories)
                await ctx.send(f"❌ Categoría no encontrada. Categorías disponibles: {cats_display}")
                return
        
        # Seleccionar pregunta aleatoria de la categoría
        try:
            question_data = random.choice(self.trivia_data[selected_category])
            question = question_data["question"]
            options = question_data["options"]
            correct_idx = question_data["answer"]
            correct_answer = options[correct_idx]
            
            # Marcar juego como activo
            self.active_games[ctx.channel.id] = True
            
            # Crear embed para la pregunta
            embed = discord.Embed(
                title=f"📝 Trivia: {self.trivia_categories.get(selected_category, selected_category.capitalize())}",
                description=question,
                color=discord.Color.blue()
            )
            
            # Añadir opciones
            options_text = ""
            for i, option in enumerate(options):
                options_text += f"{self.emoji_numbers[i]} {option}\n"
            
            embed.add_field(name="Opciones", value=options_text, inline=False)
            embed.set_footer(text="Responde reaccionando con el número de la respuesta correcta. Tienes 15 segundos.")
            
            # Enviar pregunta
            message = await ctx.send(embed=embed)
            
            # Añadir reacciones para opciones
            for i in range(len(options)):
                await message.add_reaction(self.emoji_numbers[i])
            
            # Esperar respuestas
            try:
                def check(reaction, user):
                    return (
                        user != self.bot.user and
                        reaction.message.id == message.id and
                        str(reaction.emoji) in self.emoji_numbers[:len(options)]
                    )
                
                # Dictionary para rastrear quién respondió y con qué
                responses = {}
                
                # Tiempo límite para respuestas
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=15)
                
                while datetime.datetime.now() < end_time:
                    try:
                        reaction, user = await self.bot.wait_for(
                            'reaction_add',
                            timeout=(end_time - datetime.datetime.now()).total_seconds(),
                            check=check
                        )
                        
                        # Registrar respuesta (solo la primera por usuario)
                        if user.id not in responses:
                            selected_option = self.emoji_numbers.index(str(reaction.emoji))
                            responses[user.id] = {
                                'user': user,
                                'option': selected_option,
                                'correct': selected_option == correct_idx
                            }
                    except asyncio.TimeoutError:
                        # Tiempo agotado para esta iteración, seguir esperando si aún hay tiempo
                        break
                
                # Procesar resultados
                if not responses:
                    await ctx.send("😢 Nadie respondió a la pregunta. La respuesta correcta era: " +
                                  f"**{correct_answer}**")
                else:
                    # Crear embed de resultados
                    results_embed = discord.Embed(
                        title="📊 Resultados de Trivia",
                        description=f"**Pregunta:** {question}\n**Respuesta correcta:** {correct_answer}",
                        color=discord.Color.green()
                    )
                    
                    # Listas de ganadores y perdedores
                    winners = []
                    losers = []
                    
                    for user_id, data in responses.items():
                        user = data['user']
                        selected = options[data['option']]
                        
                        if data['correct']:
                            winners.append(f"{user.mention} ✅ ({selected})")
                        else:
                            losers.append(f"{user.mention} ❌ ({selected})")
                    
                    if winners:
                        results_embed.add_field(
                            name=f"🏆 Respuestas correctas ({len(winners)})",
                            value="\n".join(winners) or "Ninguna",
                            inline=False
                        )
                    
                    if losers:
                        results_embed.add_field(
                            name=f"❌ Respuestas incorrectas ({len(losers)})",
                            value="\n".join(losers) or "Ninguna",
                            inline=False
                        )
                    
                    await ctx.send(embed=results_embed)
            
            finally:
                # Limpiar el estado del juego
                if ctx.channel.id in self.active_games:
                    del self.active_games[ctx.channel.id]
        
        except (IndexError, KeyError):
            await ctx.send("❌ Error al obtener pregunta de trivia. Por favor intenta otra categoría.")
            # Limpiar el estado del juego
            if ctx.channel.id in self.active_games:
                del self.active_games[ctx.channel.id]

    @commands.command(name="ahorcado", aliases=["hangman"])
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def hangman_game(self, ctx):
        """🎮 Juega al ahorcado clásico con diferentes categorías de palabras"""
        # Verificar si hay un juego activo en este canal
        if ctx.channel.id in self.active_games:
            await ctx.send("⚠️ Ya hay un juego activo en este canal. Espera a que termine.")
            return
        
        # Categorías y palabras
        categories = {
            "Animales": [
                "perro", "gato", "elefante", "tigre", "ballena", "delfin", "koala",
                "aguila", "serpiente", "tortuga", "pinguino", "rinoceronte"
            ],
            "Frutas": [
                "manzana", "platano", "naranja", "uva", "pera", "sandia", "melon",
                "piña", "mango", "fresa", "kiwi", "cereza", "limon"
            ],
            "Países": [
                "españa", "francia", "italia", "alemania", "japon", "brasil", "argentina",
                "mexico", "canada", "rusia", "china", "australia", "egipto"
            ],
            "Videojuegos": [
                "minecraft", "fortnite", "tetris", "zelda", "pokemon", "mario", "sonic",
                "doom", "metroid", "halo", "portal", "fifa", "skyrim"
            ]
        }
        
        # Seleccionar categoría y palabra
        category_name = random.choice(list(categories.keys()))
        word = random.choice(categories[category_name]).upper()
        word_display = ["_" for _ in word]
        guessed_letters = []
        attempts_left = 6
        
        # Etapas del ahorcado
        hangman_stages = [
            "```\n   +---+\n   |   |\n       |\n       |\n       |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n       |\n       |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n   |   |\n       |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n  /|   |\n       |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n  /|\\  |\n       |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n  /|\\  |\n  /    |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n  /|\\  |\n  / \\  |\n       |\n=========```"
        ]
        
        # Marcar juego como activo
        self.active_games[ctx.channel.id] = True
        
        try:
            # Crear y enviar el mensaje inicial
            embed = discord.Embed(
                title=f"🎮 Ahorcado: {category_name}",
                description=f"{hangman_stages[6-attempts_left]}\n\nPalabra: {' '.join(word_display)}\n\nLetras adivinadas: {', '.join(guessed_letters) if guessed_letters else 'Ninguna'}\n\nIntentos restantes: {attempts_left}",
                color=discord.Color.gold()
            )
            embed.set_footer(text="Escribe una letra para adivinar. Tienes 60 segundos por turno.")
            game_message = await ctx.send(embed=embed)
            
            # Bucle principal del juego
            while attempts_left > 0 and "_" in word_display:
                # Esperar la respuesta del jugador
                try:
                    def check(m):
                        return (
                            m.channel == ctx.channel and
                            not m.author.bot and
                            len(m.content) == 1 and
                            m.content.isalpha()
                        )
                    
                    guess_message = await self.bot.wait_for('message', timeout=60.0, check=check)
                    guess = guess_message.content.upper()
                    
                    # Verificar si la letra ya fue adivinada
                    if guess in guessed_letters:
                        await ctx.send(f"⚠️ Ya adivinaste la letra '{guess}'. Intenta con otra.", delete_after=5)
                        continue
                    
                    # Añadir a letras adivinadas
                    guessed_letters.append(guess)
                    
                    # Verificar si la letra está en la palabra
                    if guess in word:
                        # Actualizar el display de la palabra
                        for i, letter in enumerate(word):
                            if letter == guess:
                                word_display[i] = guess
                        
                        # Mensaje de éxito
                        if "_" not in word_display:
                            # ¡Victoria!
                            embed = discord.Embed(
                                title="🎮 Ahorcado: ¡Victoria!",
                                description=f"{hangman_stages[6-attempts_left]}\n\nPalabra: {' '.join(word_display)}\n\n🎉 ¡Felicidades! Han adivinado la palabra correctamente.\n\nLa palabra era: **{word}**",
                                color=discord.Color.green()
                            )
                            await game_message.edit(embed=embed)
                            break
                        else:
                            await ctx.send(f"✅ ¡Correcto! La letra '{guess}' está en la palabra.", delete_after=5)
                    else:
                        # Letra incorrecta
                        attempts_left -= 1
                        await ctx.send(f"❌ La letra '{guess}' no está en la palabra. Te quedan {attempts_left} intentos.", delete_after=5)
                        
                        # Verificar derrota
                        if attempts_left <= 0:
                            embed = discord.Embed(
                                title="🎮 Ahorcado: Derrota",
                                description=f"{hangman_stages[6]}\n\nPalabra: {' '.join(word)}\n\n😢 ¡Oh no! Se han quedado sin intentos.\n\nLa palabra era: **{word}**",
                                color=discord.Color.red()
                            )
                            await game_message.edit(embed=embed)
                            break
                    
                    # Actualizar el mensaje del juego
                    embed = discord.Embed(
                        title=f"🎮 Ahorcado: {category_name}",
                        description=f"{hangman_stages[6-attempts_left]}\n\nPalabra: {' '.join(word_display)}\n\nLetras adivinadas: {', '.join(guessed_letters)}\n\nIntentos restantes: {attempts_left}",
                        color=discord.Color.gold()
                    )
                    embed.set_footer(text="Escribe una letra para adivinar. Tienes 60 segundos por turno.")
                    await game_message.edit(embed=embed)
                    
                except asyncio.TimeoutError:
                    # Tiempo agotado
                    embed = discord.Embed(
                        title="🎮 Ahorcado: Tiempo agotado",
                        description=f"{hangman_stages[6-attempts_left]}\n\nPalabra: {' '.join(word)}\n\n⏰ ¡Se acabó el tiempo!\n\nLa palabra era: **{word}**",
                        color=discord.Color.red()
                    )
                    await game_message.edit(embed=embed)
                    break
        
        finally:
            # Limpiar el estado del juego
            if ctx.channel.id in self.active_games:
                del self.active_games[ctx.channel.id]

    @commands.command(name="ppt", aliases=["rps"])
    async def rock_paper_scissors(self, ctx):
        """✂️ Juega a Piedra, Papel o Tijera contra el bot"""
        # Opciones y emojis
        options = {
            "🪨": "Piedra",
            "📄": "Papel",
            "✂️": "Tijera"
        }
        
        # Reglas del juego (qué gana a qué)
        # clave gana a valor
        rules = {
            "🪨": "✂️",  # Piedra gana a Tijera
            "📄": "🪨",  # Papel gana a Piedra
            "✂️": "📄"   # Tijera gana a Papel
        }
        
        # Crear embed para la selección
        embed = discord.Embed(
            title="✂️ Piedra, Papel o Tijera",
            description="Elige tu jugada reaccionando a una de las opciones abajo.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Tienes 15 segundos para elegir.")
        
        # Enviar mensaje y añadir reacciones
        message = await ctx.send(embed=embed)
        for emoji in options.keys():
            await message.add_reaction(emoji)
        
        try:
            # Esperar la elección del usuario
            def check(reaction, user):
                return (
                    user == ctx.author and
                    reaction.message.id == message.id and
                    str(reaction.emoji) in options.keys()
                )
            
            reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
            player_choice = str(reaction.emoji)
            
            # Elección aleatoria para el bot
            bot_choice = random.choice(list(options.keys()))
            
            # Determinar ganador
            result = ""
            if player_choice == bot_choice:
                result = "🤝 ¡Empate!"
                color = discord.Color.gold()
            elif rules[player_choice] == bot_choice:
                result = "🎉 ¡Has ganado!"
                color = discord.Color.green()
            else:
                result = "😢 ¡Has perdido!"
                color = discord.Color.red()
            
            # Crear embed de resultados
            result_embed = discord.Embed(
                title="✂️ Resultados: Piedra, Papel o Tijera",
                description=f"**Tu elección:** {options[player_choice]} {player_choice}\n**Mi elección:** {options[bot_choice]} {bot_choice}\n\n**{result}**",
                color=color
            )
            
            await message.edit(embed=result_embed)
            
        except asyncio.TimeoutError:
            await message.edit(content="⏰ Tiempo agotado. No elegiste a tiempo.", embed=None)
            # Intentar eliminar las reacciones
            try:
                await message.clear_reactions()
            except:
                pass

    @commands.command(name="sorteo", aliases=["giveaway"])
    @commands.has_permissions(manage_guild=True)
    async def giveaway(self, ctx, tiempo: str, *, premio: str):
        """🎁 Inicia un sorteo con un premio específico. Uso: sorteo 1h Premio especial"""
        # Parsear tiempo (formatos: 30s, 5m, 2h, 1d)
        duration_seconds = 0
        time_regex = r"(\d+)([smhd])"
        
        # Limpiar la entrada de tiempo y eliminar espacios
        tiempo_limpio = tiempo.lower().strip()
        
        # Usar findall para obtener todos los pares de número y unidad
        matches = re.findall(time_regex, tiempo_limpio)
        
        if not matches:
            await ctx.send("❌ Formato de tiempo inválido. Usa formatos como: 30s, 5m, 2h, 1d")
            return
            
        for value, unit in matches:
            value = int(value)
            if unit == 's':
                duration_seconds += value
            elif unit == 'm':
                duration_seconds += value * 60
            elif unit == 'h':
                duration_seconds += value * 3600
            elif unit == 'd':
                duration_seconds += value * 86400
        
        if duration_seconds < 10 or duration_seconds > 604800:  # Entre 10 segundos y 7 días
            await ctx.send("⚠️ El tiempo debe estar entre 10 segundos y 7 días.")
            return
        
        # Calcular el tiempo de finalización
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=duration_seconds)
        
        # Crear embed para el sorteo
        embed = discord.Embed(
            title="🎁 ¡NUEVO SORTEO!",
            description=f"**Premio:** {premio}\n\n**Finaliza:** <t:{int(end_time.timestamp())}:R>\n\nReacciona con 🎉 para participar!",
            color=discord.Color.from_rgb(255, 127, 80)
        )
        embed.set_footer(text=f"Organizado por {ctx.author} • Finaliza")
        embed.timestamp = end_time
        
        # Enviar mensaje y añadir la reacción
        giveaway_msg = await ctx.send(embed=embed)
        await giveaway_msg.add_reaction("🎉")
        
        # Esperar a que termine el sorteo
        await asyncio.sleep(duration_seconds)
        
        # Obtener mensaje actualizado para ver las reacciones
        try:
            giveaway_msg = await ctx.channel.fetch_message(giveaway_msg.id)
            reaction = discord.utils.get(giveaway_msg.reactions, emoji="🎉")
            
            # Obtener participantes (excluir al bot)
            users = []
            async for user in reaction.users():
                if user != self.bot.user:
                    users.append(user)
            
            # Verificar si hay participantes
            if users:
                winner = random.choice(users)
                
                # Embed de resultados
                result_embed = discord.Embed(
                    title="🎉 ¡SORTEO FINALIZADO!",
                    description=f"**Premio:** {premio}\n\n**Ganador:** {winner.mention}\n\n**Total de participantes:** {len(users)}",
                    color=discord.Color.green()
                )
                result_embed.set_footer(text=f"Organizado por {ctx.author}")
                
                await giveaway_msg.edit(embed=result_embed)
                await ctx.send(f"🎊 ¡Felicidades {winner.mention}! Has ganado: **{premio}**")
            else:
                # No hay participantes
                result_embed = discord.Embed(
                    title="🎁 ¡SORTEO FINALIZADO!",
                    description=f"**Premio:** {premio}\n\n😢 No hubo participantes.",
                    color=discord.Color.red()
                )
                result_embed.set_footer(text=f"Organizado por {ctx.author}")
                
                await giveaway_msg.edit(embed=result_embed)
                await ctx.send("😢 El sorteo ha finalizado pero no hubo participantes.")
                
        except discord.NotFound:
            # Mensaje eliminado
            pass
        except Exception as e:
            await ctx.send(f"❌ Error al finalizar el sorteo: {str(e)}")

    @commands.command(name="adivina", aliases=["guess"])
    @commands.cooldown(1, 20, commands.BucketType.channel)
    async def guess_number(self, ctx):
        """🔢 Juega a adivinar un número entre 1 y 100"""
        # Verificar si hay un juego activo en este canal
        if ctx.channel.id in self.active_games:
            await ctx.send("⚠️ Ya hay un juego activo en este canal. Espera a que termine.")
            return
        
        # Marcar juego como activo
        self.active_games[ctx.channel.id] = True
        
        try:
            # Generar número aleatorio
            number = random.randint(1, 100)
            attempts = 0
            max_attempts = 10
            
            # Crear embed para el juego
            embed = discord.Embed(
                title="🔢 ¡Adivina el Número!",
                description=f"He pensado en un número entre 1 y 100.\n¿Puedes adivinarlo en {max_attempts} intentos o menos?",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Escribe un número para adivinar.")
            
            await ctx.send(embed=embed)
            
            # Límite de tiempo total para el juego
            end_time = datetime.datetime.now() + datetime.timedelta(minutes=2)
            
            while attempts < max_attempts and datetime.datetime.now() < end_time:
                try:
                    # Esperar respuesta
                    def check(m):
                        return (
                            m.channel == ctx.channel and
                            not m.author.bot and
                            m.content.isdigit() and
                            1 <= int(m.content) <= 100
                        )
                    
                    guess_message = await self.bot.wait_for(
                        'message',
                        timeout=(end_time - datetime.datetime.now()).total_seconds(),
                        check=check
                    )
                    
                    guess = int(guess_message.content)
                    attempts += 1
                    
                    # Comprobar la respuesta
                    if guess == number:
                        # ¡Ganador!
                        embed = discord.Embed(
                            title="🎉 ¡Correcto!",
                            description=f"¡Felicidades {guess_message.author.mention}! Has adivinado el número {number} en {attempts} intentos.",
                            color=discord.Color.green()
                        )
                        await ctx.send(embed=embed)
                        break
                    elif guess < number:
                        await ctx.send(f"📈 El número es **mayor** que {guess}. Intentos restantes: {max_attempts - attempts}", delete_after=5)
                    else:
                        await ctx.send(f"📉 El número es **menor** que {guess}. Intentos restantes: {max_attempts - attempts}", delete_after=5)
                    
                    # Verificar si se acabaron los intentos
                    if attempts >= max_attempts:
                        embed = discord.Embed(
                            title="😢 ¡Se acabaron los intentos!",
                            description=f"El número era **{number}**. ¡Mejor suerte la próxima vez!",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        break
                
                except asyncio.TimeoutError:
                    # Tiempo agotado
                    embed = discord.Embed(
                        title="⏰ ¡Tiempo agotado!",
                        description=f"El número era **{number}**. ¡Mejor suerte la próxima vez!",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    break
        
        finally:
            # Limpiar el estado del juego
            if ctx.channel.id in self.active_games:
                del self.active_games[ctx.channel.id]

    @commands.command(name="tictactoe", aliases=["gato", "tresenraya"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def tictactoe(self, ctx, opponent: discord.Member = None):
        """❌⭕ Juega al tres en raya (tic-tac-toe) contra alguien o contra el bot"""
        # Verificar si el oponente es válido
        if opponent is None:
            # Jugar contra el bot
            opponent = self.bot.user
        elif opponent == ctx.author:
            await ctx.send("❌ No puedes jugar contra ti mismo.")
            return
        elif opponent.bot and opponent != self.bot.user:
            await ctx.send("❌ No puedes jugar contra otros bots.")
            return
        
        # Verificar si hay un juego activo para el autor
        if ctx.author.id in self.active_games:
            await ctx.send("⚠️ Ya tienes un juego activo. Termínalo antes de iniciar uno nuevo.")
            return
        
        # Si el oponente es un usuario, verificar si tiene un juego activo
        if opponent != self.bot.user and opponent.id in self.active_games:
            await ctx.send(f"⚠️ {opponent.display_name} ya tiene un juego activo.")
            return
        
        # Marcar juego como activo para ambos jugadores
        self.active_games[ctx.author.id] = True
        if opponent != self.bot.user:
            self.active_games[opponent.id] = True
        
        try:
            # Inicializar tablero vacío (3x3)
            board = [" " for _ in range(9)]
            
            # Asignar símbolos
            current_player = ctx.author
            symbols = {ctx.author: "❌", opponent: "⭕"}
            
            # Crear mensaje inicial
            embed, view = self._create_tictactoe_message(board, current_player, symbols, ctx.author, opponent)
            game_message = await ctx.send(embed=embed, view=view)
            
            # Si juega contra el bot y el bot va primero, hacer su jugada
            if opponent == self.bot.user and current_player == opponent:
                # Bot hace su movimiento
                move = self._get_bot_move(board)
                board[move] = symbols[opponent]
                current_player = ctx.author
                
                # Actualizar mensaje
                embed, view = self._create_tictactoe_message(board, current_player, symbols, ctx.author, opponent)
                await game_message.edit(embed=embed, view=view)
            
            # Bucle principal del juego
            while " " in board and not self._check_winner(board, symbols[ctx.author]) and not self._check_winner(board, symbols[opponent]):
                # Si es turno del bot, hacer su jugada
                if current_player == opponent and opponent == self.bot.user:
                    await asyncio.sleep(1)  # Pausa para simular "pensamiento"
                    
                    # Bot hace su movimiento
                    move = self._get_bot_move(board)
                    board[move] = symbols[opponent]
                    current_player = ctx.author
                    
                    # Verificar victoria o empate
                    if self._check_winner(board, symbols[opponent]):
                        # Bot gana
                        result_embed = discord.Embed(
                            title="❌⭕ Tres en Raya: ¡Final!",
                            description=self._format_board(board),
                            color=discord.Color.red()
                        )
                        result_embed.add_field(name="Resultado", value=f"😢 ¡Has perdido contra el bot!", inline=False)
                        await game_message.edit(embed=result_embed, view=None)
                        break
                    elif " " not in board:
                        # Empate
                        result_embed = discord.Embed(
                            title="❌⭕ Tres en Raya: ¡Final!",
                            description=self._format_board(board),
                            color=discord.Color.gold()
                        )
                        result_embed.add_field(name="Resultado", value="🤝 ¡Empate!", inline=False)
                        await game_message.edit(embed=result_embed, view=None)
                        break
                    
                    # Actualizar mensaje
                    embed, view = self._create_tictactoe_message(board, current_player, symbols, ctx.author, opponent)
                    await game_message.edit(embed=embed, view=view)
                    continue
                
                # Esperar el movimiento del jugador humano
                try:
                    def check(m):
                        # Aceptar números del 1-9 del jugador actual
                        return (
                            m.author == current_player and
                            m.channel == ctx.channel and
                            m.content.isdigit() and
                            1 <= int(m.content) <= 9 and
                            board[int(m.content) - 1] == " "  # Asegurar que la casilla esté vacía
                        )
                    
                    move_message = await self.bot.wait_for('message', timeout=30.0, check=check)
                    
                    # Procesar movimiento
                    move = int(move_message.content) - 1
                    board[move] = symbols[current_player]
                    
                    # Cambiar jugador
                    current_player = opponent if current_player == ctx.author else ctx.author
                    
                    # Verificar victoria o empate
                    if self._check_winner(board, symbols[ctx.author]):
                        # Autor gana
                        result_embed = discord.Embed(
                            title="❌⭕ Tres en Raya: ¡Final!",
                            description=self._format_board(board),
                            color=discord.Color.green()
                        )
                        result_embed.add_field(name="Resultado", value=f"🎉 ¡{ctx.author.display_name} ha ganado!", inline=False)
                        await game_message.edit(embed=result_embed, view=None)
                        break
                    elif self._check_winner(board, symbols[opponent]) and opponent != self.bot.user:
                        # Oponente humano gana
                        result_embed = discord.Embed(
                            title="❌⭕ Tres en Raya: ¡Final!",
                            description=self._format_board(board),
                            color=discord.Color.blue()
                        )
                        result_embed.add_field(name="Resultado", value=f"🎉 ¡{opponent.display_name} ha ganado!", inline=False)
                        await game_message.edit(embed=result_embed, view=None)
                        break
                    elif " " not in board:
                        # Empate
                        result_embed = discord.Embed(
                            title="❌⭕ Tres en Raya: ¡Final!",
                            description=self._format_board(board),
                            color=discord.Color.gold()
                        )
                        result_embed.add_field(name="Resultado", value="🤝 ¡Empate!", inline=False)
                        await game_message.edit(embed=result_embed, view=None)
                        break
                    
                    # Actualizar mensaje
                    embed, view = self._create_tictactoe_message(board, current_player, symbols, ctx.author, opponent)
                    await game_message.edit(embed=embed, view=view)
                    
                except asyncio.TimeoutError:
                    # Tiempo agotado
                    timeout_embed = discord.Embed(
                        title="❌⭕ Tres en Raya: ¡Tiempo agotado!",
                        description=f"{self._format_board(board)}\n\n⏰ {current_player.display_name} tardó demasiado en realizar su movimiento.",
                        color=discord.Color.red()
                    )
                    await game_message.edit(embed=timeout_embed, view=None)
                    break
        
        finally:
            # Limpiar el estado del juego para ambos jugadores
            if ctx.author.id in self.active_games:
                del self.active_games[ctx.author.id]
            if opponent != self.bot.user and opponent.id in self.active_games:
                del self.active_games[opponent.id]

    def _create_tictactoe_message(self, board, current_player, symbols, player1, player2):
        """Crea el mensaje para el juego de tres en raya"""
        embed = discord.Embed(
            title="❌⭕ Tres en Raya",
            description=f"{self._format_board(board)}\n\n**Turno de:** {current_player.mention} ({symbols[current_player]})",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Jugadores", value=f"❌: {player1.display_name}\n⭕: {player2.display_name}", inline=True)
        embed.add_field(name="Cómo jugar", value="Escribe un número del 1 al 9 para colocar tu símbolo.\n```\n1 | 2 | 3\n---------\n4 | 5 | 6\n---------\n7 | 8 | 9\n```", inline=True)
        
        # Crear vista con botones (para representación visual, no funcionales en este ejemplo)
        view = discord.ui.View()
        
        return embed, view

    def _format_board(self, board):
        """Formatea el tablero para mostrar en el mensaje"""
        rows = [
            f"{board[0]} | {board[1]} | {board[2]}",
            "─────────",
            f"{board[3]} | {board[4]} | {board[5]}",
            "─────────",
            f"{board[6]} | {board[7]} | {board[8]}"
        ]
        return "```\n" + "\n".join(rows) + "\n```"

    def _check_winner(self, board, symbol):
        """Verifica si hay un ganador"""
        # Combinaciones ganadoras (filas, columnas, diagonales)
        win_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Filas
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columnas
            [0, 4, 8], [2, 4, 6]               # Diagonales
        ]
        
        # Verificar cada combinación
        for combo in win_combinations:
            if all(board[i] == symbol for i in combo):
                return True
        
        return False

    def _get_bot_move(self, board):
        """Determina el movimiento del bot en el juego de tres en raya"""
        # Lista de casillas disponibles
        available_moves = [i for i, spot in enumerate(board) if spot == " "]
        
        # Estrategia simple para el bot:
        # 1. Si hay un movimiento ganador, tomarlo
        # 2. Si hay un movimiento bloqueador, tomarlo
        # 3. Si el centro está disponible, tomarlo
        # 4. Si una esquina está disponible, tomarla
        # 5. Tomar cualquier movimiento disponible
        
        # Símbolos para el bot y el jugador
        bot_symbol = "⭕"
        player_symbol = "❌"
        
        # Verificar movimientos ganadores para el bot
        for move in available_moves:
            board_copy = board.copy()
            board_copy[move] = bot_symbol
            if self._check_winner(board_copy, bot_symbol):
                return move
        
        # Verificar movimientos bloqueadores (evitar que el jugador gane)
        for move in available_moves:
            board_copy = board.copy()
            board_copy[move] = player_symbol
            if self._check_winner(board_copy, player_symbol):
                return move
        
        # Preferir el centro
        if 4 in available_moves:
            return 4
        
        # Preferir las esquinas
        corners = [0, 2, 6, 8]
        available_corners = [corner for corner in corners if corner in available_moves]
        if available_corners:
            return random.choice(available_corners)
        
        # Tomar cualquier movimiento disponible
        return random.choice(available_moves)


async def setup(bot):
    await bot.add_cog(Games(bot))