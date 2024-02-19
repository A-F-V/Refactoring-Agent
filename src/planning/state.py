from ast import Tuple
from langchain_core.pydantic_v1 import BaseModel, Field

from typing import Generic, List, Optional, TypeVar, TypedDict

from src.common.definitions import (
    CodeSnippet,
    FailureReason,
    ProjectContext,
)
from src.utilities.formatting import format_list

ActionArgs = TypeVar("ActionArgs", bound=BaseModel)
ActionReturnType = TypeVar("ActionReturnType")


class ActionRequest(TypedDict, Generic[ActionArgs]):
    id: str
    args: ActionArgs


class FeedbackMessage(Exception, Generic[ActionArgs]):
    def __init__(
        self,
        failure_reason: FailureReason,
        message: str,
        request: Optional[ActionRequest[ActionArgs]] = None,
    ):
        self.reason = failure_reason
        self.message = message
        self.request = request
        super().__init__(message)


class ActionRecord(TypedDict, Generic[ActionArgs, ActionReturnType]):
    request: ActionRequest[ActionArgs]
    result: ActionReturnType


def request_to_str(request: ActionRequest) -> str:
    return f"{{\"name\":{request['id']},\"parameters\":{request['args']}}}"


def record_to_str(record: ActionRecord) -> str:
    # Get the name of the type of record.result
    type_name = record["result"].__class__.__name__
    # check if request.result is a derived class of BaseModel
    result_str = f"{type_name}({record['result']})"

    return f"{{\"request\":{request_to_str(record['request'])},\"result\":\"{result_str}\"}}"


def feedback_to_str(feedback: FeedbackMessage) -> str:
    return f'{{"failure-reason":{feedback.reason.value},"message":{feedback.message},"request":{request_to_str(feedback.request) if feedback.request else "none"}}}'


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
<Ultimate Goal>
'{state["goal"]}'
---
<Execution History and Observations (Oldest to Newest)>
{history_str}
---
<Plan>
{plan_str}
---
<Feedback>
{feedback_str}
---
<Console>
{console_str}
---
<Code Snippets>
{code_str}
"""
