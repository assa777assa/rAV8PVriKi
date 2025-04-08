import nextcord
from nextcord.ext import commands
from nextcord import Interaction
from keep_alive import keep_alive
from cogs.Ticket import TicketButtonView, CloseTicketView
from cogs.UI import DropdownView, SubDropdownView
import json
import os

keep_alive()

client = commands.Bot(command_prefix='!', intents=nextcord.Intents.all())


@client.event
async def on_ready():
    print("Bot is ready")
    # Add persistent views
    client.add_view(TicketButtonView())
    client.add_view(CloseTicketView(None))
    
    # Load dropdown data
    try:
        print("Attempting to load dropdown_data.json...")
        with open("dropdown_data.json", "r", encoding="utf-8") as file:
            dropdown_data = json.load(file)
            print("Successfully loaded dropdown_data.json")
            
        # Register dropdown views for each type
        for category_type, data in dropdown_data.items():
            options = data["options"]
            messages = data["messages"]
            embed_settings = data.get("embed", {})
            subcategories = data.get("subcategories", {})
            
            # Register main dropdown view
            client.add_view(DropdownView(options, messages, subcategories, embed_settings))
            
            # Register views for subcategories if they exist
            if subcategories and "options" in subcategories:
                for subcat in subcategories["options"]:
                    subcat_data = subcategories["messages"].get(subcat, {})
                    if subcat_data and "options" in subcat_data:
                        sub_options = subcat_data["options"]
                        sub_messages = subcat_data["messages"]
                        client.add_view(SubDropdownView(sub_options, sub_messages, embed_settings))
    except Exception as e:
        print(f"Error loading dropdown views: {e}")
        
    print("Persistent views loaded")


ServerID = 1351958328087154748

initial_extension = []

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        initial_extension.append('cogs.' + filename[:-3])

if __name__ == '__main__':
    for extension in initial_extension:
        client.load_extension(extension)
        print(f'Loaded {extension}')

client.run(os.environ['TOKEN'])