import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert  # 注意

from atguigu.domain.state import DialogueState
from atguigu.repository.dialogue_record import DialogueRecord

class DialogueRepository:

    def __init__(self,session: AsyncSession):
        self.session = session

    async def load_state(self,sender_id:str) -> DialogueState:
        """
        根据用户ID 从数据库中查询该用户的完整对话状态
        Args:
            sender_id: 用户ID

        Returns:DialogueState: 用户的完整对话状态

        """
        stmt = select(DialogueRecord).where(DialogueRecord.sender_id == sender_id)

        cursor = await self.session.execute(stmt)

        record = cursor.scalar_one_or_none()
        if record is None:
            return DialogueState(sender_id=sender_id)

        state_dict = json.loads(record.state_json)

        return DialogueState.from_dict(state_dict)

    async def save_state(self,sender_id:str,dialogue_state:DialogueState):
        """
        将引擎处理后的state 保存到数据库中
        不是直接保存，会涉及修改
        1. 如果第一次来(sender_id主键第一次没有生成，数据表中没有sender_id值) 保存
        2. 如果非第一次进来(sender_id主键已经生成，数据表中有sender_id这一列值) 修改
        sender_id 是唯一的
        Args:
            sender_id: 用户ID
            dialogue_state: 引擎修改后的状态

        Returns:
        """
        dialogue_state_dict = DialogueState.to_dict(dialogue_state)
        dialogue_state_json = json.dumps(dialogue_state_dict,ensure_ascii=False)

        insert_stmt = insert(DialogueRecord).values(sender_id=sender_id, state_json=dialogue_state_json)
        update_stmt = insert_stmt.on_duplicate_key_update(state_json=insert_stmt.inserted.state_json)

        await self.session.execute(update_stmt)

        await self.session.commit()




