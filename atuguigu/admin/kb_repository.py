"""知识库数据访问层：分类 + FAQ。"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from atuguigu.admin.models import KbCategory, KbFaq


class KbCategoryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self) -> list[KbCategory]:
        stmt = select(KbCategory).where(KbCategory.yn == 1).order_by(KbCategory.sort_no)
        cursor = await self._session.execute(stmt)
        return list(cursor.scalars().all())

    async def get_by_id(self, category_id: int) -> KbCategory | None:
        stmt = select(KbCategory).where(KbCategory.id == category_id, KbCategory.yn == 1)
        cursor = await self._session.execute(stmt)
        return cursor.scalar_one_or_none()

    async def add(self, category: KbCategory) -> KbCategory:
        self._session.add(category)
        await self._session.commit()
        await self._session.refresh(category)
        return category


class KbFaqRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list(
        self,
        category_id: int | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[KbFaq], int]:
        where = []
        if category_id is not None:
            where.append(KbFaq.category_id == category_id)
        if status is not None:
            where.append(KbFaq.status == status)

        count_stmt = select(func.count()).select_from(KbFaq)
        if where:
            count_stmt = count_stmt.where(*where)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = select(KbFaq)
        if where:
            stmt = stmt.where(*where)
        stmt = stmt.order_by(KbFaq.sort_no, KbFaq.id).offset(offset).limit(limit)
        cursor = await self._session.execute(stmt)
        return list(cursor.scalars().all()), total

    async def get_by_id(self, faq_id: int) -> KbFaq | None:
        stmt = select(KbFaq).where(KbFaq.id == faq_id)
        cursor = await self._session.execute(stmt)
        return cursor.scalar_one_or_none()

    async def add(self, faq: KbFaq) -> KbFaq:
        self._session.add(faq)
        await self._session.commit()
        await self._session.refresh(faq)
        return faq

    async def delete(self, faq: KbFaq) -> None:
        await self._session.delete(faq)
        await self._session.commit()