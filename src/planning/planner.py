from enum import Enum
from typing import List
from src.actions.action import Action
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
        Note the following:
        - The history is not visible to the user.
        """
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
        task = """
        Select ONLY one of the following to do next: 'execute', 'plan' or 'finish'.
        - 'execute': Run the next action on the top of the plan
        - 'plan': Adjust the plan/schedule of actions to take by either adding or clearing the current plan. You will not be able to execute actions from the plan if you select this.
        - 'finish': Finish the process. Do not call if there are still actions to take or if the goal has not been perfectly met.
        
        Additional Notes:
        - Transition by only 1 step at a time.
        - Make sure the history of executed actions completes the goal in its entirety. 
        - If you are asked a query, you must answer it by writting to the console (only achieved by calling `print-message`).
        - You may need to adjust your plan as you go, especially if a result from a past action should be incorporated into a future action.
        
        """
        self.controller = LLMController([next_step_action], task)

    def _create_next_step_action(self):
        def transition_to_next_node(state: RefactoringAgentState, args: NextStepInput):
            if args.next_step == NextStep.PLAN:
                self.next_node = "planner"
            elif args.next_step == NextStep.EXECUTE:
                if state["plan"]:
                    self.next_node = "execute"
                else:
                    self.next_node = "planner"  # TODO: error state
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
