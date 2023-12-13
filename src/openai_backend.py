from typing import Callable, Optional

from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.chat_models.base import BaseChatModel
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import Runnable
from langchain.tools import BaseTool


def identity_function(x):
    return x


class ChatBotTemplate:
    def __init__(
        self,
        main_llm: BaseChatModel,
        tools: Optional[list[BaseTool]] = None,
        format_function: Callable = identity_function,
        tool_format_function: Callable = identity_function,
    ):
        self.tools = tools
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "Your name is Klyde, you are a bot on discord server. "
                        "Your goal is to help server users. "
                        "Be friendly and helpful."
                    ),
                ),
                ("user", "{human_message}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        if tools:
            main_llm = self.bind_tools(
                main_llm, tools=tools, format_function=tool_format_function
            )

        self.agent = (
            {
                "human_message": lambda x: x["human_message"],
                "agent_scratchpad": lambda x: format_function(x["intermediate_steps"]),
            }
            | prompt
            | main_llm
            | OpenAIFunctionsAgentOutputParser()
        )

    def chat(self, human_message: str):
        agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
        output = agent_executor.invoke({"human_message": human_message})

        return output["output"]

    async def achat(self, human_message: str):
        agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
        output = await agent_executor.ainvoke({"human_message": human_message})

        return output["output"]

    def bind_tools(
        self,
        llm: BaseChatModel,
        tools: Optional[list[BaseTool]],
        format_function: Callable,
    ) -> Runnable:
        return llm.bind(functions=[format_function(tool) for tool in tools])
