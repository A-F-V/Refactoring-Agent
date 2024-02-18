from typing import List, Tuple, TypedDict

from src.actions.action import ActionRecord


class History(TypedDict):
    actions_observations: List[ActionRecord]
