from typing import Type, Optional, List
from src.actions.action import Action
from src.common.definitions import Definition, pydantic_to_str

from src.planning.state import RefactoringAgentState
from src.utilities.paths import add_path_to_prefix
from ..common import ProjectContext, Symbol

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain_core.runnables import RunnableBinding
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
import jedi
import os


######################################
# JEDI Utils
def get_definition_for_name(defining_name, context: ProjectContext):
    # Load the file
    path = defining_name.module_path

    (start, _) = defining_name.get_definition_start_position()
    (end, _) = defining_name.get_definition_end_position()
    with open(path, "r") as file:
        code = file.readlines()
        #    Get the code
        return "\n".join(code[start - 1 : end + 1])


###########################################
# Tools


class GetDefinitionInput(BaseModel):
    symbol: dict = Field(description="The symbol to get the defintion for")


def create_definition_getter():
    def code_get_defintion(
        state: RefactoringAgentState, args: GetDefinitionInput
    ) -> str:
        folder_path = state["project_context"].folder_path
        symbol = Symbol(**args.symbol)

        script = jedi.Script(path=add_path_to_prefix(folder_path, symbol.file_location))
        # TODO: Add more error handling
        cursor = script.goto(symbol.line, symbol.column)
        definition = cursor[0].goto()[0]
        definition_body = get_definition_for_name(definition, state["project_context"])

        def_obj = Definition(symbol=symbol, code=definition_body)
        return pydantic_to_str(def_obj)

    return Action(
        id="code_get_definition",
        description="Get the definition of a symbol in the project",
        model_cls=GetDefinitionInput,
        f=code_get_defintion,
    )
