import json
import stat
from typing import Optional, List
from src.actions.action import Action
from src.common.definitions import pydantic_to_str

from src.planning.state import RefactoringAgentState
from src.utilities.paths import remove_path_prefix
from ..common import ProjectContext, Symbol

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import tool

import jedi
import os


###########################################
# Tools


class SearchInput(BaseModel):
    query: str = Field(description="a symbol to search for in repository.")
    fuzzy: bool = Field(description="whether to use fuzzy search", default=False)
    file_path: Optional[str] = Field(
        description="whether to narrow the search to a specific file. If not provided, search the entire repository.",
        default=None,
    )


def create_code_search():
    def parse_completion_to_symbol(completion, context: ProjectContext) -> Symbol:
        (line, column) = completion.line, completion.column
        path = remove_path_prefix(completion.module_path, context.folder_path)
        result = Symbol(
            name=str(completion.name),
            file_location=str(path),
            line=int(line),
            column=int(column),
        )
        return result

    def code_search(state: RefactoringAgentState, args: SearchInput) -> str:
        folder_path = state["project_context"].folder_path
        query = args.query
        fuzzy = args.fuzzy
        file_path = args.file_path

        # searcher
        if file_path is None:
            # folder path
            searcher = jedi.Project(folder_path)
        else:
            # folder path / file path
            path = os.path.join(folder_path, file_path)
            searcher = jedi.Script(path=path)

        completions = list(searcher.complete_search(query, fuzzy=fuzzy))
        output = [
            parse_completion_to_symbol(completion, state["project_context"])
            for completion in completions
        ]
        # Todo: make the path relative to the project
        output = "\n".join(map(pydantic_to_str, output))
        return output

    return Action(
        id="code_search",
        description="Performs a search for a symbol in a file or folder.",
        model_cls=SearchInput,
        f=code_search,
    )
