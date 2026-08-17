from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert  # 注意mysql包
import json
from atuguigu.domain.state import DialogueState
from atuguigu.repository.dialogue_record import DialogueRecord

class DialogueRepository:

    def __init__(self,session:AsyncSession):
        self._session = session

    async def load_state(self,sender_id: str) -> DialogueState:
        stmt = select(DialogueRecord).where(DialogueRecord.sender_id == sender_id)

        cursor = await self._session.execute(stmt)

        record:DialogueRecord = cursor.scalar_one_or_none()
        if record is None:
            return DialogueState(sender_id=sender_id)

        state_dict = json.loads(record.state_json)

        return DialogueState.from_dict(state_dict)


    async def save_state(self,sender_id: str, state:DialogueState):

        state_dict = DialogueState.to_dict(state)

        dialogue_state_json = json.dumps(state_dict, ensure_ascii=False)

        insert_stmt = insert(DialogueRecord).values(sender_id=sender_id, state_json=dialogue_state_json)

        update_stmt = insert_stmt.on_duplicate_key_update(state_json=insert_stmt.inserted.state_json)

        await self._session.execute(update_stmt)

        await self._session.commit()
