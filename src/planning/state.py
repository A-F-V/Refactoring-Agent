from ast import Tuple
from typing import List, TypedDict
from src.common.definitions import ActionRequest, ProjectContext
from src.common.definitions import ActionRecord


class RefactoringAgentState(TypedDict):
    goal: str
    project_context: ProjectContext
    history: List[ActionRecord]
    plan: List[ActionRequest]
