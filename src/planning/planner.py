from enum import Enum
from typing import List
from src.actions.action import Action
from src.execution import ActionDispatcher, LLMController
from src.planning.plan_actions import (
    create_add_to_plan_action,
    create_clear_plan_action,
)
from src.planning.state import RefactoringAgentState
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import END


class Planner:
    def __init__(self, action_list: List[Action]):
        self.plan_dispatcher = ActionDispatcher()
        self.plan_dispatcher.register_action(create_clear_plan_action())
        self.plan_dispatcher.register_action(create_add_to_plan_action(action_list))
        # TODO: Stop planning
        task = "Plan the next actions to take to achieve the ultimate goal"
        self.controller = LLMController(self.plan_dispatcher.get_action_list(), task)

    def __call__(self, state: RefactoringAgentState):
        # TODO save plan history
        return self.controller(state)


class NextStep(Enum):
    PLAN = "plan"
    EXECUTE = "execute"
    FINISH = "finish"


class NextStepInput(BaseModel):
    next_step: NextStep = Field(description="The next step to take")


class DecisionMaker:
    next_node: str

    def __init__(self) -> None:
        next_step_action = self._create_next_step_action()
        task = "Select whether to plan, execute, or finish. You must only choose one to do right now. Select finish when there is no work in the plan to execute."
        self.controller = LLMController([next_step_action], task)

    def _create_next_step_action(self):
        def transition_to_next_node(state: RefactoringAgentState, args: NextStepInput):
            if args.next_step == NextStep.PLAN:
                self.next_node = "planner"
            elif args.next_step == NextStep.EXECUTE:
                if state["plan"]:
                    self.next_node = "execute"
                else:
                    self.next_node = END  # TODO: error state
            else:
                self.next_node = END
            return f"Transitioning to {self.next_node}"

        action = Action(
            id="transition_to_next_step",
            description="Transition to the next step",
            model_cls=NextStepInput,
            f=transition_to_next_node,
        )
        return action

    def __call__(self, state: RefactoringAgentState):
        state, decision = self.controller.run(state)
        return self.next_node
