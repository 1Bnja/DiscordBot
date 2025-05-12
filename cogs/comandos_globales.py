import discord
from discord.ext import commands

class GlobalCommands(commands.Cog):
    @commands.command(name="limpiartodo", aliases=["clearall", "purgeall"])
    @commands.has_permissions(manage_messages=True)
    async def limpiartodo(self, ctx):
        """Elimina TODOS los mensajes del canal actual."""
        await ctx.send("🧹 Borrando todos los mensajes...", delete_after=2)
        deleted = await ctx.channel.purge()
        await ctx.send(f"🧹 Se han borrado {len(deleted)} mensajes.", delete_after=3)
    
    @commands.command()
    async def ping(self, ctx):
        """Muestra la latencia del bot."""
        await ctx.send(f'🏓 Pong! Latencia: {round(self.bot.latency * 1000)}ms')

    @commands.command()
    async def serverinfo(self, ctx):
        """Muestra información del servidor."""
        guild = ctx.guild
        embed = discord.Embed(title=f"Servidor: {guild.name}", color=discord.Color.green())
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Miembros", value=guild.member_count)
        embed.add_field(name="Dueño", value=guild.owner)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GlobalCommands(bot))