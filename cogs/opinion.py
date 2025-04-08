import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed

class Opinie(commands.Cog):
    def __init__(self, client):
        self.client = client

    ServerID = 1351958328087154748

    @nextcord.slash_command(name="opinia", description="Wystaw opinię o usłudze.", guild_ids=[ServerID])
    async def opinia(
        self,
        interaction: Interaction,
        czas: int = SlashOption(name="czas", description="Oceń czas realizacji (1-5)", min_value=1, max_value=5, required=True),
        przebieg: int = SlashOption(name="przebieg", description="Oceń przebieg współpracy (1-5)", min_value=1, max_value=5, required=True),
        realizacja: int = SlashOption(name="realizacja", description="Oceń jakość realizacji (1-5)", min_value=1, max_value=5, required=True),
        oferta: str = SlashOption(name="typ",description="Wybierz oferte", required=True, choices=["Nitro", "Boost godzin", "Social boost", "Members"]),
        opinia: str = SlashOption(name="opinia", description="Twoja opinia", required=False)
    ):
        suma_ocen = czas + przebieg + realizacja

        if suma_ocen <= 8:
            color = 0xFF0000 
        elif suma_ocen <= 12:
            color = 0xFFA500
        else:
            color = 0x00FF00

        embed = Embed(
            title="𝐍𝐎𝐖𝐀 𝐎𝐏𝐈𝐍𝐈𝐀",
            description=f"**Autor:** {interaction.user.mention}",
            color=color
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        def gwiazdki(ocena):
            return "⭐" * ocena + "☆" * (5 - ocena)
        
        def format_oferta(name):
            return "**" + name + "**"

        embed.add_field(name="Czas realizacji:", value=gwiazdki(czas), inline=False)
        embed.add_field(name="Przebieg współpracy:", value=gwiazdki(przebieg), inline=False)
        embed.add_field(name="Jakość realizacji:", value=gwiazdki(realizacja), inline=False)
        embed.add_field(name="Oferta:", value=format_oferta(oferta), inline=False)

        if opinia:
            embed.add_field(name="Opinia klienta:", value=opinia, inline=False)

        # Find channel that starts with ⭐•opinie
        opinie_channel = None
        for channel in interaction.guild.text_channels:
            if channel.name.startswith("⭐•opinie"):
                opinie_channel = channel
                break
                
        if not opinie_channel:
            category = nextcord.utils.get(interaction.guild.categories, name="TICKETY")
            overwrites = {
                interaction.guild.default_role: nextcord.PermissionOverwrite(view_channel=True, send_messages=False),
                interaction.guild.me: nextcord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            opinie_channel = await interaction.guild.create_text_channel(
                name="⭐•opinie",
                overwrites=overwrites,
                category=category
            )

        await opinie_channel.send(embed=embed)
        await interaction.response.send_message("Dziękujemy za Twoją opinię!", ephemeral=True)

def setup(client):
    client.add_cog(Opinie(client))
