from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from src.actions.code_search import create_code_search
from src.planning.planner import DecisionMaker, Planner
from src.planning.state import RefactoringAgentState
from .common.definitions import ProjectContext
from .execution import ActionDispatcher, ExecuteTopOfPlan, LLMController
from .actions.basic_actions import create_logging_action


class RefactoringAgent:
    def __init__(self):
        # Load Actions
        self._setup_agent_graph()

    @staticmethod
    def _should_continue(state: RefactoringAgentState):
        return False

    def _initial_state(self, state: RefactoringAgentState):
        print("State Initialized")

    def _create_refactoring_actions(self):
        action_list = ActionDispatcher()
        action_list.register_action(create_logging_action())
        action_list.register_action(create_code_search())
        return action_list.get_action_list()

    def _setup_agent_graph(self):

        action_list = self._create_refactoring_actions()

        self.graph = StateGraph(RefactoringAgentState)

        self.graph.add_node("planner", Planner(action_list))
        self.graph.add_node("execute", ExecuteTopOfPlan(action_list))
        self.graph.add_conditional_edges("planner", DecisionMaker())
        self.graph.add_conditional_edges("execute", DecisionMaker())
        self.graph.set_entry_point("planner")
        # self.graph.add_node('')
        self.app = self.graph.compile()

    def run(self, input: str, context: ProjectContext) -> RefactoringAgentState:
        state: RefactoringAgentState = {
            "goal": input,
            "project_context": context,
            "history": [],
            "plan": [],
            "feedback": [],
        }
        return RefactoringAgentState(**self.app.invoke(state))
