import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed, ButtonStyle
from nextcord.ui import View, Button
import json
import re

def load_ticket_data():
    with open("ticket_data.json", "r", encoding="utf-8") as file:
        return json.load(file)
    

ticket_data = load_ticket_data()

class TicketButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @staticmethod
    async def create_ticket(interaction: Interaction, product_info=None):
        guild = interaction.guild
        user = interaction.user

        existing_channel = nextcord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(f"Masz już otwarty ticket: {existing_channel.mention}", ephemeral=True)
            return

        trial_seller_role = nextcord.utils.get(guild.roles, name="Trail seller")
        seller_role = nextcord.utils.get(guild.roles, name="seller")

        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
            user: nextcord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: nextcord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_permissions=True)
        }

        if trial_seller_role:
            overwrites[trial_seller_role] = nextcord.PermissionOverwrite(view_channel=True, send_messages=True)
        if seller_role:
            overwrites[seller_role] = nextcord.PermissionOverwrite(view_channel=True, send_messages=True)

        category = nextcord.utils.get(guild.categories, name="tickety")

        try:
            ticket_channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites, category=category)
            await interaction.response.send_message(f"Twój ticket został utworzony: {ticket_channel.mention}", ephemeral=True)

            product_name = product_info.get('name', 'N/A') if product_info else None
            embed = create_embed("ticket_open", user, product_name)
            await ticket_channel.send(content="@everyone", embed=embed, view=CloseTicketView(ticket_channel))

        except nextcord.Forbidden:
            await interaction.response.send_message("Brak uprawnień do tworzenia kanału!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @nextcord.ui.button(label="Otwórz Ticket", style=ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, button: Button, interaction: Interaction):
        await self.create_ticket(interaction)


class CloseTicketView(View):
    def __init__(self, channel):
        super().__init__(timeout=None)  # Make the view persistent
        self.channel = channel

    @nextcord.ui.button(label="❌ Zamknij Ticket", style=ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, button: Button, interaction: Interaction):
        await interaction.response.send_message("Ticket zostanie zamknięty za 5 sekund...", ephemeral=True)
        await nextcord.utils.sleep_until(nextcord.utils.utcnow().replace(second=nextcord.utils.utcnow().second + 5))
        await self.channel.delete()

    @nextcord.ui.button(label="⚙️ Ustawienia Ticketu", style=ButtonStyle.secondary, custom_id="ticket_settings")
    async def ticket_settings(self, button: Button, interaction: Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
            return

        embed = Embed(title="Ustawienia Ticketu", description="", color=0x3498db)
        await interaction.response.send_message(embed=embed, view=TicketSettingsView(self.channel), ephemeral=True)


class TicketSettingsView(View):
    def __init__(self, ticket_channel):
        super().__init__()
        self.ticket_channel = ticket_channel

    @nextcord.ui.button(label="🔔 Powiadom", style=ButtonStyle.primary, custom_id="notify_ticket")
    async def notify_ticket(self, button: Button, interaction: Interaction):
        try:
            ticket_owner = None
            for member in self.ticket_channel.members:
                if not member.bot and not member.guild_permissions.administrator:
                    ticket_owner = member
                    break

            if ticket_owner:
                embed = Embed(
                    title="Powiadomienie dotyczące Twojego ticketa!",
                    description=f"Administrator wysłał powiadomienie w sprawie Twojego ticketu: {self.ticket_channel.mention}.",
                    color=0x3498db
                )
                await ticket_owner.send(embed=embed)
                await interaction.response.send_message("Wysłano powiadomienie do właściciela ticketu!", ephemeral=True)
            else:
                await interaction.response.send_message("Nie znaleziono właściciela ticketu.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Błąd: {e}", ephemeral=True)

    @nextcord.ui.button(label="🔒 Przejmij", style=ButtonStyle.success, custom_id="take_ticket")
    async def take_ticket(self, button: Button, interaction: Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
            return

        try:
            messages = [message async for message in self.ticket_channel.history(limit=1, oldest_first=True)]
            if not messages:
                await interaction.response.send_message("Nie znaleziono informacji o tickecie.", ephemeral=True)
                return

            first_message = messages[0]
            if not first_message.embeds:
                await interaction.response.send_message("Nie znaleziono informacji o tickecie.", ephemeral=True)
                return

            ticket_owner = None
            print("Fields in embed:")
            for field in first_message.embeds[0].fields:
                print(f"Field name: {field.name}")
                print(f"Field value: {field.value}")
                if "𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐂𝐉𝐄 𝐎 𝐊𝐋𝐈𝐄𝐍𝐂𝐈𝐄" in field.name:
                    mention_match = re.search(r'<@(\d+)>', field.value)
                    if mention_match:
                        user_id = int(mention_match.group(1))
                        ticket_owner = await interaction.guild.fetch_member(user_id)
                        break
                    user_id_match = re.search(r'ID:\s*(\d+)', field.value)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        ticket_owner = await interaction.guild.fetch_member(user_id)
                        break

            if not ticket_owner:
                await interaction.response.send_message("Nie znaleziono właściciela ticketu.", ephemeral=True)
                return

            for member in self.ticket_channel.members:
                if member != interaction.guild.me and member != ticket_owner and member != interaction.user:
                    await self.ticket_channel.set_permissions(member, view_channel=False)

            await self.ticket_channel.set_permissions(ticket_owner, view_channel=True, send_messages=True)
            await self.ticket_channel.set_permissions(interaction.user, view_channel=True, send_messages=True)

            embed = Embed(
                title="Ticket Przejęty",
                description=f"🔒 Ten ticket został przejęty przez {interaction.user.mention}.",
                color=0x2ecc71
            )
            await self.ticket_channel.send(embed=embed)
            await interaction.response.send_message("Pomyślnie przejąłeś ticket.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"error: {str(e)}", ephemeral=True)

    @nextcord.ui.button(label="❌ Zamknij Ticket", style=ButtonStyle.danger, custom_id="close_ticket_admin")
    async def close_ticket_admin(self, button: Button, interaction: Interaction):
        await interaction.response.send_message("Ticket zostanie zamknięty za 5 sekund...", ephemeral=True)
        await nextcord.utils.sleep_until(nextcord.utils.utcnow().replace(second=nextcord.utils.utcnow().second + 5))
        await self.ticket_channel.delete()

    @nextcord.ui.button(label="➕ Dodaj Osobę", style=ButtonStyle.success, custom_id="add_user")
    async def add_user(self, button: Button, interaction: Interaction):
        await interaction.response.send_message("Podaj ID użytkownika do dodania:", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=30)
            user = await interaction.guild.fetch_member(int(msg.content))
            await self.ticket_channel.set_permissions(user, view_channel=True, send_messages=True)
            await interaction.followup.send(f"Dodano {user.mention} do ticketu!", ephemeral=True)
        except:
            await interaction.followup.send("Błąd Sprawdź ID użytkownika.", ephemeral=True)

    @nextcord.ui.button(label="➖ Usuń Osobę", style=ButtonStyle.secondary, custom_id="remove_user")
    async def remove_user(self, button: Button, interaction: Interaction):
        await interaction.response.send_message("Podaj ID użytkownika do usunięcia:", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=30)
            user = await interaction.guild.fetch_member(int(msg.content))
            await self.ticket_channel.set_permissions(user, view_channel=False, send_messages=False)
            await interaction.followup.send(f"Usunięto {user.mention} z ticketu!", ephemeral=True)
        except:
            await interaction.followup.send("Błąd Sprawdź ID użytkownika.", ephemeral=True)


def create_embed(embed_key, user, product_name=None):
    embed_data = ticket_data[embed_key]
    embed = nextcord.Embed(
        title=embed_data.get("title", ""),
        description=embed_data.get("description", ""),
        color=int(embed_data.get("color", "#ffffff").lstrip("#"), 16)
    )

    for field in embed_data.get("fields", []):
        if "𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐂𝐉𝐄 𝐎 𝐊𝐋𝐈𝐄𝐍𝐂𝐈𝐄" in field["name"]:
            value = field["value"].format(
                user_mention=user.mention,
                user_name=user.name,
                user_id=user.id
            )
        elif "𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐂𝐉𝐄 𝐎 𝐏𝐑𝐎𝐃𝐔𝐊𝐂𝐈𝐄" in field["name"]:
            value = field["value"].format(
                name=product_name if product_name else "N/A"
            )
        else:
            value = field["value"]

        embed.add_field(
            name=field["name"],
            value=value,
            inline=field.get("inline", False)
        )

    if embed_data.get("footer"):
        embed.set_footer(text=embed_data["footer"])

    if embed_data.get("thumbnail", False) and user.avatar:
        embed.set_thumbnail(url=user.avatar.url)

    return embed


class Ticket(commands.Cog):
    def __init__(self, client):
        self.client = client

    ServerID = 1351929804559093871

    @nextcord.slash_command(name="ticket", description="ticket", guild_ids=[ServerID])
    async def ticket(self, interaction: Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Brak uprawnień", ephemeral=True)
            return
        embed = Embed(title="Tickets", description="Otwórz ticket.", color=0x3498db)
        await interaction.response.send_message(embed=embed, view=TicketButtonView(), ephemeral=True)


def setup(client):
    client.add_cog(Ticket(client))