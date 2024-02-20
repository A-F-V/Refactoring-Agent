import json
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.utils.function_calling import convert_to_openai_function

from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.output_parsers.openai_tools import JsonOutputToolsParser
from langchain_core.output_parsers import JsonOutputParser
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from src.actions.action import Action
from src.common.definitions import (
    ActionSuccess,
    FailureReason,
)

from src.planning.state import (
    ActionRecord,
    ActionRequest,
    FeedbackMessage,
    RefactoringAgentState,
    state_to_str,
)
from src.utilities.formatting import format_list


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

    def dispatch(
        self, state: RefactoringAgentState, request: ActionRequest
    ) -> ActionRecord:
        """
        Dispatches an action based on its ID.

        Args:
            id (str): The ID of the action to dispatch.
            action_str (str): The action string to execute.
            **kwargs: Additional keyword arguments to pass to the action's execute method.

        Returns:
            ActionRecord: The result of the action execution.
        """
        id = request["id"]
        args = request["args"]
        action = self.actions.get(id)
        if action:
            try:
                observation = action.execute(state, args)
                return ActionRecord(
                    request=request,
                    result=observation,
                )
            except Exception as e:
                raise FeedbackMessage(
                    FailureReason.ACTION_FAILED, str(e), request=request
                )
        else:
            raise FeedbackMessage(
                FailureReason.ACTION_NOT_FOUND,
                f"Action {id} not found",
                request=request,
            )


class ExecuteTopOfPlan:
    def __init__(self, action_list: List[Action]):
        self.dispatcher = ActionDispatcher()
        for action in action_list:
            self.dispatcher.register_action(action)

    def __call__(self, state: RefactoringAgentState):
        # Check if there is an action at the top of the plan
        plan = state["plan"]
        try:
            if len(plan) == 0:
                raise FeedbackMessage(FailureReason.EMPTY_PLAN, "Plan is empty")
            action = plan[0]
            # Remove the action from the plan
            state["plan"] = plan[1:]
            # Dispatch the action
            record = self.dispatcher.dispatch(state, action)
            # Save the result
            state["history"].append(record)
        except FeedbackMessage as f:
            state["feedback"].append(f)
        return state


class ExecutePlan:
    def __init__(self, action_list: List[Action]) -> None:
        self.executor = ExecuteTopOfPlan(action_list)

    def __call__(self, state: RefactoringAgentState):
        while len(state["plan"]) > 0:
            state = self.executor(state)
        return state


# Given a prompt, the LLMControler will dispatch a suitable action


class LLMController:
    def __init__(
        self,
        actions: List[Action],
        current_task: str,
        verbose=True,
        number_of_actions=1,
    ):
        self.actions = actions
        self.llm = ChatOpenAI(model="gpt-4-1106-preview")
        self.parser = JsonOutputToolsParser()
        self.current_task = current_task
        self.number_of_actions = number_of_actions
        self.create_prompt()
        self.verbose = verbose
        # self.chain = self.prompt_template | self.llm | self.parser

    def create_prompt(self):
        # For execution
        prompt = hub.pull("hwchase17/openai-tools-agent")
        self.agent_prompt = prompt
        # For Context
        # TODO: Evaluate this part
        message = f"""
<Current Task>
'{self.current_task}'
---
{{state}}
---
Now invoke suitable functions to complete the Current Task. 
Arguments for the functions should be constructed from the context provided, including from the output of past actions.
Do not send other messages other than invoking functions.
Invoke no more than {self.number_of_actions} function calls to complete the task.
"""
        self.context_prompt = PromptTemplate.from_template(message)

    def format_context_prompt(self, state: RefactoringAgentState) -> str:
        message_sent = self.context_prompt.format(state=state_to_str(state))
        if self.verbose:
            print(message_sent)
            pass
        return message_sent

    def get_openai_tools(self, state):
        tools = map(lambda x: x.to_tool(state), self.actions)
        # open_ai_tools = map(convert_to_openai_function, tools)
        return list(tools)

    def run(self, state: RefactoringAgentState):
        tools = self.get_openai_tools(state)

        # Construct the OpenAI Tools agent
        agent = create_openai_tools_agent(self.llm, tools, self.agent_prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=self.verbose)
        # Decide what to do
        if self.verbose:
            # print("Action List:")
            # print("\n".join([str(action) for action in self.actions]))
            # print("----")
            pass
        output = ""
        try:
            try:
                result = agent_executor.invoke(
                    {"input": self.format_context_prompt(state)}
                )
                output = result["output"]
            except Exception as e:
                raise FeedbackMessage(FailureReason.ACTION_FAILED, str(e))
        except FeedbackMessage as f:
            state["feedback"].append(f)
        finally:
            return state, output

    def __call__(self, state: RefactoringAgentState):
        state, output = self.run(state)
        return state
