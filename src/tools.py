import datetime


from typing import Optional, Type

import discord
import pytz
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class GetDataFromChannelSchema(BaseModel):
    channel_id: int = Field(description="should be a channel id")
    n_days: Optional[int] = Field(
        description="should be a number of last days to get messages from. Use only if you don't know how many messages you want to get"
    )
    n_messages: Optional[int] = Field(
        description="should be a number of messages to get or None if n_days is not None"
    )


class GetDataFromChannelTool(BaseTool):
    client: discord.Client
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
        channel = self.client.get_channel(channel_id)
        if not channel:
            return "Channel not found"
        return await self.get_channel_history(channel, n_days, n_messages)

    @staticmethod
    async def get_channel_history(channel, n_days: Optional[int] = None, n_messages: Optional[int] = None):
        MAX_CHARACTERS = 2000
        messages = []
        if channel.type == discord.ChannelType.public_thread:
            messages = [message async for message in channel.history()]
        elif n_days:
            day_ago = datetime.datetime.now() - datetime.timedelta(days=n_days)
            messages = [message async for message in channel.history(after=day_ago)]
        elif n_messages:
            messages = [message async for message in channel.history(limit=n_messages)]

        channel_history = ""
        for old_message in messages:
            created_at = old_message.created_at.astimezone(pytz.timezone("Europe/Warsaw"))
            channel_history += (
                    created_at.strftime('%Y-%m-%d %H:%M')
                    + f" {old_message.author.display_name}: "
            )
            channel_history += old_message.content
            channel_history += "\n"
        channel_history = channel_history[:MAX_CHARACTERS]

        return channel_history
