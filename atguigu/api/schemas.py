
"""
接口数据模型，前后端交互使用
"""
from typing import Any
from pydantic import BaseModel, Field
from atguigu.domain.messages import ChatHistoryMessage


class ChatObject(BaseModel):
    id:str
    type:str
    title:str | None = None
    attributes:dict[str,Any] = Field(default_factory=dict)

class ChatBotMessage(BaseModel):
    text: str | None = None
    object:ChatObject | None = None


class ChatRequest(BaseModel):
    sender_id:str
    message_id:str | None = None
    text:str | None = None
    object:ChatObject | None = None


class ChatResponse(BaseModel):
    """
    响应数据模型
    """
    message_id:str
    messages:list[ChatBotMessage]


class ChatHistoryResponse(BaseModel):
    sender_id:str
    messages:list[ChatHistoryMessage]



