import click
from ..execution import ActionDispatcher
from .action import Action
from langchain_core.pydantic_v1 import BaseModel, Field

#########################
# Logging Action


class LoggingInput(BaseModel):
    message: str = Field(description="The message to print")


def create_logging_action():
    def log(state, args: LoggingInput):
        print(f"LOG: {args.message}", flush=True)
        return "Logged message"

    action = Action(
        id="print-message",
        description="Print a message to the console. There is no other way to communicate to the user than through printing with this action.",
        model_cls=LoggingInput,
        f=log,
    )
    return action
