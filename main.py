import discord
from discord.ext import commands
import os
import logging
import ssl
import certifi
import os

ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())
# Importar los módulos de cogs

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_PREFIX = os.environ.get("DISCORD_PREFIX", "!") 

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

# Crear instancia del bot con intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=DISCORD_PREFIX, intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Bot conectado como {bot.user.name}')
    
    # Cargar todos los cogs (módulos)
    try:
        # Mostrar directorio actual para debugging
        current_dir = os.getcwd()
        logger.info(f"Directorio actual: {current_dir}")
        
        # Cargar el módulo music_player
        await bot.load_extension('cogs.music_player')
        logger.info('Módulo cargado: music_player')
        
        # Cargar el nuevo módulo para videos del Rubius
        await bot.load_extension('cogs.rubius_videos')
        logger.info('Módulo cargado: rubius_videos')

        await bot.load_extension('cogs.fama_toque')
        logger.info('Módulo cargado: fama_toque')

        await bot.load_extension('cogs.book_search')
        logger.info('Módulo cargado: book_search')

        await bot.load_extension('cogs.comandos_globales')
        logger.info('Módulo cargado: global_commands')

    except Exception as e:
        logger.error(f'Error al cargar módulos: {str(e)}')

    logger.info('¡Bot listo!')

# Iniciar el bot
if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)