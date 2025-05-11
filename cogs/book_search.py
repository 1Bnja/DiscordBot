import discord
from discord.ext import commands
import aiohttp
import logging
from urllib.parse import quote

logger = logging.getLogger('discord_bot.books')

class BookSearch(commands.Cog):
    """Comandos para buscar libros en Open Library"""
    
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://openlibrary.org/search.json"
        self.book_url = "https://openlibrary.org/works/"
    
    @commands.command(name='libro')
    async def search_book(self, ctx, *, query):
        """Busca un libro en Open Library por título"""
        if not query:
            await ctx.send("❌ Por favor, especifica un título para buscar.")
            return
        
        async with ctx.typing():
            try:
                # Informar al usuario que estamos procesando su solicitud
                message = await ctx.send("🔍 Buscando libros... Esto puede tardar unos segundos.")
                
                # Realizar la búsqueda en Open Library
                async with aiohttp.ClientSession() as session:
                    # Codificar la consulta para URLs
                    encoded_query = quote(query)
                    search_url = f"{self.api_url}?q={encoded_query}&limit=5"
                    
                    async with session.get(search_url) as response:
                        if response.status != 200:
                            await message.edit(content="❌ Error al conectar con Open Library.")
                            return
                        
                        data = await response.json()
                        
                        if not data.get('docs') or data.get('numFound', 0) == 0:
                            await message.edit(content=f"❌ No se encontraron libros con el título: **{query}**")
                            return
                        
                        # Obtener el primer resultado
                        book = data['docs'][0]
                        
                        # Crear un embed con la información del libro
                        embed = discord.Embed(
                            title=book.get('title', 'Título desconocido'),
                            color=discord.Color.blue()
                        )
                        
                        # Añadir autor si está disponible
                        authors = book.get('author_name', ['Autor desconocido'])
                        author_text = ', '.join(authors[:3])
                        if len(authors) > 3:
                            author_text += f" y {len(authors) - 3} más"
                        embed.add_field(name="✍️ Autor", value=author_text, inline=False)
                        
                        # Añadir año de publicación si está disponible
                        if 'first_publish_year' in book:
                            embed.add_field(name="📅 Año de publicación", value=book['first_publish_year'], inline=True)
                        
                        # Añadir idioma si está disponible
                        languages = book.get('language', [])
                        if languages:
                            embed.add_field(name="🌐 Idioma", value=', '.join(languages[:3]), inline=True)
                        
                        # Añadir enlace a Open Library
                        if 'key' in book:
                            # Extraer el ID de la obra de la clave
                            work_id = book['key'].split('/')[-1]
                            book_link = f"https://openlibrary.org{book['key']}"
                            embed.url = book_link
                            
                            # Añadir enlace para leer el libro si está disponible
                            read_link = f"https://openlibrary.org/works/{work_id}/check-in"
                            embed.add_field(
                                name="📚 Leer", 
                                value=f"[Ver en Open Library]({book_link}) | [Verificar disponibilidad]({read_link})", 
                                inline=False
                            )
                        
                        # Añadir portada si está disponible
                        if 'cover_i' in book:
                            cover_url = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg"
                            embed.set_thumbnail(url=cover_url)
                        
                        # Si hay más resultados disponibles, mencionarlo
                        if data['numFound'] > 1:
                            remaining = min(data['numFound'] - 1, 4)  # Mostrar hasta 4 resultados más
                            titles = [f"{i+2}. {doc.get('title', 'Título desconocido')}" 
                                     for i, doc in enumerate(data['docs'][1:remaining+1])]
                            
                            if titles:
                                embed.add_field(
                                    name=f"🔍 Otros {remaining} resultados:",
                                    value='\n'.join(titles),
                                    inline=False
                                )
                        
                        # Añadir footer con información sobre la búsqueda
                        embed.set_footer(text=f"Búsqueda: {query} | Resultados totales: {data['numFound']}")
                        
                        await message.edit(content=None, embed=embed)
                        
            except Exception as e:
                logger.error(f"Error al buscar libros: {str(e)}")
                await ctx.send(f"❌ Error al buscar el libro: {str(e)}")

async def setup(bot):
    # Asegurarse de que aiohttp está instalado
    try:
        import aiohttp
        await bot.add_cog(BookSearch(bot))
    except ImportError:
        logger.error("Se requiere aiohttp para el módulo de búsqueda de libros")
        print("Error: Se requiere la librería aiohttp. Instálala con 'pip install aiohttp'")