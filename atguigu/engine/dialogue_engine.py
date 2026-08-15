from atguigu.domain.messages import UserMessage, ProcessResult,BotMessage
from atguigu.domain.state import DialogueState


class DialogueEngine:
    async def process_message(self,state:DialogueState,user_message:UserMessage)->ProcessResult:
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id = user_message.message_id,
            messages=[BotMessage(text="（占位回复）我已经收到你的消息了。")]
        )
