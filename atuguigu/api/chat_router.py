from uuid import uuid4

from dataclasses import dataclass
from fastapi import APIRouter,Depends
from atuguigu.api.schemas import ChatRequest,ChatResponse,ChatBotMessage,ChatObject
from atuguigu.domain.messages import UserMessage,ProcessedResult,MessageType,FocusedObject
from atuguigu.api.dependencies import DialogueStateServiceDep

router = APIRouter()

@router.get("/")
def hello_endpoint():
    return {"message":"Hello World"}

@dataclass(slots=True)
class User:
    name: str
    age: int
    address: str

@router.get("/test",response_model=User)
def test():
    return {
        "name":"zs",
        "age":"22",
        "address":"sz",
        "message":"hello world"
    }


def _build_user_message(chat_request:ChatRequest) -> UserMessage:
    return UserMessage(
        sender_id=chat_request.sender_id,
        message_id= str(uuid4().hex),
        type= MessageType.OBJECT if chat_request.object is not None else MessageType.TEXT,
        text=chat_request.text,
        object= FocusedObject(
            id=chat_request.object.id,
            type= chat_request.object.type,
            title= chat_request.object.title,
            attributes= chat_request.object.attributes
        ) if chat_request.object is not None else None
    )


def _build_chat_response(processed_result:ProcessedResult):
    return ChatResponse(
        message_id=processed_result.message_id,
        messages= [ChatBotMessage(
              text=msg.text,
              object = ChatObject(
                id = msg.object.id,
                title=msg.object.title,
                type=msg.object.type,
                attributes=msg.object.attributes
            ) if msg.object is not None else None)
                   for msg in processed_result.messages]
    )


@router.post("/api/chat",response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest, service:DialogueStateServiceDep):
    # 1.将接口数据模型转成领域数据模型
    user_message = _build_user_message(chat_request)

    # 2.调用service 处理领域数据模型 --- 返回的还是领域数据模型
    processed_result = await service.process_message(user_message)

    # 3.将处理后的领域数据模型转成 接口数据模型
    chat_response = _build_chat_response(processed_result)
    return chat_response








