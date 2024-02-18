from typing import Type, Optional, List
from ..common import ProjectContext, Symbol, parse_completion_to_symbol

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
def get_definition_for_name(file_path, start_line, end_line):
    # Load the file
    with open(file_path, "r") as file:
        code = file.readlines()
        #    Get the code
        return "\n".join(code[start_line:end_line])


###########################################
# Tools
