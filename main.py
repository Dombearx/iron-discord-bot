import os
from enum import Enum

import discord
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.chat_models import ChatOpenAI
from langchain.tools.render import format_tool_to_openai_function
from loguru import logger
from dotenv import load_dotenv

from src.openai_backend import ChatBotTemplate
from src.tools import GetDataFromChannelTool
import datetime


from typing import Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import pytz

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


class OpenAIChatBot(ChatBotTemplate):
    def __init__(self, model_name: str, temperature: float = 0.7):
        main_llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        super().__init__(
            main_llm,
            tools=[
                GetDataFromChannelTool(client=client),
            ],
            format_function=format_to_openai_functions,
            tool_format_function=format_tool_to_openai_function,
        )


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

class Trigger(Enum):
    MENTION = 1
    RESPONSE = 2
    THREAD = 3
    DM_MESSAGE = 4
def should_respond(message) -> Optional[Trigger]:
    if message.reference:
        if message.reference.cached_message:
            if message.reference.cached_message.author == client.user:
                return Trigger.RESPONSE
    if client.user in message.mentions:
        return Trigger.MENTION
    if message.channel.type == discord.ChannelType.public_thread:
        return Trigger.THREAD
    if message.channel.type == discord.ChannelType.private:
        return Trigger.DM_MESSAGE
    return None

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channels = {}
    users = {}
    trigger = should_respond(message)
    if trigger:
        human_message = message.content
        logger.debug(f"Processing: {human_message}")

        if message.channel_mentions:
            for channel in message.channel_mentions:
                channels[channel.name] = channel.id
        for user in message.mentions:
            if user != client.user:
                users[user.display_name] = user.id

        channel_history = await GetDataFromChannelTool.get_channel_history(message.channel, n_days=1)

        complete_message = (
            f"Your id is {client.user.id}\n"
            f"Mentioned channels: {channels}\n"
            f"Mentioned users: {users}\n"
            f"{channel_history}"
        )
        if trigger != Trigger.THREAD:
            complete_message = complete_message.rstrip()
            complete_message = "\n".join(complete_message.split("\n")[:-1])

        async with message.channel.typing():
            response = await chatbot.achat(human_message, chat_history=complete_message.split("\n"))
            if response.strip().endswith("END") or response.strip().endswith("END."):
                return
            await message.channel.send(response)


if __name__ == "__main__":
    load_dotenv()
    model_name = "gpt-3.5-turbo"
    chatbot = OpenAIChatBot(model_name)
    client.run(os.environ["DISCORD_TOKEN"])
