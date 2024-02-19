from ast import Tuple

from typing import List, TypedDict
from src.common.definitions import (
    ActionRequest,
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


def state_to_str(state: RefactoringAgentState) -> str:
    history = map(record_to_str, state["history"])
    plan = map(request_to_str, state["plan"])
    feedback = map(feedback_to_str, state["feedback"])

    plan_str = format_list(plan, "P", "Plan")
    history_str = format_list(history, "H", "History")
    feedback_str = format_list(feedback, "F", "Feedback")
    return f"""
    Goal:
    {state['goal']}
    History
    {history_str}
    Plan
    {plan_str}
    Feedback
    {feedback_str})"""
