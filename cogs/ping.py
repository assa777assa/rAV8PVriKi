import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed, ButtonStyle

class pingCommand(commands.Cog):
    def __init__(self, client):
        self.client = client

    ServerID = 1351958328087154748

    @nextcord.slash_command(name="ping", description="ping bot", guild_ids=[ServerID])
    async def ping(self, interaction: Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Brak uprawnień", ephemeral=True)
            return
        await interaction.response.send_message(f'Pong! {round(self.client.latency * 1000)}ms')

def setup(client):
    client.add_cog(pingCommand(client))