from atuguigu.domain.messages import UserMessage, ProcessedResult, ChatHistoryMessage
from atuguigu.engines.dialogue_engine import DialogueEngine
from atuguigu.repository.dialogue_repository import DialogueRepository
from atuguigu.observability.repository import ObservabilityRepository
from atuguigu.utils.message_utils import ChatHistoryBuilder


class DialogueStateService:

    def __init__(self,engine: DialogueEngine,repository: DialogueRepository, observability_repository: ObservabilityRepository | None = None):
        self._engine = engine
        self._repository = repository
        self._observability = observability_repository

    async def process_message(self,user_message: UserMessage) -> ProcessedResult:
        dialogue_state = await self._repository.load_state(user_message.sender_id)

        processed_result = await self._engine.process_message(user_message, dialogue_state)

        await self._repository.save_state(user_message.sender_id,dialogue_state)

        # 拆历史 + 落 trace（best-effort，失败不阻断主聊天链路）
        trace = self._engine.take_trace()
        if trace is not None and self._observability is not None:
            try:
                await self._observability.persist_turn(dialogue_state, trace)
            except Exception as exc:  # noqa: BLE001 - 可观测性落库失败不影响业务
                print(f"[observability] 落库失败：{exc}")

        return processed_result

    async def get_chat_history(self, sender_id:str) -> list[ChatHistoryMessage]:

        # 1.查询当前用户对应的整个对话状态
        state = await self._repository.load_state(sender_id)

        # 2. 获取当前用户对话状态的sessions
        final_chat_history = []
        for session in state.sessions:

            for turn in session.turns:
                user_message = turn.user_message


                user_chat_message = ChatHistoryBuilder.build_chat_history(session.session_id,"user",user_message.text,user_message.object)

                final_chat_history.append(user_chat_message)
                bot_messages = turn.bot_messages
                for bot_message in bot_messages:
                    bot_chat_message = ChatHistoryBuilder.build_chat_history(session.session_id,
                                                                             "bot",
                                                                             bot_message.text,
                                                                             bot_message.object)
                    final_chat_history.append(bot_chat_message)

        return final_chat_history




