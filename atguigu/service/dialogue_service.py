from atguigu.domain.messages import UserMessage,ProcessResult
from atguigu.domain.state import DialogueState
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.repository.dialogue_repository import DialogueRepository



class DialogueService:
    def __init__(self,dialogue_state_repository:DialogueRepository,
                 dialogue_engine: DialogueEngine):
        self.dialogue_state_repository = dialogue_state_repository
        self.dialogue_engine = dialogue_engine

    async def process_message(self,user_message:UserMessage) -> ProcessResult:

        state:DialogueState = await self.dialogue_state_repository.load_state(user_message.sender_id)

        process_result:ProcessResult = await self.dialogue_engine.process_message(state,user_message)

        # 3.通过repository 保存最新对话状态
        await self.dialogue_state_repository.save_state(state)

        # 4.返回本轮处理结果
        return process_result
