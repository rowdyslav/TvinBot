import os
import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands

client = commands.Bot(intents=nextcord.Intents.default())
load_dotenv()
TOKEN = os.environ["BOT_TOKEN"]

for f in os.listdir("./cogs"):
    if f.endswith(".py"):
        client.load_extension(f"cogs.{f[:-3]}")


@client.event
async def on_ready():
    print(f"Логин как {client.user.name} ({client.user.id})")  # type: ignore


client.run(TOKEN)
