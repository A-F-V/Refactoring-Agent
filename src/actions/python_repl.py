from langchain.agents import Tool,tool
from langchain_experimental.utilities import PythonREPL

@tool
def PythonReplTool(code:str):
    """
    A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.
    """
    python_repl = PythonREPL()
    return python_repl.run(code)