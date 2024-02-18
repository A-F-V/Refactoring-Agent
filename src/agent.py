from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from src.planning.memory import History
from .actions import PythonReplTool, CodeSearchToolkit
from .common.definitions import ProjectContext, SequentialActionState
from .execution import ActionDispatcher, LLMController
from .actions.basic_actions import create_logging_action
from typing import TypedDict
from langchain.prompts import PromptTemplate, HumanMessagePromptTemplate


class RefactoringAgentState(SequentialActionState):
    user_task: str
    project_context: ProjectContext
    history: History


def create_simple_controller():
    dispatcher = ActionDispatcher()
    dispatcher.register_action(create_logging_action())

    return LLMController(dispatcher)


class RefactoringAgent:
    def __init__(self):
        # Load Actions
        self._setup_agent_graph()

    @staticmethod
    def _should_continue(state: RefactoringAgentState):
        return False

    def _initial_state(self, state: RefactoringAgentState):
        print("State Initialized")
        return {"next_llm_request": state["user_task"]}

    def _setup_agent_graph(self):
        self.graph = StateGraph(RefactoringAgentState)

        self.graph.add_node("entry", self._initial_state)
        self.graph.add_node("llm-controller", create_simple_controller())
        self.graph.add_edge("entry", "llm-controller")
        self.graph.add_edge("llm-controller", END)
        self.graph.set_entry_point("entry")
        # self.graph.add_node('')
        self.app = self.graph.compile()

    def run(self, input: str, context: ProjectContext):
        request = {
            "user_task": input,
            "project_context": context,
            "history": History(actions_observations=[]),
        }
        return self.app.invoke(request)
