from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from src.actions.code_inspection import create_code_loader
from src.actions.code_manipulation import create_apply_change
from src.actions.code_search import create_definition_gotoer
from src.actions.code_search import create_code_search
from src.planning.planner import LLMExecutor, ShouldContinue, Planner, Thinker
from src.planning.state import RefactoringAgentState
from .common.definitions import ProjectContext
from .execution import ActionDispatcher, ExecutePlan, ExecuteTopOfPlan, LLMController
from .actions.basic_actions import create_logging_action
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig


class RefactoringAgent:
    def __init__(self):
        # Load Actions
        self._setup_agent_graph()

    def _create_refactoring_actions(self):
        action_list = ActionDispatcher()
        # Code Querying & Manipulation
        action_list.register_action(create_code_search())
        action_list.register_action(create_apply_change())
        # action_list.register_action(create_definition_gotoer())
        # action_list.register_action(create_code_loader())
        # Git

        return action_list.get_action_list()

    def _setup_agent_graph(self):

        action_list = self._create_refactoring_actions()
        self.graph = StateGraph(RefactoringAgentState)

        self.graph.add_node("think", Thinker())  # Planner(action_list))
        self.graph.add_node("execute", LLMExecutor(action_list))
        self.graph.add_node(
            "finish",
            LLMController(
                [create_logging_action()],
                "Log any results you wish to show the user by calling print_message.",
            ),
        )
        self.graph.add_edge("think", "execute")
        self.graph.add_conditional_edges("execute", ShouldContinue())
        self.graph.add_edge("finish", END)
        self.graph.set_entry_point("think")
        # self.graph.add_node('')
        self.app = self.graph.compile()

    def run(self, inp: str, context: ProjectContext) -> RefactoringAgentState:
        state: RefactoringAgentState = {
            "goal": inp,
            "project_context": context,
            "history": [],
            "plan": [],
            "feedback": [],
            "console": [],
            "code_blocks": [],
            "thoughts": [],
        }
        config = RunnableConfig(recursion_limit=10)
        return RefactoringAgentState(**self.app.invoke(state, config=config))
