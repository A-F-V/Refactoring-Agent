from typing import Type, Optional

from .project_context import ProjectContext

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
import jedi
import os

######################################
# JEDI Utils
def get_definition_for_name(file_path, start_line,end_line):
    # Load the file
    with open(file_path, "r") as file:
        code = file.readlines()
        #    Get the code
        return "\n".join(code[start_line:end_line])

    
###########################################
# Tools
class SearchInput(BaseModel):
    query: str = Field(description="should be a search query for jedi")
    file_path: str = Field(description="should be a file path")


def create_script_search_tool(project_context: ProjectContext):
    def search(query:str, file_path:str):
        # folder path / file path
        path = os.path.join(project_context["folder_path"], file_path)
        script = jedi.Script(path=path)
        completions =  list(script.complete_search(query))
        print(completions)
        result = []
        for completion in completions:
            signatures = completion.get_signatures()
            start = completion.get_definition_start_position()
            end = completion.get_definition_end_position()
            body = get_definition_for_name(path,start[0],end[0])
            info = {
                "name": completion.name,
                "type": completion.type,
                "signatures": [sig.description for sig in signatures],
                "body": body,
            }
            result.append(str(info))
            
            

        return "\n".join(result)

    return StructuredTool.from_function(
        func=search,
        name="script-search",
        description="Search a file for symbols using jedi. Returns the definition of the symbol.",
        args_schema=SearchInput,
    )

               




# Create a search toolkita

class CodeSearchToolkit:
    def __init__(self,context:ProjectContext) -> None:
        self.context = context
        
    def get_tools(self):
        return [create_script_search_tool(self.context)]