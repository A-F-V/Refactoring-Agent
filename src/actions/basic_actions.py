import click

from src.planning.state import RefactoringAgentState
from ..execution import ActionDispatcher
from .action import Action
from langchain_core.pydantic_v1 import BaseModel, Field

#########################
# Logging Action


class LoggingInput(BaseModel):
    message: str = Field(description="The message to print")


def create_logging_action():
    def log(state: RefactoringAgentState, args: LoggingInput):
        msg = args.message
        print(f"LOG: {msg}", flush=True)
        state["console"].append(msg)
        return f"Logged '{msg}'"

    action = Action(
        id="print_message",
        description="Print a message to the dedicated `Console`",
        model_cls=LoggingInput,
        f=log,
    )
    return action


class DoNothing(BaseModel):
    pass


def create_no_op_action(id: str, description: str, result="No operation performed"):
    def no_op(state: RefactoringAgentState, args: DoNothing):
        return result

    action = Action(
        id=id,
        description=description,
        model_cls=DoNothing,
        f=no_op,
    )
    return action
