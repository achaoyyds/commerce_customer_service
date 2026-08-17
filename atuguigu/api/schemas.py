"""
定义接口数据模型：和前端进行交互
集成BaseModel:在运行期间完成类型的校验和类型的转换
"""

from typing import Any
from pydantic import BaseModel

class ChatObject(BaseModel):
    id:str
    title:str
    type:str
    attributes: dict[str,Any]

class ChatBotMessage(BaseModel):
    text: str
    object: ChatObject | None = None

class ChatRequest(BaseModel):
    sender_id: str
    text: str
    object: ChatObject | None = None

class ChatResponse(BaseModel):
    """
    聊天响应的数据模型
    """
    message_id:str
    messages:list[ChatBotMessage]


