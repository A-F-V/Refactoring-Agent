from typing import List, Tuple, TypedDict

from ..execution import ActionRecord


class History(TypedDict):
    actions_observations: List[ActionRecord]
