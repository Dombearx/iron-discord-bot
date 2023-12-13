import os
from enum import Enum

import discord
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.chat_models import ChatOpenAI
from langchain.tools.render import format_tool_to_openai_function
from loguru import logger
from dotenv import load_dotenv

from src.openai_backend import ChatBotTemplate

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

import datetime


from typing import Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import pytz


class GetDataFromChannelSchema(BaseModel):
    channel_id: int = Field(description="should be a channel id")
    n_days: Optional[int] = Field(
        description="should be a number of last days to get messages from. Use only if you don't know how many messages you want to get"
    )
    n_messages: Optional[int] = Field(
        description="should be a number of messages to get or None if n_days is not None"
    )


class GetDataFromChannelTool(BaseTool):
    name: str = "get_data_from_channel"
    description: str = (
        "Allows to get messages from given channel. Either from last n_days or last n_messages."
        "Will never return more than 100 messages. "
        "Tool is async only."
    )
    args_schema: Type[GetDataFromChannelSchema] = GetDataFromChannelSchema

    def _run(
        self,
        channel_id: int,
        n_days: Optional[int] = None,
        n_messages: Optional[int] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> bool:
        """Use the tool."""
        raise NotImplementedError("get_data_from_channel does not support sync")

    async def _arun(
        self,
        channel_id: int,
        n_days: Optional[int] = None,
        n_messages: Optional[int] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        channel = client.get_channel(channel_id)
        messages = []
        if n_days:
            day_ago = datetime.datetime.now() - datetime.timedelta(days=n_days)
            messages = [message async for message in channel.history(after=day_ago)]
        if n_messages:
            messages = [message async for message in channel.history(limit=n_messages)]
        messages = messages[:100]

        channel_history = ""
        for old_message in messages:
            created_at = old_message.created_at.astimezone(pytz.timezone("Europe/Warsaw"))
            channel_history += (
                old_message.author.name
                + " at "
                + created_at.strftime('%Y-%m-%d %H:%M')
                + " said: "
            )
            channel_history += old_message.content
            channel_history += "\n"
        return channel_history


class OpenAIChatBot(ChatBotTemplate):
    def __init__(self, model_name: str, temperature: float = 0.7):
        main_llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        super().__init__(
            main_llm,
            tools=[
                GetDataFromChannelTool(),
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
def should_respond(message) -> Optional[Trigger]:
    if message.reference:
        if message.reference.cached_message:
            if message.reference.cached_message.author == client.user:
                return Trigger.RESPONSE
    if client.user in message.mentions:
        return Trigger.MENTION
    if message.channel.type == discord.ChannelType.public_thread:
        return Trigger.THREAD
    return None

async def get_channel_history(channel):
    history_range = 1

    if channel.type == discord.ChannelType.public_thread:
        history_range = 0

    day_ago = datetime.datetime.now() - datetime.timedelta(days=history_range)
    if not history_range:
        day_ago = None

    channel_history = ""
    async for old_message in channel.history(after=day_ago):
        created_at = old_message.created_at.astimezone(pytz.timezone("Europe/Warsaw"))
        channel_history += (
            old_message.author.name
            + " at "
            + created_at.strftime('%Y-%m-%d %H:%M')
            + " said: "
        )
        channel_history += old_message.content
        channel_history += "\n"
    return channel_history

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

        channel_history = await get_channel_history(message.channel)

        complete_message = (
            f"Your id is {client.user.id}\n"
            f"Mentioned channels: {channels}\n"
            f"Mentioned users: {users}\n"
            f"{channel_history}"
        )
        if trigger == Trigger.THREAD:
            complete_message = complete_message.rstrip()
            complete_message += f" {message.content}"

        async with message.channel.typing():
            # response = "Hello from AWS!"
            response = await chatbot.achat(complete_message)
            await message.channel.send(response)


if __name__ == "__main__":
    load_dotenv()
    model_name = "gpt-3.5-turbo"
    chatbot = OpenAIChatBot(model_name)
    client.run(os.environ["DISCORD_TOKEN"])
