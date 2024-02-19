import json
import stat
from typing import Optional, List
from src.actions.action import Action
from src.actions.code_inspection import get_body_of_symbol
from src.common import Symbol
from src.common.definitions import Definition, pydantic_to_str

from src.planning.state import RefactoringAgentState
from src.utilities.jedi_utils import goto_symbol, jedi_name_to_symbol
from src.utilities.paths import add_path_to_prefix, remove_path_prefix
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
            jedi_name_to_symbol(completion, state["project_context"])
            for completion in completions
        ]
        output = "\n".join(map(pydantic_to_str, output))
        return output

    return Action(
        id="code_search",
        description="Performs a search for a symbol in a file or folder.",
        model_cls=SearchInput,
        f=code_search,
    )


class GotoDefinitionInput(BaseModel):
    symbol: dict = Field(description="The symbol to get the definition of.")


# TODO: Error handling
def create_definition_gotoer():
    def code_goto_definition(
        state: RefactoringAgentState, args: GotoDefinitionInput
    ) -> str:
        symbol = Symbol(**args.symbol)

        source_name = goto_symbol(state["project_context"], symbol)

        assert len(source_name._name) == 1

        definition_name = source_name[0].goto()

        assert len(definition_name) == 1

        definition_symbol = jedi_name_to_symbol(
            definition_name[0], state["project_context"]
        )

        return pydantic_to_str(definition_symbol)

    return Action(
        id="code_goto_definition",
        description="Goes the definition of a symbol in the project",
        model_cls=GotoDefinitionInput,
        f=code_goto_definition,
    )
