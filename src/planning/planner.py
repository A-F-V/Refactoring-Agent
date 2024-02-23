from enum import Enum
from typing import List
from src.actions.action import Action, FeedbackMessage
from src.actions.basic_actions import create_logging_action
from src.common.definitions import FailureReason
from src.evaluation.feedback_functions import (
    create_evolving_thought_feedback,
    create_repeating_work_feedback,
    create_short_thought_feedback,
)
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


class NewThought(BaseModel):
    thought: str = Field(description="The thought to add to the thoughts list")


class Thinker:
    def __init__(self, action_list):

        def create_thought():

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

        action_ids = ["- " + action.id for action in action_list]
        action_str = "\n".join(action_ids)

        task = """Reflect on the current state and write a brief thought to help your future self."""
        # old_instruction additional_instructions = """Use this as a way to plan your next steps, reflect on what went well and how you can improve. Be incredibly brief (1-2 sentences). This message will be saved in the thoughts section. Do not prefix your answer."""
        additional_instructions = f"""Use this as a way to plan your next steps, reflect on what went well and how you can improve. Be incredibly brief (try to use fewer than 150 characters), mentioning only the most relevant and salient points, paraphrasing in a semi-colon seperated list. For example: 'do X; avoid Y; consider Z.'
For reference, the available actions are:
{action_str}
Reason in terms of these symbols.
        """

        def eval_think_factory(state: RefactoringAgentState):
            return [
                create_evolving_thought_feedback(state),
                create_short_thought_feedback(),
                create_repeating_work_feedback(state),
            ]

        self.add_thought = create_thought()
        self.controller = LLMController(
            [],
            task,
            additional_instructions=additional_instructions,
            record_history=False,
            eval_factory=eval_think_factory,
        )

    def __call__(self, state: RefactoringAgentState):
        state, result = self.controller.run(state)
        args = NewThought(thought=str(result))
        self.add_thought.execute(state, args)
        print("Thought added to the thoughts list")
        return state


class NextStep(Enum):
    PLAN = "plan"
    EXECUTE = "execute"
    FINISH = "finish"

    def __str__(self):
        return self.value


class NextStepInput(BaseModel):
    should_continue: bool = Field(
        description="Whether we should do another 'think-execute' (true) loop or finish (false)."
    )


class ShouldContinue:
    next_node: str

    def __init__(self) -> None:
        self.should_continue_action = self._create_should_continue_action()
        task = """Decide whether to think & execute again or finish. """
        additional_instructions = (
            """Return 'true' to think and execute again, or 'false' to finish."""
        )
        self.controller = LLMController(
            [],
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
        for retry in range(3):
            state, decision = self.controller.run(state)
            # Parse the decision
            if decision == "true":
                return "think"
            elif decision == "false":
                return "finish"

        raise Exception("Failed to parse the decision")


class LLMExecutor:
    def __init__(self, action_list: List[Action]):
        task = """Select the next actions to execute."""
        additional_instructions = """You will be allowed to execute actions in the future, so do not worry about executing all the actions at once. **Execute only one function**.. Say 'Done' after you are done invoking the function."""
        self.executor = LLMController(
            action_list,
            task,
            additional_instructions=additional_instructions,
            record_history=True,
        )

    def __call__(self, state: RefactoringAgentState):
        return self.executor(state)
