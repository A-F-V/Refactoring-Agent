from typing import Optional, List
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


def create_code_search(context: ProjectContext):
    @tool("code-symbol-search", args_schema=SearchInput)
    def code_search(
        query: str,
        fuzzy: bool = False,
        file_path: Optional[str] = None,
    ) -> List[Symbol]:
        """
        Performs a search for a symbol in a file or folder.
        """
        # searcher
        if file_path is None:
            # folder path
            searcher = jedi.Project(context.folder_path)
        else:
            # folder path / file path
            path = os.path.join(context.folder_path, file_path)
            searcher = jedi.Script(path=path)

        completions = list(searcher.complete_search(query, fuzzy=fuzzy))

        print(completions)
        return [parse_completion_to_symbol(completion) for completion in completions]

    return code_search


# Create a search toolkita


class CodeSearchToolkit:

    def __init__(self, context: ProjectContext):
        self.context = context

    def get_tools(self):
        return [create_code_search(self.context)]
