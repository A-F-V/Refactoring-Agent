from enum import Enum
from typing import List
from src.actions.action import Action, FeedbackMessage
from src.actions.basic_actions import create_logging_action
from src.common.definitions import FailureReason
from src.execution import ActionDispatcher, LLMController
from src.planning.plan_actions import (
    create_action_adder_for_plan,
    create_clear_plan_action,
)
from src.planning.state import RefactoringAgentState
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import END


class Planner:
    def __init__(self, action_list: List[Action]):
        self.plan_dispatcher = ActionDispatcher()
        self.plan_dispatcher.register_action(create_clear_plan_action())
        for action in action_list:
            self.plan_dispatcher.register_action(create_action_adder_for_plan(action))
        # TODO: Stop planning
        task = """Select the next actions to add to the plan or clear the plan.
        Additional Notes:
        - You will be allowed to replan in the future so you can adjust your plan as you go.
        - If your plan requires a result from an action that has not been executed yet, then stop planning.
        - Do not let the plan fill up with garbage
        """
        # TODO: Incorporate Saving thoughts
        self.controller = LLMController(
            self.plan_dispatcher.get_action_list(), task, number_of_actions=3
        )

    def __call__(self, state: RefactoringAgentState):
        # TODO save plan history
        return self.controller(state)


class NextStep(Enum):
    PLAN = "plan"
    EXECUTE = "execute"
    FINISH = "finish"

    def __str__(self):
        return self.value


class NextStepInput(BaseModel):
    should_continue: bool = Field(
        description="Whether we should do another 'plan-executee' (true) loop or finish (false)."
    )


class ShouldContinue:
    next_node: str

    def __init__(self) -> None:
        should_continue_action = self._create_should_continue_action()
        task = """
       Decide ONLY which branch to take next:
       - Plan-Execute branch
       - Finish branch
        Do not return any other information
        """
        self.controller = LLMController([should_continue_action], task)

    def _create_should_continue_action(self):
        def should_continue(state: RefactoringAgentState, args: NextStepInput):
            if args.should_continue:
                self.next_node = "planner"
                return "Moving to planner step"
            else:
                self.next_node = "finish"
                return "Moving to finish step"

        action = Action(
            id="should_continue",
            description="""true = plan and execute, false = finish""",
            model_cls=NextStepInput,
            # return_direct=True,
            f=should_continue,
        )
        return action

    def __call__(self, state: RefactoringAgentState):
        state, decision = self.controller.run(state)
        return self.next_node
