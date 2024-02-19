from typing import Type, Optional, List
from src.actions.action import Action

from src.common.definitions import CodeSpan, Symbol
from src.planning.state import RefactoringAgentState
from src.utilities.jedi_utils import jedi_name_to_symbol, load_code, span_to_snippet

from ..common import ProjectContext
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool
from langchain_core.runnables import RunnableBinding
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
import os


class ReadCodeSnippetInput(BaseModel):
    code_span: dict = Field(description="The code span to read")


# TODO: Error handling
def create_code_loader():
    def code_reader(state: RefactoringAgentState, args: ReadCodeSnippetInput) -> str:
        span = CodeSpan(**args.code_span)
        snippet = span_to_snippet(span, state["project_context"])

        state["code_snippets"].append(snippet)
        return f"Loaded code snippet from {span.file_location} at lines {span.start_line} to {span.end_line}"

    return Action(
        id="code_load",
        description="Loads a code span from the project",
        model_cls=ReadCodeSnippetInput,
        f=code_reader,
    )
