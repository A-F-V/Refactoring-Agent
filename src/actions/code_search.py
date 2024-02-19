import json
import stat
from typing import Optional, List
from src.actions.action import Action

from src.planning.state import RefactoringAgentState
from ..common import ProjectContext, Symbol, parse_completion_to_symbol

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

        print(completions)
        output = [parse_completion_to_symbol(completion) for completion in completions]
        # Todo: make the path relative to the project
        output = "\n".join(map(str, output))
        print(output)
        return output

    return Action(
        id="code_search",
        description="Performs a search for a symbol in a file or folder.",
        model_cls=SearchInput,
        f=code_search,
    )
