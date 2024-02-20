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
        task = """Select the next actions to add to the plan or clear the plan."""
        additional_instructions = """
        - You will be allowed to replan in the future so you can adjust your plan as you go.
        - If your plan requires a result from an action that has not been executed yet, then stop planning.
        - Do not let the plan fill up with garbage"""

        # TODO: Incorporate Saving thoughts
        self.controller = LLMController(
            self.plan_dispatcher.get_action_list(),
            task,
            additional_instructions=additional_instructions,
        )

    def __call__(self, state: RefactoringAgentState):
        # TODO save plan history
        return self.controller(state)


class Thinker:
    def __init__(self):
        task = """Reflect on the current state and write a brief thought to help your future self."""
        additional_instructions = """After thinking, you will be prompted to select some actions to execute. You should consider what actions you have already executed before and factor that into your advice. You will be given more opportunities to think and execute in the future, so keep your thoughts extremely brief.
        For Example:
        `Search for function, read the definition, and extract the function signature`
        """
        self.controller = LLMController(
            [], task, additional_instructions=additional_instructions
        )

    def __call__(self, state: RefactoringAgentState):
        _, thought = self.controller.run(state)
        state["thoughts"].append(thought)
        return state


class NextStep(Enum):
    PLAN = "plan"
    EXECUTE = "execute"
    FINISH = "finish"

    def __str__(self):
        return self.value


class NextStepInput(BaseModel):
    should_continue: bool = Field(
        description="Whether we should do another 'think-executee' (true) loop or finish (false)."
    )


class ShouldContinue:
    next_node: str

    def __init__(self) -> None:
        should_continue_action = self._create_should_continue_action()
        task = """Decide whether to think & execute again or finish. """
        additional_instructions = """Decide ONLY which branch to take next:
       - Think-Execute branch
       - Finish branch
        Do not return reply with any information or reasoning.
        Execute exactly one function"""
        self.controller = LLMController(
            [should_continue_action],
            task,
            additional_instructions=additional_instructions,
        )

    def _create_should_continue_action(self):
        def should_continue(state: RefactoringAgentState, args: NextStepInput):
            if args.should_continue:
                self.next_node = "think"
                return "Moving to thinking step"
            else:
                self.next_node = "finish"
                return "Moving to finish step"

        action = Action(
            id="should_continue",
            description="""true = think and execute, false = finish""",
            model_cls=NextStepInput,
            # return_direct=True,
            f=should_continue,
        )
        return action

    def __call__(self, state: RefactoringAgentState):
        state, decision = self.controller.run(state)
        return self.next_node


class LLMExecutor:
    def __init__(self, action_list: List[Action]):
        task = """Select the next actions to execute."""
        additional_instructions = """You will be allowed to execute actions in the future, so do not worry about executing all the actions at once."""
        self.executor = LLMController(
            action_list, task, additional_instructions=additional_instructions
        )

    def __call__(self, state: RefactoringAgentState):
        return self.executor(state)
