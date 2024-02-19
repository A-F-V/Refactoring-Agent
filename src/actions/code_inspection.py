from typing import Type, Optional, List

from src.common.definitions import Symbol

from ..common import ProjectContext

from langchain.tools import BaseTool, StructuredTool
from langchain_core.runnables import RunnableBinding
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
import os


######################################
# JEDI Utils
def get_body_of_symbol(symbol: Symbol, context: ProjectContext):
    # Load the file
    path = symbol.module_path

    (start, _) = symbol.get_definition_start_position()
    (end, _) = symbol.get_definition_end_position()
    with open(path, "r") as file:
        code = file.readlines()
        #    Get the code
        return "\n".join(code[start - 1 : end + 1])


###########################################
# Tools
