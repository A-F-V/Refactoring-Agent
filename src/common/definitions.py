from enum import Enum
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Optional, TypedDict


def pydantic_to_str(request: BaseModel, name: str) -> str:
    # get name of type
    return f"{{'{name}':{request.dict()}}}"


class ProjectContext(BaseModel):
    """A project context."""

    folder_path: str = Field(description="The folder path of the project")
    eval_project_id: str = Field(description="The project id")


###########################################
# Action Defs
class Symbol(BaseModel):
    name: str = Field(description="The name of the symbol")
    file_path: str = Field(description="The file path of the symbol")
    line: int = Field(description="The line number of the symbol")
    column: int = Field(description="The column number of the symbol")


class CodeSpan(BaseModel):
    file_path: str = Field(description="The file location of the span")
    start_line: int = Field(description="The starting line number of the span")
    end_line: int = Field(description="The ending line number of the span")


class Definition(BaseModel):
    symbol: Symbol = Field(description="The symbol of the definition")
    span: CodeSpan = Field(description="The span of the definition")


class CodeChange(BaseModel):
    file: str = Field(description="The file to apply the change to.")
    start_line: int = Field(description="The start line of the change.")
    end_line: int = Field(description="The end line of the change exclusive.")
    replacement_code: str = Field(description="The replacement code to apply.")


##########################################
# State Defs


class ActionSuccess(Enum):
    SUCCESS = "SUCCESS"
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    ACTION_FAILED = "ACTION_FAILED"


# can we just store the parsed action str?
# Don't need Success?
class FailureReason(Enum):
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    INVALID_ACTION_ARGS = "INVALID_ACTION_ARGS"
    ACTION_FAILED = "ACTION_FAILED"
    EMPTY_PLAN = "EMPTY_PLAN"


# Make FeedbackMessage an Exception
class CodeSnippet(TypedDict):
    file_path: str
    code: str
    starting_line: int


def snippet_to_str(snippet: CodeSnippet) -> str:
    return f"""<{snippet['file_path']}/line {snippet['starting_line']}>\n{snippet['code']}"""
