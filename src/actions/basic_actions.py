import click
from ..execution import ActionDispatcher
from .action import Action
from langchain_core.pydantic_v1 import BaseModel, Field

#########################
# Logging Action


class LoggingInput(BaseModel):
    message: str = Field(description="The message to log")


def create_logging_action():
    def log(state, args: LoggingInput):
        print(args, flush=True)
        return "Logged message"

    action = Action(
        id="log-message",
        description="Log a message to the console. ",
        model_cls=LoggingInput,
        f=log,
    )
    return action
