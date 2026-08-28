from typing import Literal

from atuguigu.api.schemas import ChatHistoryResponse
from atuguigu.domain.messages import UserMessage, BotMessage, MessageType, FocusedObject, ChatHistoryMessage
from atuguigu.domain.state import Turn

class ChatHistoryBuilder:

    @staticmethod
    def build_turns_message(turns: list[Turn]) -> str:
        """
        构建历史对话 最后10轮
        Q: 用户问题
        A: 机器人回复
        """

        chat_history = []
        for turn in turns:
            # 1.获取用户角色的消息
            user_message = turn.user_message
            user_message_str = ChatHistoryBuilder._build_message(user_message)
            chat_history.append(f"USER:{user_message_str}")

            bot_messages = turn.bot_messages
            for bot_message in bot_messages:
                bot_message_str = ChatHistoryBuilder._build_message(bot_message)
                chat_history.append(f"BOT:{bot_message_str}")

        return "\n".join(chat_history)

    @staticmethod
    def _build_message(message:UserMessage | BotMessage) -> str:

        if isinstance(message, BotMessage) and message.object is None:
            return  message.text.strip()

        if isinstance(message, UserMessage) and message.type is MessageType.TEXT:
            return message.text.strip()

        return ChatHistoryBuilder._render_object_message(message.object)

    @staticmethod
    def _render_object_message(object:FocusedObject) -> str:
        id = object.id
        label = {
            "account": "账户",
            "card": "银行卡",
            "loan": "贷款",
            "transaction": "交易",
            "product": "产品",
        }.get(object.type, "业务对象")
        title = object.title
        attributes_str = "|".join([f"{k}={v}" for k,v in object.attributes.items()])
        return f"【id={id} label={label} title={title} attributes={attributes_str}】"

    @classmethod
    def build_chat_history(cls,  session_id: str,
                           role: Literal["user", "bot"],
                           text: str,
                           object: FocusedObject) -> ChatHistoryMessage:
        return ChatHistoryMessage(session_id=session_id,
                                  role=role,
                                  text=text,
                                  object=object
                                  )
