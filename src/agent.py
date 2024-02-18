from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from src.planning.memory import History
from .actions import PythonReplTool, CodeSearchToolkit
from .common.definitions import ProjectContext
from .actions.action import ActionDispatcher
from .actions.basic_actions import create_logging_action
from typing import TypedDict


class RefactoringAgentState(TypedDict):
    history: History


class RefactoringAgent:
    def __init__(self, context: ProjectContext):
        self.context = context
        # Load Actions
        self.dispatcher = ActionDispatcher()
        self.dispatcher.register_action(create_logging_action())
        
        self._setup_agent_graph()

    @staticmethod
    def _should_continue(state: RefactoringAgentState):
        return False
    
    def _setup_agent_graph(self):
        self.graph = StateGraph(RefactoringAgentState)
        
        self.llm = ChatOpenAI(model="gpt-4-turbo-preview")
        
        #self.graph.add_node('')
        self.app = self.graph.compile()
        
    def run(self,input:str)
        return self.app.invoke(input)
