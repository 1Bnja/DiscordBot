import discord
from discord.ext import commands
import random
import logging
from collections import defaultdict

logger = logging.getLogger('discord_bot.fama_toque')

class FamaToque(commands.Cog):
    """Juego de Fama y Toque"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # {user_id: {"number": "1234", "attempts": 0, "guesses": []}}
    
    def generate_secret_number(self):
        """Genera un número secreto de 4 cifras con dígitos diferentes"""
        digits = list(range(10))  # 0-9
        random.shuffle(digits)
        secret_number = ''.join(map(str, digits[:4]))
        return secret_number
    
    def evaluate_guess(self, secret_number, guess):
        """Evalúa el intento del usuario y devuelve famas y toques"""
        famas = 0
        toques = 0
        
        # Contar famas (número correcto en posición correcta)
        for i in range(4):
            if guess[i] == secret_number[i]:
                famas += 1
        
        # Contar toques (número correcto en posición incorrecta)
        for i in range(4):
            if guess[i] in secret_number and guess[i] != secret_number[i]:
                toques += 1
                
        return famas, toques
    
    @commands.command(name='famatoque', aliases=['ft', 'jugar'])
    async def start_game(self, ctx):
        """Inicia un nuevo juego de Fama y Toque"""
        user_id = ctx.author.id
        
        # Si el usuario ya tiene un juego activo
        if user_id in self.active_games:
            await ctx.send(f"❌ Ya tienes un juego en curso. Usa `!rendirse` para terminar el juego actual.")
            return
        
        # Crear nuevo juego
        secret_number = self.generate_secret_number()
        self.active_games[user_id] = {
            "number": secret_number,
            "attempts": 0,
            "guesses": []
        }
        
        logger.info(f"Nuevo juego para {ctx.author.name} - Número secreto: {secret_number}")
        
        embed = discord.Embed(
            title="🎮 Fama y Toque",
            description=(
                "He generado un número secreto de 4 dígitos. "
                "Tienes 7 intentos para adivinarlo.\n\n"
                "**REGLAS:**\n"
                "• **Fama**: Dígito correcto en posición correcta\n"
                "• **Toque**: Dígito correcto en posición incorrecta\n\n"
                "Para adivinar, simplemente escribe un número de 4 cifras.\n"
                "Para rendirte, escribe `!rendirse`."
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Jugador: {ctx.author.name} | Intento 0/7")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rendirse')
    async def surrender(self, ctx):
        """Rendirse en el juego actual"""
        user_id = ctx.author.id
        
        if user_id not in self.active_games:
            await ctx.send("❌ No tienes un juego activo.")
            return
        
        secret_number = self.active_games[user_id]["number"]
        del self.active_games[user_id]
        
        await ctx.send(f"😔 Te has rendido. El número secreto era: **{secret_number}**")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignorar mensajes del bot
        if message.author.bot:
            return
        
        user_id = message.author.id
        
        # Verificar si el usuario tiene un juego activo
        if user_id in self.active_games:
            # Verificar si el mensaje es un intento de adivinar
            content = message.content.strip()
            
            # Verificar si es un número de 4 dígitos
            if content.isdigit() and len(content) == 4:
                await self.process_guess(message, content)
        await self.bot.process_commands(message)
    
    async def process_guess(self, message, guess):
        """Procesa un intento de adivinar el número"""
        user_id = message.author.id
        game = self.active_games[user_id]
        secret_number = game["number"]
        
        # Incrementar intentos
        game["attempts"] += 1
        attempts = game["attempts"]
        game["guesses"].append(guess)
        
        # Evaluar intento
        famas, toques = self.evaluate_guess(secret_number, guess)
        
        # Preparar mensaje de respuesta
        embed = discord.Embed(
            title=f"Intento #{attempts}: {guess}",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Famas", value=f"**{famas}**", inline=True)
        embed.add_field(name="Toques", value=f"**{toques}**", inline=True)
        
        # Mostrar intentos previos
        if len(game["guesses"]) > 1:
            history = "\n".join([
                f"#{i+1}: {g} → Famas: {self.evaluate_guess(secret_number, g)[0]}, Toques: {self.evaluate_guess(secret_number, g)[1]}"
                for i, g in enumerate(game["guesses"][:-1])
            ])
            embed.add_field(name="Intentos anteriores", value=f"```\n{history}\n```", inline=False)
        
        embed.set_footer(text=f"Jugador: {message.author.name} | Intento {attempts}/7")
        
        # Victoria
        if famas == 4:
            embed.title = f"🎉 ¡VICTORIA! El número era {secret_number}"
            embed.description = f"¡Felicidades! Has adivinado el número secreto en {attempts} intentos."
            embed.color = discord.Color.green()
            del self.active_games[user_id]
        
        # Derrota
        elif attempts >= 7:
            embed.title = f"😞 DERROTA - El número era {secret_number}"
            embed.description = "Has agotado tus 7 intentos sin adivinar el número."
            embed.color = discord.Color.red()
            del self.active_games[user_id]
            
        await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FamaToque(bot))