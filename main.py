import os
import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands

client = commands.Bot(intents=nextcord.Intents.default())

for f in os.listdir("./cogs"):
    if f.endswith(".py"):
        client.load_extension(f"cogs.{f[:-3]}")

@client.event
async def on_ready():
    print(f"Логин как {client.user.name} ({client.user.id})") # type: ignore

load_dotenv()
client.run(os.environ["BOT_TOKEN"])
