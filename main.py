import os
import discord
from loguru import logger
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channels = []
    users = []
    if client.user in message.mentions:
        human_order = message.content.replace(f"<@{client.user.id}> ", "")
        logger.debug(f"Processing: {human_order}")

        if message.channel_mentions:
            for channel in message.channel_mentions:
                pass


        async with message.channel.typing():
            response = "placeholder"
            await message.channel.send(response)


if __name__ == "__main__":
    load_dotenv()
    client.run(os.environ["DISCORD_TOKEN"])
