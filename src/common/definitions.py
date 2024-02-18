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


class ActionRecord(TypedDict):
    request: ActionRequest
    success: ActionSuccess
    observation: str
