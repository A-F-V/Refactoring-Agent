from math import e
from typing import Optional
from trulens_eval import Feedback, Select
from trulens_eval import Tru
from trulens_eval import TruChain
from trulens_eval.feedback import OpenAI as fOpenAI
import numpy as np

from src.planning.state import RefactoringAgentState, record_to_str

tru = Tru()

# These are to be used by the LLMController where the second query is the one that is used

sentinel = -1.0


def create_sentinel_aggregator(agg):
    def aggregator(values):
        # Filter out None values
        values = [v for v in values if v is not sentinel]
        return agg(values)

    return aggregator


def create_tool_relevance_feedback(state):
    def tool_relevance(output) -> float:
        provider = fOpenAI()
        # return sentinel if the output is not a dict
        if (
            not isinstance(output, dict)
            or "tool" not in output
            or "tool_input" not in output
        ):
            return sentinel
        tool_id = output["tool"]
        tool_input = output["tool_input"]
        res = float(
            provider.endpoint.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "How relevant was the selection of TOOL with TOOL_INPUT in addressing the current task in STATE? Reply with a number between 0 and 10.",
                    },
                    {
                        "role": "user",
                        "content": f"TOOL: {tool_id}; TOOL_INPUT: {tool_input}; STATE: {state}",
                    },
                ],
            )
            .choices[0]
            .message.content
        )
        return res

    f_tool_relevance = (
        Feedback(tool_relevance)
        .on_output()
        .aggregate(create_sentinel_aggregator(np.mean))
    )
    return f_tool_relevance


def create_short_thought_feedback():
    def short_thought(thought: str) -> float:
        return float(e ** (-float(len(thought)) * 0.003))

    return Feedback(short_thought).on_output()


def create_evolving_thought_feedback(state: RefactoringAgentState):
    def evolving_thought(thought: str):
        provider = fOpenAI()
        past_thoughts_actions = []
        if len(state["history"]) == 0:
            return 1.0
        for i in range(len(state["thoughts"]) - 1):
            past_thoughts_actions.append(
                f"#T{i}: {state['thoughts'][i]}\n#A{i}: {record_to_str(state['history'][i])}"
            )
        res = float(
            provider.endpoint.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "Given PAST_THOUGHTS_AND_ACTIONS, how much has the NEXT_THOUGHT added to solving the ULTIMATE_GOAL? Give a number between 0 to 1 where 1 means it has contributed to achieving the goal in its fullest. Reply only with a number, for example: '0.75'",
                    },
                    {
                        "role": "user",
                        "content": f"### PAST_THOUGHTS_AND_ACTIONS ###\n {past_thoughts_actions}\n\n\n ### NEXT_THOUGHT ###\n {thought}\n\n\n ### ULTIMATE_GOAL ###\n {state['goal']}",
                    },
                ],
            )
            .choices[0]
            .message.content
        )
        return res

    return Feedback(evolving_thought).on_output()


def create_repeating_work_feedback(state: RefactoringAgentState):
    def no_repeated_work(thought: str):
        provider = fOpenAI()
        past_thoughts_actions = []
        if len(state["history"]) == 0:
            return 1.0
        for i in range(len(state["history"]) - 1):
            past_thoughts_actions.append(f"#A{i}: {record_to_str(state['history'][i])}")
        res = float(
            provider.endpoint.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "Given PAST_ACTIONS, how much is the NEXT_THOUGHT suggesting we repeat work already completed? Give a number between 0 to 1 where 1 means it is suggesting a full repeat of work already completed. Reply only with a number, for example: '0.5'",
                    },
                    {
                        "role": "user",
                        "content": f"### PAST_ACTIONS ###\n {past_thoughts_actions}\n\n\n ### NEXT_THOUGHT ###\n {thought}",
                    },
                ],
            )
            .choices[0]
            .message.content
        )
        return 1 - res

    return Feedback(no_repeated_work).on_output()
