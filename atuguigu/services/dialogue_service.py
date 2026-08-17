from atuguigu.domain.messages import UserMessage,ProcessedResult
from atuguigu.engines.dialogue_engine import DialogueEngine
from atuguigu.repository.dialogue_repository import DialogueRepository

class DialogueStateService:

    def __init__(self,engine: DialogueEngine,repository: DialogueRepository):
        self._engine = engine
        self._repository = repository

    async def process_message(self,user_message: UserMessage) -> ProcessedResult:
        dialogue_state = await self._repository.load_state(user_message.sender_id)

        processed_result = await self._engine.handle_message(dialogue_state)

        await self._repository.save_state(user_message.sender_id,dialogue_state)

        return processed_result

