from enum import Enum
from pydantic import BaseModel, Field
from typing import TypedDict


###########################################
# Action Defs
class Symbol(BaseModel):
    name: str = Field(description="The name of the symbol")
    file_location: str = Field(description="The file location of the symbol")
    line: int = Field(description="The line number of the symbol")
    column: int = Field(description="The column number of the symbol")


def parse_completion_to_symbol(completion) -> Symbol:
    (line, column) = completion.get_definition_start_position()
    # end = completion.get_definition_end_position()
    result = Symbol(
        name=str(completion.name),
        file_location=str(completion.module_path),
        line=int(line),
        column=int(column),
    )
    return result


##########################################
# State Defs


class ProjectContext(BaseModel):
    """A project context."""

    folder_path: str = Field(description="The folder path of the project")


class ActionSuccess(Enum):
    SUCCESS = "SUCCESS"
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    ACTION_FAILED = "ACTION_FAILED"


class ActionRequest(TypedDict):
    id: str
    action_str: str


def request_to_str(request: ActionRequest) -> str:
    return f"{{\"name\":{request['id']},\"parameters\":{request['action_str']}}}"


class ActionRecord(TypedDict):
    request: ActionRequest
    result: str


# Don't need Success?
def record_to_str(record: ActionRecord) -> str:
    return f"{{\"request\":{request_to_str(record['request'])},\"result\":{record['result']}}}"


class FailureReason(Enum):
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    INVALID_ACTION_ARGS = "INVALID_ACTION_ARGS"
    ACTION_FAILED = "ACTION_FAILED"
    EMPTY_PLAN = "EMPTY_PLAN"


# Make FeedbackMessage an Exception
class FeedbackMessage(Exception):
    def __init__(self, failure_reason: FailureReason, message: str):
        self.reason = failure_reason
        self.message = message
        super().__init__(message)


def feedback_to_str(feedback: FeedbackMessage) -> str:
    return f'{{"failure-reason":{feedback.reason.value},"message":{feedback.message}}}'
