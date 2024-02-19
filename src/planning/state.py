from ast import Tuple

from typing import List, TypedDict
from src.common.definitions import (
    ActionRequest,
    CodeSnippet,
    FeedbackMessage,
    ProjectContext,
    feedback_to_str,
    record_to_str,
    request_to_str,
)
from src.common.definitions import ActionRecord
from src.utilities.formatting import format_list


class RefactoringAgentState(TypedDict):
    goal: str
    project_context: ProjectContext
    history: List[ActionRecord]
    plan: List[ActionRequest]
    # TODO: Feedback of failed actions
    feedback: List[FeedbackMessage]
    console: List[str]
    code_snippets: List[CodeSnippet]


def state_to_str(state: RefactoringAgentState) -> str:
    history = map(record_to_str, state["history"])
    plan = map(request_to_str, state["plan"])
    feedback = map(feedback_to_str, state["feedback"])

    plan_str = format_list(plan, "P", "Plan")
    history_str = format_list(history, "H", "History")
    feedback_str = format_list(feedback, "F", "Feedback")
    console_str = format_list(state["console"], "C", "Console")
    code_str = format_list(state["code_snippets"], "S", "Code Snippets")
    return f"""Goal:
{state['goal']}
History
{history_str}
Plan
{plan_str}
Feedback
{feedback_str}
Console
{console_str}
Code
{code_str}
"""
