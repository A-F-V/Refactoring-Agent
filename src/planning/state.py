from ast import Tuple
from langchain_core.pydantic_v1 import BaseModel, Field

from typing import Generic, List, Optional, TypeVar, TypedDict

from src.common.definitions import (
    CodeSnippet,
    CodeSpan,
    FailureReason,
    ProjectContext,
    snippet_to_str,
)
from src.utilities.formatting import format_list
from src.utilities.jedi_utils import span_to_snippet

ActionArgs = TypeVar("ActionArgs", bound=BaseModel)
ActionReturnType = TypeVar("ActionReturnType")

RED = "\033[91m"
RESET = "\033[0m"
GREEN = "\033[92m"


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

    return f"{{\"name\":{RED}{request['id']}{RESET},\"parameters\":{request['args']}}}"


def record_to_str(record: ActionRecord) -> str:
    # Get the name of the type of record.result
    type_name = record["result"].__class__.__name__
    # check if request.result is a derived class of BaseModel
    # if type_name is str or int, then result_str is the value of record.result
    if type_name == "str" or type_name == "int":
        result_str = record["result"]
    else:
        result_str = f"{type_name}({record['result']})"

    return f"{{\"request\":{request_to_str(record['request'])},\"result\":{GREEN}\"{result_str}\"{RESET}}}"


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
    code_blocks: List[CodeSpan]
    thoughts: List[str]


def state_to_str(state: RefactoringAgentState) -> str:
    history = map(record_to_str, state["history"])
    plan = map(request_to_str, state["plan"])
    feedback = map(feedback_to_str, state["feedback"])
    snippets = map(
        lambda s: snippet_to_str(span_to_snippet(s, state["project_context"])),
        state["code_blocks"],
    )

    # plan_str = format_list(plan, "P", "Plan")
    # console_str = format_list(state["console"], "C", "Console")
    history_str = format_list(history, "H", "History")
    feedback_str = format_list(feedback, "F", "Feedback")
    thoughts_str = format_list(state["thoughts"], "T", "Thoughts")
    code_str = format_list(snippets, "CODE-BLOCK-", "Code Snippets")
    return f"""### Main Goal ###
'{state["goal"]}'
---
### Execution History and Observations (Oldest to Newest) ###
{history_str}
---
### Thoughts (Oldest to Newest) ###
{thoughts_str}
---
### Feedback ###
{feedback_str}
---
### Code Snippets ###
{code_str}
"""
