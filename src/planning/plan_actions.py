import json
from typing import List
from src.actions.action import ActionRequest, FeedbackMessage
from src.common.definitions import FailureReason
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
    parameters: object = Field(description="The arguments to pass to the function")


def create_action_adder_for_plan(action: Action):

    def add_to_plan(state: RefactoringAgentState, args: AddToPlanInput):
        action_id = action.id
        action_str = json.dumps(args.parameters)
        # Verify that the action's arguments are valid
        try:
            p_args = action.cls(**args.parameters)
        except Exception as e:
            raise FeedbackMessage(
                FailureReason.INVALID_ACTION_ARGS,
                f"Invalid arguments for action {action_id}: {action_str}",
            )

        request = ActionRequest(id=action_id, args=p_args)
        state["plan"].append(request)
        return f"Added {action_id} with args {action_str} to plan"

    description = f"""
        Adds the following action to the plan:
        {str(action)}
        """

    return Action(
        id=f"add_{action.id}_to_plan",
        description=description,
        model_cls=AddToPlanInput,
        f=add_to_plan,
    )
