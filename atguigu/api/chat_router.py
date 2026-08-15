import uuid

from fastapi import APIRouter, Depends

from atguigu.api.dependencies import get_dialogue_service
from atguigu.api.schemas import ChatRequest, ChatResponse, ChatBotMessage, ChatObject, ChatHistoryResponse
from atguigu.domain.messages import UserMessage, ProcessResult, MessageType, FocusedObject, ChatHistoryMessage
from atguigu.service.dialogue_service import DialogueService


chat_router = APIRouter()


@chat_router.post("/api/chat")
async def chat(
        chat_request: ChatRequest,
        dialogue_service: DialogueService = Depends(get_dialogue_service),
) -> ChatResponse:

    # 接口数据模型转换成领域数据模型
    user_message = _build_user_message(chat_request)

    process_result:ProcessResult = await dialogue_service.process_message(user_message)

    chat_response = _build_chat_response(process_result)

    return chat_response


@chat_router.get("/api/chat/history",response_model=ChatHistoryResponse)
async def get_chat_history(sender_id:str,service:DialogueService):
    return ChatHistoryResponse(
        sender_id=sender_id,
        messages=[
            ChatHistoryMessage(role='user', text='你好',session_id=1),
            ChatHistoryMessage(role='bot', text='我不好',session_id=1),
        ],
    )


def _build_user_message(chat_request:ChatRequest) -> UserMessage:
    return UserMessage(
        sender_id= chat_request.sender_id,
        message_id=str(uuid.uuid4()),
        type= MessageType.OBJECT if chat_request.object is not None else MessageType.TEXT,
        text= chat_request.text,
        object= FocusedObject(
            id = chat_request.object.id,
            type = chat_request.object.type,
            title=chat_request.object.title,
            attributes=chat_request.object.attributes
        ) if chat_request.object is not None else None
    )


def _build_chat_response(process_result:ProcessResult) -> ChatResponse:
    return ChatResponse(
        message_id=process_result.message_id,
        messages=[
            ChatBotMessage(
                text=bot_message.text,
                object=ChatObject(
                    id = bot_message.object.id,
                    type = bot_message.object.type,
                    title = bot_message.object.title,
                    attributes=bot_message.object.attributes
                ) if bot_message.object is not None else None
            )
            for bot_message in process_result.messages
        ]
    )

