import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import logging

logger = logging.getLogger('discord_bot.rubius')

class RubiusVideos(commands.Cog):
    """Comandos relacionados con El Rubius"""
    
    def __init__(self, bot):
        self.bot = bot
        self.rubius_channel_url = "https://www.youtube.com/@elrubius/videos"
        self.ytdl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': True,
            'ignoreerrors': True,
        }
    
    @commands.command(name='rubiusnew')
    async def rubius_new(self, ctx):
        """Muestra los últimos 10 videos del Rubius Z"""
        async with ctx.typing():
            try:
                # Informar al usuario que estamos procesando su solicitud
                await ctx.send("🔍 Buscando los últimos videos de El Rubius Z... Esto puede tardar unos segundos.")
                
                # Obtener datos del canal usando yt-dlp
                with youtube_dl.YoutubeDL(self.ytdl_opts) as ytdl:
                    info = ytdl.extract_info(self.rubius_channel_url, download=False)
                    
                    if 'entries' not in info:
                        await ctx.send("❌ No se pudo obtener información del canal.")
                        return
                    
                    # Tomar solo los 5 primeros videos (los más recientes)
                    latest_videos = info['entries'][:5]
                    
                    if not latest_videos:
                        await ctx.send("❌ No se encontraron videos recientes.")
                        return
                    
                    # Crear un embed principal con información del canal
                    embed = discord.Embed(
                        title="📺 Últimos videos de El Rubius Z",
                        color=discord.Color.red(),
                        url=self.rubius_channel_url
                    )
                    
                    # Añadir miniatura del canal en el embed principal
                    if 'thumbnails' in info and info['thumbnails']:
                        embed.set_thumbnail(url=info['thumbnails'][0]['url'])
                    
                    # Enviar embed principal
                    await ctx.send(embed=embed)
                    
                    # Enviar un embed para cada video
                    for i, video in enumerate(latest_videos, 1):
                        title = video.get('title', 'Sin título')
                        video_url = f"https://www.youtube.com/watch?v={video['id']}"
                        
                        # Crear embed individual para cada video
                        video_embed = discord.Embed(
                            title=f"{i}. {title}",
                            url=video_url,
                            color=discord.Color.red()
                        )
                        
                        # Añadir miniatura si está disponible
                        if 'thumbnails' in video and video['thumbnails']:
                            # Elegir la miniatura de mejor calidad disponible
                            thumbnail_url = video['thumbnails'][-1]['url']
                            video_embed.set_image(url=thumbnail_url)
                        
                        await ctx.send(embed=video_embed)
            
            except Exception as e:
                logger.error(f"Error al obtener videos del Rubius: {str(e)}")
                await ctx.send(f"❌ Error al obtener videos: {str(e)}")

async def setup(bot):
    await bot.add_cog(RubiusVideos(bot))