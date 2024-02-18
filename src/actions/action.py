from abc import ABC, abstractmethod
from ast import Str
from enum import Enum
import json
from re import I
from sre_constants import SUCCESS
from typing import TypeVar, Generic, Callable, Type, TypedDict
from unittest.mock import Base
from ..common import ProjectContext
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain.tools import tool, StructuredTool

# Action is an abstract base class

ActionArgs = TypeVar("ActionArgs", bound=BaseModel)
State = TypeVar("State")


class Action(Generic[ActionArgs, State]):
    def __init__(
        self,
        id,
        description,
        model_cls: Type[ActionArgs],
        f: Callable[[State, ActionArgs], str],
    ):
        self.id = id
        self.description = description
        self.parser = JsonOutputParser(pydantic_object=model_cls)
        self.f = f
        self.cls = model_cls

    def execute(self, state: State, action_str: str) -> str:
        action_args = self.parser.invoke(action_str)
        result = self.f(state, action_args)
        return result

    def to_tool(self, state) -> StructuredTool:
        def tool_f(**kwargs):
            return self.f(state, self.cls(**kwargs))

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
