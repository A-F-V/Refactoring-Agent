import json
from src.common.definitions import ActionRequest
from src.execution import ActionDispatcher
from src.planning.state import RefactoringAgentState
from ..actions.action import Action
from langchain_core.pydantic_v1 import BaseModel, Field


class ClearPlanInput(BaseModel):
    pass


def create_clear_plan_action():
    def clear_plan(state: RefactoringAgentState, args: ClearPlanInput):
        state["plan"] = []
        return "Cleared plan"

    action = Action(
        id="clear_plan",
        description="Clear the current plan",
        model_cls=ClearPlanInput,
        f=clear_plan,
    )
    return action


class AddToPlanInput(BaseModel):
    name: str = Field(description="The name of the function to call")
    parameters: object = Field(description="The arguments to pass to the function")


def create_add_to_plan_action():
    def add_to_plan(state: RefactoringAgentState, args: AddToPlanInput):
        action_id = args.name
        action_str = json.dumps(args.parameters)
        request = ActionRequest(id=action_id, action_str=action_str)
        state["plan"].append(request)
        return f"Added {action_id} with args {action_str} to plan"

    # TODO: Eval this part
    description = """
        Add an action to the plan
        """
    action = Action(
        id="add_to_plan",
        description=description,
        model_cls=AddToPlanInput,
        f=add_to_plan,
    )
    return action
