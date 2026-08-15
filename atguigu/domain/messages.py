from dataclasses import field, dataclass
from enum import Enum
from typing import Any, Dict, Literal


class MessageType(Enum):
    TEXT = "text"
    OBJECT = "object"

@dataclass(slots=True)
class FocusedObject:
    type:str
    id:str
    title:str | None = None
    attributes:dict[str,Any] = field(default_factory=dict)


    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "id": self.id,
            "title": self.title,
            "attributes": dict(self.attributes)
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FocusedObject":
        return cls(
            type = data["type"],
            id = data["id"],
            title = data.get("title",""),
            attributes = data.get("attributes",{})
        )

@dataclass(slots=True)
class UserMessage:
    sender_id:str
    message_id:str
    type: MessageType
    text:str | None = None
    object : FocusedObject | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "message_id": self.message_id,
            "type": self.type.value,
            "text": self.text,
            "object": self.object.to_dict() if self.object else None
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserMessage":
        return cls(
            sender_id = data["sender_id"],
            message_id = data["message_id"],
            type = MessageType(data["type"]),
            text = data["text"],
            object = FocusedObject.from_dict(data["object"]) if data.get("object") else None
        )

@dataclass(slots=True)
class BotMessage:
    text: str | None = None
    object: FocusedObject | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "object": self.object.to_dict() if self.object else None
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BotMessage":
        return cls(
            text = data["text"],
            object = FocusedObject.from_dict(data["object"]) if data.get("object")  else None
        )

@dataclass(slots=True)
class ProcessResult:
    message_id: str
    sender_id: str
    messages:list[BotMessage]


@dataclass(slots=True)
class ChatHistoryMessage:
    session_id:str
    role:Literal["user","bot",]
    text:str | None = None
    object: FocusedObject | None = None








