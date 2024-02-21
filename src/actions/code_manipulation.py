from typing import Optional, List

from numpy import diff
from regex import E
from src.actions.action import Action
from src.common import Symbol
from src.common.definitions import (
    CodeChange,
    CodeSnippet,
    CodeSpan,
    Definition,
    pydantic_to_str,
)

from src.planning.state import RefactoringAgentState
from src.utilities.jedi_utils import (
    goto_symbol,
    jedi_name_to_symbol,
    span_to_snippet,
    symbol_to_definition,
)
from src.utilities.paths import (
    add_path_to_prefix,
    remove_path_prefix,
    standardize_code_path,
)
from ..common import ProjectContext, Symbol

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import tool

import jedi
import os
import pygit2 as git

###########################################
# Tools


def apply_change_to_file(context: ProjectContext, change: CodeChange):
    # Load the file
    path = add_path_to_prefix(context.folder_path, change.file)
    with open(path, "r") as file:
        code = file.readlines()

    # Apply the change
    start = change.start_line - 1
    end = change.end_line - 1  # File index to 0  index
    replacement_code = change.replacement_code.split("\n")
    replacement_code = [f"{line}\n" for line in replacement_code]
    code[start:end] = replacement_code

    # Write the change
    with open(path, "w") as file:
        file.write("".join(code))

    return "Change applied"


def apply_change_to_snippets(change: CodeChange, span: CodeSpan):
    # If snippet is in a different file, return
    diff_len = len(change.replacement_code.split("\n"))
    if change.replacement_code == "":
        diff_len = 0
    change_in_lines = diff_len - (change.end_line - change.start_line)
    s_path = standardize_code_path(span.file_path)
    c_path = standardize_code_path(change.file)
    if s_path != c_path:
        return

    # if change is below span, nothing to do
    if span.end_line < change.start_line:
        return

    # if the change is wholly within the span, update the span
    if span.start_line <= change.start_line and span.end_line > change.end_line:
        # Move the end line by the difference in lines
        span.end_line += change_in_lines
        assert span.end_line >= span.start_line
        return


class CodeChangeInput(BaseModel):
    file: str = Field(description="The file to apply the change to.")
    start_line: int = Field(description="The start line of the change.")
    end_line: int = Field(description="The end line of the change exclusive.")
    replacement_code: str = Field(description="The replacement code to apply.")
    change_summary: str = Field(description="A summary of the change")


def create_apply_change():

    def apply_change(state: RefactoringAgentState, args: CodeChangeInput) -> str:
        change = CodeChange(
            file=args.file,
            start_line=args.start_line,
            end_line=args.end_line,
            replacement_code=args.replacement_code,
        )

        print(pydantic_to_str(args, "ApplyChangeInput"))

        # Apply the change to the file
        apply_change_to_file(state["project_context"], change)
        # Apply the change to the code snippets
        for span in state["code_blocks"]:
            apply_change_to_snippets(change, span)
        return f"Changed applied to {args.file}: {args.change_summary}"

    return Action(
        id="edit_code",
        description="Applies a change to a file. Achieves this by replacing the old code with your replacement code.",
        model_cls=CodeChangeInput,
        f=apply_change,
    )
