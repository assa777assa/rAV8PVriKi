import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import os

client = commands.Bot(command_prefix='!', intents=nextcord.Intents.all())

@client.event
async def on_ready():
    print("Bot is ready")

ServerID = 1351958328087154748


initial_extension = []

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        initial_extension.append('cogs.' + filename[:-3])

if __name__ == '__main__':
    for extension in initial_extension:
        client.load_extension(extension)
        print(f'Loaded {extension}')


