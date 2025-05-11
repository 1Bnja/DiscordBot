import discord
from discord.ext import commands
import asyncio
import yt_dlp as youtube_dl 
import logging
import os
import platform

logger = logging.getLogger('discord_bot.music')

def get_ffmpeg_path():
    # Si estamos en Render (ambiente de producción)
    if os.environ.get('RENDER'):
        logger.info("Ejecutando en Render - usando ffmpeg del sistema")
        return 'ffmpeg'  # En Render, ffmpeg estará en el PATH
    
    # Si estamos en Windows (desarrollo local)
    if platform.system() == 'Windows':
        local_path = r'C:\ffmpeg\bin\ffmpeg.exe' # Reemplaza con tu ruta actual
        logger.info(f"Ejecutando en Windows - usando ffmpeg local: {local_path}")
        return local_path
    
    # Fallback para otros sistemas
    logger.info("Ejecutando en otro sistema - usando ffmpeg del sistema")
    return 'ffmpeg'

# Configuración de youtube-dl
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio[ext=m4a]/bestaudio/best',
    'outtmpl': 'temp/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
    'executable': get_ffmpeg_path(),
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, filename, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.filename = filename  
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.webpage_url = data.get('webpage_url')
        self.uploader = data.get('uploader')
        self.original = source

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))

        if 'entries' in data:
            data = data['entries'][0]

        filename = ytdl.prepare_filename(data)

        # El error está aquí - falta pasar filename como parámetro
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, filename=filename)




class MusicPlayer(commands.Cog):
    """Reproductor de música para Discord"""
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}  # {guild_id: [tracks]}
        self.now_playing = {}  # {guild_id: track}
        self.play_next_song = {}  # {guild_id: asyncio.Event}
        self.audio_players = {}  # {guild_id: player}
        
    def get_queue(self, guild_id):
        """Obtener la cola para un servidor específico"""
        if guild_id not in self.queue:
            self.queue[guild_id] = []
        return self.queue[guild_id]
            
    @commands.command(name='join', aliases=['connect'])
    async def join(self, ctx):
        """Unirse al canal de voz"""
        if not ctx.author.voice:
            await ctx.send("❌ Debes estar en un canal de voz para usar este comando.")
            return False
            
        channel = ctx.author.voice.channel
        
        if ctx.voice_client:
            if ctx.voice_client.channel.id == channel.id:
                return True
            await ctx.voice_client.move_to(channel)
        else:
            try:
                await channel.connect()
                self.play_next_song[ctx.guild.id] = asyncio.Event()
                await ctx.send(f"👋 Me he unido a {channel.mention}")
            except Exception as e:
                logger.error(f"Error al unirse al canal de voz: {e}")
                await ctx.send("❌ No pude unirme al canal de voz.")
                return False
        
        return True
            
    @commands.command(name='leave', aliases=['disconnect'])
    async def leave(self, ctx):
        """Salir del canal de voz"""
        if not ctx.voice_client:
            await ctx.send("❌ No estoy en un canal de voz.")
            return
            
        guild_id = ctx.guild.id
        
        # Limpiar cola y ahora reproduciendo
        if guild_id in self.queue:
            self.queue[guild_id] = []
        if guild_id in self.now_playing:
            del self.now_playing[guild_id]
        if guild_id in self.audio_players:
            del self.audio_players[guild_id]
            
        await ctx.voice_client.disconnect()
        await ctx.send("👋 He salido del canal de voz.")
        
    async def play_next(self, ctx):
        """Reproduce la siguiente canción en la cola"""
        guild_id = ctx.guild.id
        voice_client = ctx.voice_client
        
        if not voice_client:
            return
            
        if not self.get_queue(guild_id):
            if guild_id in self.now_playing:
                del self.now_playing[guild_id]
            return
            
        # Obtener la siguiente canción
        song_url = self.queue[guild_id].pop(0)
        
        try:
            async with ctx.typing():
                player = await YTDLSource.from_url(song_url, loop=self.bot.loop)

                self.now_playing[guild_id] = player
                
                def after_playing(error):
                    if error:
                        logger.error(f"Error en la reproducción: {error}")
                    
                    # Eliminar archivo descargado
                    try:
                        os.remove(player.filename)
                        logger.info(f"🗑️ Archivo eliminado: {player.filename}")
                    except Exception as e:
                        logger.warning(f"No se pudo eliminar el archivo: {e}")
                    
                    # Continuar con la siguiente canción
                    coro = self.play_next(ctx)
                    fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

                    
                voice_client.play(player, after=after_playing)
                embed = discord.Embed(
                    title="🎵 Reproduciendo ahora",
                    description=f"[{player.title}]({player.webpage_url})",
                    color=discord.Color.green()
                )
                
                if player.thumbnail:
                    embed.set_thumbnail(url=player.thumbnail)
                if player.uploader:
                    embed.add_field(name="👤 Subido por", value=player.uploader, inline=True)
                if player.duration:
                    minutes, seconds = divmod(player.duration, 60)
                    embed.add_field(name="⏱️ Duración", value=f"{minutes}:{seconds:02d}", inline=True)
                    
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error al reproducir música: {e}")
            await ctx.send(f"❌ Error al reproducir: {str(e)}")
            
            # Intentar con la siguiente canción
            await self.play_next(ctx)
        
    @commands.command(name='play')
    async def play(self, ctx, *, url):
        """Reproducir música: !play [url/nombre de canción]"""
        # Unirse al canal si no está ya
        if not await self.join(ctx):
            return
            
        guild_id = ctx.guild.id
        voice_client = ctx.voice_client
        
        # Comprobar si es búsqueda en lugar de URL
        if not url.startswith(('https://', 'http://')):
            url = f"ytsearch:{url}"
            
        # Esperar mensaje para indicar que estamos procesando
        async with ctx.typing():
            try:
                # Solo para verificar que la URL es válida y obtener info
                info = await self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                
                if 'entries' in info:
                    # Es una playlist o resultado de búsqueda
                    url = info['entries'][0]['webpage_url']
                    await ctx.send(f"🔍 Encontrado: **{info['entries'][0]['title']}**")
                else:
                    url = info['webpage_url']
                    
                # Añadir a la cola
                self.get_queue(guild_id).append(url)
                
                if not voice_client.is_playing():
                    await ctx.send("▶️ Comenzando reproducción...")
                    await self.play_next(ctx)
                else:
                    title = info['entries'][0]['title'] if 'entries' in info else info['title']
                    await ctx.send(f"📝 Añadido a la cola: **{title}**")
                    
            except Exception as e:
                logger.error(f"Error al agregar canción: {e}")
                await ctx.send(f"❌ Error al buscar la canción: {str(e)}")
            
    @commands.command(name='pause')
    async def pause(self, ctx):
        """Pausar la reproducción actual"""
        voice_client = ctx.voice_client
        if not voice_client or not voice_client.is_playing():
            await ctx.send("❌ No hay nada reproduciéndose actualmente.")
            return
            
        voice_client.pause()
        await ctx.send("⏸️ Reproducción pausada")
        
    @commands.command(name='resume')
    async def resume(self, ctx):
        """Reanudar la reproducción"""
        voice_client = ctx.voice_client
        if not voice_client:
            await ctx.send("❌ No estoy conectado a un canal de voz.")
            return
            
        if voice_client.is_paused():
            voice_client.resume()
            await ctx.send("▶️ Reproducción reanudada")
        else:
            await ctx.send("❌ La reproducción no está pausada.")
            
    @commands.command(name='skip')
    async def skip(self, ctx):
        """Saltar a la siguiente canción en la cola"""
        voice_client = ctx.voice_client
        guild_id = ctx.guild.id
        
        if not voice_client or not voice_client.is_playing():
            await ctx.send("❌ No hay nada reproduciéndose actualmente.")
            return
        
        # Guardar el nombre del archivo antes de detener la reproducción
        current_file = None
        if guild_id in self.now_playing:
            current_file = self.now_playing[guild_id].filename
            logger.info(f"🎵 Saltando canción: {self.now_playing[guild_id].title}")
        
        # Detener la reproducción (esto debería activar la función after_playing)
        voice_client.stop()
        
        # Verificar si el archivo aún existe y eliminarlo manualmente si es necesario
        if current_file and os.path.exists(current_file):
            try:
                os.remove(current_file)
                logger.info(f"🗑️ Archivo eliminado manualmente: {current_file}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar el archivo manualmente: {e}")
        
        await ctx.send("⏭️ Canción saltada")
        
    @commands.command(name='queue', aliases=['q'])
    async def queue_cmd(self, ctx):
        """Mostrar la cola actual"""
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        if not queue and guild_id not in self.now_playing:
            await ctx.send("📝 La cola está vacía.")
            return
            
        embed = discord.Embed(title="🎵 Cola de Reproducción", color=discord.Color.blue())
        
        # Mostrar canción actual
        if guild_id in self.now_playing:
            player = self.now_playing[guild_id]
            embed.add_field(
                name="▶️ Reproduciendo ahora",
                value=f"[{player.title}]({player.webpage_url})",
                inline=False
            )
            
        # Mostrar canciones en cola (URLs)
        if queue:
            # Para cada URL en la cola, intentar obtener información básica
            items_to_display = min(len(queue), 5)  # Limitar a 5 elementos
            queue_text = ""
            
            for i in range(items_to_display):
                try:
                    info = ytdl.extract_info(queue[i], download=False, process=False)
                    title = info.get('title', 'Canción desconocida')
                    queue_text += f"{i+1}. {title}\n"
                except:
                    queue_text += f"{i+1}. [URL no procesada]\n"
            
            if len(queue) > items_to_display:
                queue_text += f"\n... y {len(queue) - items_to_display} más"
                
            embed.add_field(name="📝 Próximas canciones", value=queue_text, inline=False)
        else:
            embed.add_field(name="📝 Próximas canciones", value="No hay canciones en cola", inline=False)
            
        await ctx.send(embed=embed)
        
    @commands.command(name='clear')
    async def clear(self, ctx):
        """Limpiar la cola de reproducción"""
        guild_id = ctx.guild.id
        if guild_id in self.queue:
            self.queue[guild_id] = []
            await ctx.send("🗑️ Cola limpiada")
        else:
            await ctx.send("📝 La cola ya está vacía")
            
    @commands.command(name='now', aliases=['np', 'nowplaying'])
    async def now_playing_cmd(self, ctx):
        """Mostrar la canción que se está reproduciendo actualmente"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.now_playing:
            await ctx.send("❌ No hay nada reproduciéndose actualmente.")
            return
            
        player = self.now_playing[guild_id]
        embed = discord.Embed(
            title="🎵 Reproduciendo ahora",
            description=f"[{player.title}]({player.webpage_url})",
            color=discord.Color.green()
        )
        
        if player.thumbnail:
            embed.set_thumbnail(url=player.thumbnail)
        if player.uploader:
            embed.add_field(name="👤 Subido por", value=player.uploader, inline=True)
        if player.duration:
            minutes, seconds = divmod(player.duration, 60)
            embed.add_field(name="⏱️ Duración", value=f"{minutes}:{seconds:02d}", inline=True)
            
        await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=['vol'])
    async def volume(self, ctx, volume: int = None):
        """Ajustar el volumen (0-150)"""
        if not ctx.voice_client:
            await ctx.send("❌ No estoy conectado a un canal de voz.")
            return
            
        if volume is None:
            vol = int(ctx.voice_client.source.volume * 100) if ctx.voice_client.source else 0
            await ctx.send(f"🔊 Volumen actual: **{vol}%**")
            return
            
        # Limitar volumen entre 0 y 150%
        volume = max(0, min(150, volume))
        
        if ctx.voice_client.source:
            ctx.voice_client.source.volume = volume / 100.0
            await ctx.send(f"🔊 Volumen ajustado a **{volume}%**")

async def setup(bot):
    await bot.add_cog(MusicPlayer(bot))