from action import ActionDispatcher, ProjectContextualisedAction
from pydantic import BaseModel, Field

#########################
# Logging Action


class LoggingInput(BaseModel):
    message: str = Field(description="The message to log")


def create_logging_action():
    def log(context, args):
        print(args.message)
        return "Logged message"

    action = ProjectContextualisedAction(
        id="log", description="Log a message", model_cls=LoggingInput, f=log
    )
    return action
