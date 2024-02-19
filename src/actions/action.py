from abc import ABC, abstractmethod
from ast import Str
from enum import Enum
import json
from re import I
from sre_constants import SUCCESS
from typing import TypeVar, Generic, Callable, Type, TypedDict
from unittest.mock import Base
from src.common.definitions import FailureReason, FeedbackMessage

from src.planning.state import RefactoringAgentState
from ..common import ProjectContext
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain.tools import tool, StructuredTool

# Action is an abstract base class

ActionArgs = TypeVar("ActionArgs", bound=BaseModel)
# State = TypeVar("State")


class Action(Generic[ActionArgs]):
    def __init__(
        self,
        id,
        description,
        model_cls: Type[ActionArgs],
        f: Callable[[RefactoringAgentState, ActionArgs], str],
    ):
        self.id = id
        self.description = description
        self.parser = JsonOutputParser(pydantic_object=model_cls)
        self.f = f
        self.cls = model_cls

    def execute(self, state: RefactoringAgentState, action_str: str) -> str:
        action_args = self.parser.invoke(action_str)
        result = self.f(state, action_args)
        return result

    def to_tool(self, state: RefactoringAgentState) -> StructuredTool:
        def tool_f(**kwargs):
            try:
                try:
                    args = self.cls(**kwargs)
                except Exception as e:
                    raise FeedbackMessage(FailureReason.INVALID_ACTION_ARGS, str(e))
                try:
                    return self.f(state, args)
                except Exception as e:
                    raise FeedbackMessage(FailureReason.ACTION_FAILED, str(e))
            except FeedbackMessage as f:
                state["feedback"].append(f)

        return StructuredTool(
            name=self.id,
            description=self.description,
            args_schema=self.cls,
            func=tool_f,
        )

    def __str__(self):
        return f"""Action: {self.id}
                Description: {self.description}
                Args: {self.cls.schema()}"""
