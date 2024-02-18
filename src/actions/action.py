from abc import ABC, abstractmethod
from enum import Enum
from sre_constants import SUCCESS
from typing import TypeVar, Generic, Callable, Type, TypedDict
from ..common import ProjectContext
from pydantic import BaseModel
from langchain_core.output_parsers import JsonOutputParser

# Action is an abstract base class


class Action(ABC):
    def __init__(self, id, description):
        self.id = id
        self.description = description

    @abstractmethod
    def execute(self, action_str: str, **kwargs) -> str:
        pass

    @abstractmethod
    def get_prompt_schema(self) -> str:
        pass


class ActionSuccess(Enum):
    SUCCESS = "SUCCESS"
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    ACTION_FAILED = "ACTION_FAILED"


class ActionRecord(TypedDict):
    id: str
    success: ActionSuccess
    action_str: str
    observation: str


AA = TypeVar("AA", bound=BaseModel)
# Ensure AA is a pedantic type


class ProjectContextualisedAction(Action, Generic[AA]):
    def __init__(
        self,
        id,
        description,
        model_cls: Type[AA],
        f: Callable[[ProjectContext, AA], str],
    ):
        super().__init__(id, description)
        self.parser = JsonOutputParser(pydantic_object=model_cls)
        self.f = f
        self.cls = model_cls

    def execute(self, action_str: str, **kwargs) -> str:
        context = kwargs.get("context")
        if not context or not isinstance(context, ProjectContext):
            raise ValueError("No context provided")
        args = self.parser.invoke(action_str)
        return self.f(context, args)

    def get_prompt_schema(self) -> str:
        return str(self.cls.model_json_schema())


class ActionDispatcher:
    def __init__(self):
        self.actions = {}

    def register_action(self, action: Action):
        self.actions[action.id] = action

    def dispatch(self, id: str, action_str: str, **kwargs) -> ActionRecord:
        action = self.actions.get(id)
        if action:
            try:
                observation = action.execute(action_str, **kwargs)
                return ActionRecord(
                    id=id,
                    success=ActionSuccess.SUCCESS,
                    action_str=action_str,
                    observation=observation,
                )
            except Exception as e:
                return ActionRecord(
                    id=id,
                    success=ActionSuccess.ACTION_FAILED,
                    action_str=action_str,
                    observation=str(e),
                )
        else:
            return ActionRecord(
                id=id,
                success=ActionSuccess.ACTION_NOT_FOUND,
                action_str=action_str,
                observation="",
            )
