import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed
from cogs.Ticket import TicketButtonView, CloseTicketView
import json

#load json data
def load_dropdown_data():
    filename = "dropdown_data.json"
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)

#hex to int
def hex_to_int(hex_color):
    return int(hex_color.lstrip("#"), 16)

def format_embed_text(text):
    if isinstance(text, list):  
        return "\n".join(text) 
    return str(text)

class EmbedButtonView(nextcord.ui.View):
    def __init__(self, product_name=None):
        super().__init__()
        self.product_name = product_name

    @nextcord.ui.button(label="Utwórz Ticket", style=nextcord.ButtonStyle.primary)
    async def button_click(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await TicketButtonView.create_ticket(interaction, {"name": self.product_name} if self.product_name else None)

class SubDropdown(nextcord.ui.Select):
    def __init__(self, subcategories, messages, embed_settings, deeper_subcategories=None):
        self.messages = messages
        self.embed_settings = embed_settings
        self.deeper_subcategories = deeper_subcategories or {}

        select_options = [nextcord.SelectOption(label=opt, description=f"{opt}") for opt in subcategories]
        super().__init__(placeholder="Wybierz opcje:", min_values=1, max_values=1, options=select_options)

    async def callback(self, interaction: Interaction):
        selected_option = self.values[0]

        if self.deeper_subcategories and selected_option in self.deeper_subcategories:
            deeper_data = self.deeper_subcategories[selected_option]
            sub_options = deeper_data["options"]
            sub_messages = deeper_data["messages"]

            view = SubDropdownView(sub_options, sub_messages, self.embed_settings, deeper_data.get("subcategories", {}))
            await interaction.response.send_message("Wybierz kategorie", view=view, ephemeral=True)
            return

        if selected_option not in self.messages:
            await interaction.response.send_message("brak danych", ephemeral=True)
            return

        option_data = self.messages[selected_option]
        embed_color = hex_to_int(self.embed_settings.get("color", "#ff73fa"))
        embed_title = f"{option_data.get('icon', '')} {option_data.get('title', '')}".strip()

        embed = Embed(
            title=embed_title if embed_title else None,
            description=option_data["description"],
            color=embed_color
        )
        embed.set_footer(text=self.embed_settings.get("footer", ""))

        for field in option_data.get("fields", []):
            embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field.get("inline", False)
            )

        view = EmbedButtonView(selected_option)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class SubDropdownView(nextcord.ui.View):
    def __init__(self, subcategories, messages, embed_settings, deeper_subcategories=None):
        super().__init__()
        self.add_item(SubDropdown(subcategories, messages, embed_settings, deeper_subcategories))



class Dropdown(nextcord.ui.Select):
    def __init__(self, options, messages, subcategories, embed_settings):
        self.messages = messages
        self.subcategories = subcategories
        self.embed_settings = embed_settings

        if not options:
            options = ["Info"]
            self.messages["Info"] = {
                "icon": "ℹ️",
                "title": "",
                "description": "",
                "fields": []
            }

        select_options = []
        for option in options:
            if option in self.messages:
                emoji_str = self.messages[option].get("icon", None)
                option_data = nextcord.SelectOption(label=option)
                if emoji_str and emoji_str.startswith("<") and emoji_str.endswith(">"):
                    option_data.emoji = emoji_str
                elif emoji_str:
                    try:
                        option_data.emoji = emoji_str
                    except:
                        pass
                select_options.append(option_data)

        super().__init__(
            placeholder="Wybierz opcję",
            min_values=1,
            max_values=1,
            options=select_options
        )

    async def callback(self, interaction: Interaction):
        selected_option = self.values[0]

        if self.subcategories and "options" in self.subcategories and selected_option in self.subcategories["options"]:
            subcategory_data = self.subcategories["messages"].get(selected_option)
            if subcategory_data:
                sub_options = subcategory_data["options"]
                sub_messages = subcategory_data["messages"]
                deeper_subcategories = subcategory_data.get("subcategories", {})

                view = SubDropdownView(sub_options, sub_messages, self.embed_settings, deeper_subcategories)
                await interaction.response.send_message("Wybierz kategorie", view=view, ephemeral=True)
                return

        if selected_option not in self.messages:
            await interaction.response.send_message("brak danych", ephemeral=True)
            return

        option_data = self.messages[selected_option]
        embed_color = hex_to_int(self.embed_settings.get("color", "#ff73fa"))
        embed_title = f"{option_data.get('icon', '')} {option_data.get('title', '')}".strip()

        embed = Embed(
            title=embed_title if embed_title else None,
            description=option_data["description"],
            color=embed_color
        )
        embed.set_footer(text=self.embed_settings.get("footer", ""))

        for field in option_data.get("fields", []):
            embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field.get("inline", False)
            )

        view = EmbedButtonView(selected_option)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class DropdownView(nextcord.ui.View):
    def __init__(self, options, messages, subcategories, embed_settings):
        super().__init__()
        self.add_item(Dropdown(options, messages, subcategories, embed_settings))


class UI(commands.Cog):
    def __init__(self, client):
        self.client = client

    ServerID = 1351958328087154748

    @nextcord.slash_command(name="dropdown", description="Select Option", guild_ids=[ServerID])
    async def drop(self, interaction: Interaction,
                   dropdown_type: str = SlashOption(
                       name="type",
                       description="choose category",
                       required=True,
                       choices=["nitro", "boostgodzin", "socialboost", "members", "konta"]
                   )):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Brak uprawnień", ephemeral=True)
            return

        try:
            dropdown_data = load_dropdown_data()
        except FileNotFoundError:
            await interaction.response.send_message("error", ephemeral=True)
            return

        if dropdown_type not in dropdown_data:
            await interaction.response.send_message("error", ephemeral=True)
            return

        category_data = dropdown_data[dropdown_type]
        text = category_data["text"]
        options = category_data["options"]
        messages = category_data["messages"]
        embed_settings = category_data.get("embed", {})
        subcategories = category_data.get("subcategories", {})

        embed_color = hex_to_int(embed_settings.get("color", "#ff73fa"))
        embed_title = embed_settings.get("title", "Wybierz kategorię")

        embed = Embed(title=embed_title, description=format_embed_text(text), color=embed_color)
        embed.set_footer(text=embed_settings.get("footer", ""))

        for field in embed_settings.get("fields", []):
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False)
            )

        if "image" in embed_settings:
            embed.set_image(url=embed_settings["image"])
        if "thumbnail" in embed_settings:
            embed.set_thumbnail(url=embed_settings["thumbnail"])

        if dropdown_type == "boostgodzin":
            view = EmbedButtonView("boostgodzin")
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
            return

        view = DropdownView(options, messages, subcategories, embed_settings)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)


def setup(client):
    client.add_cog(UI(client))
