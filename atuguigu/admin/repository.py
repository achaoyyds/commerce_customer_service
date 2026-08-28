"""运营后台数据访问层。"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from atuguigu.admin.models import SysUser


class SysUserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_user_no(self, user_no: str) -> SysUser | None:
        stmt = select(SysUser).where(SysUser.user_no == user_no)
        cursor = await self._session.execute(stmt)
        return cursor.scalar_one_or_none()

    async def get_by_username(self, username: str) -> SysUser | None:
        stmt = select(SysUser).where(SysUser.username == username)
        cursor = await self._session.execute(stmt)
        return cursor.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> SysUser | None:
        stmt = select(SysUser).where(SysUser.id == user_id)
        cursor = await self._session.execute(stmt)
        return cursor.scalar_one_or_none()

    async def list(self, offset: int = 0, limit: int = 20) -> tuple[list[SysUser], int]:
        count_stmt = select(func.count()).select_from(SysUser)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = select(SysUser).order_by(SysUser.id).offset(offset).limit(limit)
        cursor = await self._session.execute(stmt)
        return list(cursor.scalars().all()), total

    async def add(self, user: SysUser) -> SysUser:
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user