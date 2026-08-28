
from typing import Any
from dataclasses import dataclass, field

from atuguigu.task.action.base import ActionResult
from atuguigu.task.action.register import ActionRegister
from atuguigu.domain.state import DialogueState


@dataclass(slots=True)
class ActionCall:
    action_name: str
    action_kwargs: dict[str,Any] = field(default_factory=dict)


class ActionRunner:
    """
    专门负责运行 Action
    """

    def __init__(self,action_register: ActionRegister):
        self.action_register = action_register


    async def run(self,action_call: ActionCall,state:DialogueState) -> ActionResult:

        action = self.action_register.get_action(action_call.action_name)
        action_result = await action.run(action_call.action_kwargs,state)

        return action_result