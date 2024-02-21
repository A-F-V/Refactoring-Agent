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

        def create_thought():
            class NewThought(BaseModel):
                thought: str = Field(
                    description="The thought to add to the thoughts list"
                )

            def thought(state: RefactoringAgentState, args: NewThought):
                state["thoughts"].append(args.thought)
                return 'Say "Done"'

            action = Action(
                id="add_thought",
                description="Add a thought to the thoughts list.",
                model_cls=NewThought,
                f=thought,
            )
            return action

        task = """Reflect on the current state and write a brief thought to help your future self."""
        additional_instructions = """Use this as a way to plan your next steps, reflect on what went well and how you can improve. Be incredibly brief (1-2 sentences). 
        Call the add_thought function to add a thought to the thoughts list. Say 'Done' after you have added your thought."""
        self.controller = LLMController(
            [create_thought()],
            task,
            additional_instructions=additional_instructions,
            record_history=False,
        )

    def __call__(self, state: RefactoringAgentState):
        return self.controller(state)


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
        additional_instructions = """Call the `should_continue` function with a true boolean to continue thinking & executing, and false to finish. Say 'Done' after you have called `should_continue`. Call `should_continue` only once."""
        self.controller = LLMController(
            [should_continue_action],
            task,
            additional_instructions=additional_instructions,
            record_history=False,
        )

    def _create_should_continue_action(self):
        def should_continue(state: RefactoringAgentState, args: NextStepInput):
            message = f"You said should_continue={args.should_continue}. Wait for further instructions and do not invoke any functions including `should_continue`. Simply say 'Done'"
            if args.should_continue:
                self.next_node = "think"
            else:
                self.next_node = "finish"
            return message

        action = Action(
            id="should_continue",
            description="""true = think and execute, false = finish.""",
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
        additional_instructions = """You will be allowed to execute actions in the future, so do not worry about executing all the actions at once.
        Call any of the available functions. Say 'Done' after you are done invoking functions."""
        self.executor = LLMController(
            action_list,
            task,
            additional_instructions=additional_instructions,
            record_history=True,
        )

    def __call__(self, state: RefactoringAgentState):
        return self.executor(state)
