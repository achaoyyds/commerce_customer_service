from atuguigu.domain.state import DialogueState
from atuguigu.domain.messages import BotMessage
from atuguigu.domain.state import DialogueState
from atuguigu.handlers.chitchat_responder import ChitChatResponder


class ChitChatHandler:

    def __init__(self,chat_responder:ChitChatResponder):
        self.chat_responder = chat_responder

    async def handle(self,chat:str,dialogue_state:DialogueState):
        return await self.chat_responder.respond_chat(chat,dialogue_state)