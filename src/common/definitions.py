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


class SequentialActionState(TypedDict):
    next_action_id: str
    next_action_args: str
    last_action_result: str
    next_llm_request: str


class ProjectContext(BaseModel):
    """A project context."""

    folder_path: str = Field(description="The folder path of the project")
