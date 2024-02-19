import json
from uuid import UUID
from langchain.callbacks.base import BaseCallbackHandler
from re import I
from sre_constants import SUCCESS
from typing import Optional, TypeVar, Generic, Callable, Type, TypedDict
from unittest.mock import Base
from src.common.definitions import FailureReason

from src.planning.state import ActionRequest, FeedbackMessage, RefactoringAgentState
from ..common import ProjectContext
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain.tools import tool, StructuredTool

# Action is an abstract base class


# State = TypeVar("State")

ActionArgs = TypeVar("ActionArgs", bound=BaseModel)
ActionReturnType = TypeVar("ActionReturnType")


class Action(Generic[ActionArgs, ActionReturnType]):
    def __init__(
        self,
        id,
        description,
        model_cls: Type[ActionArgs],
        f: Callable[[RefactoringAgentState, ActionArgs], ActionReturnType],
        return_direct=False,
    ):
        self.id = id
        self.description = description
        self.parser = JsonOutputParser(pydantic_object=model_cls)
        self.f = f
        self.cls = model_cls
        self.return_direct = return_direct

    def execute(
        self, state: RefactoringAgentState, args: ActionArgs
    ) -> ActionReturnType:
        return self.f(state, args)

    def to_tool(self, state: RefactoringAgentState) -> StructuredTool:
        class Callbacks(BaseCallbackHandler):
            def on_tool_error(
                self,
                error: BaseException,
                *,
                run_id: UUID,
                parent_run_id: UUID | None = None,
                **kwargs,
            ):
                if error is FeedbackMessage:
                    state["feedback"].append(error)

        def tool_f(**kwargs) -> ActionReturnType:
            args_str = json.dumps(kwargs)
            try:
                args = self.cls(**kwargs)
                request = ActionRequest(id=self.id, args=args)
                try:
                    return self.f(state, args)
                except FeedbackMessage as f:
                    raise f
                except Exception as e:
                    raise FeedbackMessage(
                        FailureReason.ACTION_FAILED, str(e), request=request
                    )
            except Exception as e:
                raise FeedbackMessage(
                    FailureReason.INVALID_ACTION_ARGS,
                    f"Coulnd't parse arguments: {args_str}",
                )

        return StructuredTool(
            name=self.id,
            callbacks=[Callbacks()],
            description=self.description,
            args_schema=self.cls,
            func=tool_f,
            return_direct=self.return_direct,
        )

    def __str__(self):
        return f"""{{"name": '{self.id}', "description": '{self.description}', "parameters": {self.cls.schema()['properties']}}}"""
