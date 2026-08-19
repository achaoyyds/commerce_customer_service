from dataclasses import dataclass
from typing import Any

from atuguigu.command.commands import Command


@dataclass(slots=True)
class TaskTurnPlan:

    commands: list[Command]

    @classmethod
    def from_dict(cls, data: dict[str,Any]) -> "TaskTurnPlan":
        return cls(
            commands=[Command.from_dict(cmd) for cmd in data["commands"]]
        )


@dataclass(slots=True)
class KnowledgeTurnPlan:
    intents: list[str]

    @classmethod
    def from_dict(cls, data: dict[str,Any]) -> "KnowledgeTurnPlan":
        return cls(
            intents = data["intents"],
        )

@dataclass(slots=True)
class ChitChatTurnPlan:
    chat: str

    @classmethod
    def from_dict(cls, data: dict[str,Any]) -> "ChitChatTurnPlan":
        return cls(
            chat = data["chat"],
        )

@dataclass(slots=True)
class TurnPlan:
    """
    数据模型
    作用：一轮的路由结果
    """
    task: TaskTurnPlan | None = None
    knowledge: KnowledgeTurnPlan | None = None
    chitchat: ChitChatTurnPlan | None = None
    
    @classmethod
    def from_dict(cls, turn_plan_data: dict[str,Any]) -> "TurnPlan":
        return cls(
            task=TaskTurnPlan.from_dict(turn_plan_data['task']) if turn_plan_data.get('task') is not None else None,
            knowledge=KnowledgeTurnPlan.from_dict(turn_plan_data['knowledge']) if turn_plan_data.get(
                'knowledge') is not None else None,
            chitchat=ChitChatTurnPlan.from_dict(turn_plan_data['chitchat']) if turn_plan_data.get(
                'chitchat') is not None else None
        )
