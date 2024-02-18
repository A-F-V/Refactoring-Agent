from enum import Enum
import json
import sys
from tabnanny import verbose
from typing import Dict, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.utils.function_calling import convert_to_openai_function
from src.actions.action import Action
from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.output_parsers.openai_tools import JsonOutputToolsParser
from langchain_core.output_parsers import JsonOutputParser
from src.common.definitions import SequentialActionState
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent


class ActionSuccess(Enum):
    SUCCESS = "SUCCESS"
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    ACTION_FAILED = "ACTION_FAILED"


class ActionRecord(TypedDict):
    id: str
    success: ActionSuccess
    action_str: str
    observation: str


class ActionDispatcher:
    """
    A class that manages the registration and dispatching of actions.
    """

    def __init__(self):
        self.actions: Dict[str, Action] = {}

    def register_action(self, action: Action):
        """
        Registers an action with the dispatcher.

        Args:
            action (Action): The action to register.
        """
        self.actions[action.id] = action

    def get_action_list(self):
        """
        Returns a list of all registered actions.

        Returns:
            list: A list of Action objects.
        """
        return list(self.actions.values())

    def dispatch(self, state: SequentialActionState) -> ActionRecord:
        """
        Dispatches an action based on its ID.

        Args:
            id (str): The ID of the action to dispatch.
            action_str (str): The action string to execute.
            **kwargs: Additional keyword arguments to pass to the action's execute method.

        Returns:
            ActionRecord: The result of the action execution.
        """
        id = state["next_action_id"]
        action_str = state["next_action_args"]
        action = self.actions.get(id)
        if action:
            try:
                observation = action.execute(state)
                return ActionRecord(
                    id=id,
                    success=ActionSuccess.SUCCESS,
                    action_str=action_str,
                    observation=observation,
                )
            except Exception as e:
                return ActionRecord(
                    id=id,
                    success=ActionSuccess.ACTION_FAILED,
                    action_str=action_str,
                    observation=str(e),
                )
        else:
            return ActionRecord(
                id=id,
                success=ActionSuccess.ACTION_NOT_FOUND,
                action_str=action_str,
                observation="",
            )


# Given a prompt, the LLMControler will dispatch a suitable action


class LLMController:
    def __init__(self, dispatcher: ActionDispatcher):
        self.dispatcher = dispatcher
        self.create_prompt()
        self.llm = ChatOpenAI(model="gpt-4-turbo-preview")
        self.parser = JsonOutputToolsParser()
        # self.chain = self.prompt_template | self.llm | self.parser

    def create_prompt(self):
        prompt = hub.pull("hwchase17/openai-tools-agent")
        self.prompt_template = prompt

    def get_openai_tools(self, state):
        tools = map(lambda x: x.to_tool(state), self.dispatcher.get_action_list())
        # open_ai_tools = map(convert_to_openai_function, tools)
        return list(tools)

    def run(self, state: SequentialActionState):
        tools = self.get_openai_tools(state)

        # Construct the OpenAI Tools agent
        agent = create_openai_tools_agent(self.llm, tools, self.prompt_template)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        # Decide what to do

        output = agent_executor.invoke({"input": state["next_llm_request"]})
        # print(output)

    def __call__(self, state):
        self.run(state)
