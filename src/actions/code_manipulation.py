from typing import Optional, List

from numpy import diff
from src.actions.action import Action
from src.common import Symbol
from src.common.definitions import Definition, pydantic_to_str

from src.planning.state import RefactoringAgentState
from src.utilities.jedi_utils import (
    goto_symbol,
    jedi_name_to_symbol,
    span_to_snippet,
    symbol_to_definition,
)
from src.utilities.paths import add_path_to_prefix, remove_path_prefix
from ..common import ProjectContext, Symbol

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import tool

import jedi
import os


###########################################
# Tools
example_diff = """
    -Hello, world!
    +Hello, universe!
    This is an example
    -of a unified diff format.
    +of the unified diff format."""


class ApplyChangeInput(BaseModel):
    file: str = Field(description="The file to apply the change to.")
    hunk_header: str = Field(description="The hunk header.")
    diff: str = Field(description=f"The diff to apply. An example is {example_diff}")


def create_apply_change():

    def apply_change(state: RefactoringAgentState, args: ApplyChangeInput) -> str:
        diff_obj = f"""--- {args.file}
+++ {args.file}
{args.hunk_header}
{args.diff}
"""
        print(diff_obj)
        # Invalidate the code snippets
        return diff_obj

    return Action(
        id="apply_code_change",
        description="Applies a change to a file.",
        model_cls=ApplyChangeInput,
        f=apply_change,
    )
