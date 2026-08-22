from typing import Any

from atuguigu.task.action.base import Action, ActionResult
from atuguigu.domain.state import DialogueState


class ActionListener(Action):
    name = "action_listen"

    async def run(self, action_args: dict[str, Any],state:DialogueState) -> ActionResult:
        pass


