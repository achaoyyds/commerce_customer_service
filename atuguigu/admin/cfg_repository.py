"""流程配置数据访问层：槽位 + 流程 + 步骤 + 连线 + 发布。"""
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from atuguigu.admin.models import (
    CfgFlow,
    CfgFlowLink,
    CfgFlowStep,
    CfgRelease,
    CfgSlot,
)


class CfgSlotRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self) -> list[CfgSlot]:
        stmt = select(CfgSlot).where(CfgSlot.yn == 1).order_by(CfgSlot.id)
        cursor = await self._session.execute(stmt)
        return list(cursor.scalars().all())

    async def get_by_id(self, slot_id: int) -> CfgSlot | None:
        stmt = select(CfgSlot).where(CfgSlot.id == slot_id, CfgSlot.yn == 1)
        cursor = await self._session.execute(stmt)
        return cursor.scalar_one_or_none()

    async def add(self, slot: CfgSlot) -> CfgSlot:
        self._session.add(slot)
        await self._session.commit()
        await self._session.refresh(slot)
        return slot


class CfgFlowRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, flow_category: str | None = None) -> list[CfgFlow]:
        stmt = select(CfgFlow)
        if flow_category is not None:
            stmt = stmt.where(CfgFlow.flow_category == flow_category)
        stmt = stmt.order_by(CfgFlow.id)
        cursor = await self._session.execute(stmt)
        return list(cursor.scalars().all())

    async def get_by_id(self, flow_id: int) -> CfgFlow | None:
        stmt = select(CfgFlow).where(CfgFlow.id == flow_id)
        cursor = await self._session.execute(stmt)
        return cursor.scalar_one_or_none()

    async def get_steps(self, flow_id: int) -> list[CfgFlowStep]:
        stmt = select(CfgFlowStep).where(CfgFlowStep.flow_id == flow_id).order_by(CfgFlowStep.sort_no)
        cursor = await self._session.execute(stmt)
        return list(cursor.scalars().all())

    async def get_links(self, flow_id: int) -> list[CfgFlowLink]:
        stmt = select(CfgFlowLink).where(CfgFlowLink.flow_id == flow_id).order_by(CfgFlowLink.sort_no)
        cursor = await self._session.execute(stmt)
        return list(cursor.scalars().all())

    async def add(self, flow: CfgFlow) -> CfgFlow:
        self._session.add(flow)
        await self._session.flush()
        return flow

    async def delete_steps(self, flow_id: int) -> None:
        await self._session.execute(delete(CfgFlowStep).where(CfgFlowStep.flow_id == flow_id))

    async def delete_links(self, flow_id: int) -> None:
        await self._session.execute(delete(CfgFlowLink).where(CfgFlowLink.flow_id == flow_id))


class CfgReleaseRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, release_type: str | None = None, limit: int = 50) -> list[CfgRelease]:
        stmt = select(CfgRelease)
        if release_type is not None:
            stmt = stmt.where(CfgRelease.release_type == release_type)
        stmt = stmt.order_by(CfgRelease.id.desc()).limit(limit)
        cursor = await self._session.execute(stmt)
        return list(cursor.scalars().all())

    async def get_by_release_no(self, release_no: str) -> CfgRelease | None:
        stmt = select(CfgRelease).where(CfgRelease.release_no == release_no)
        cursor = await self._session.execute(stmt)
        return cursor.scalar_one_or_none()

    async def get_latest_published(self, release_type: str, target_code: str = "ALL") -> CfgRelease | None:
        stmt = (
            select(CfgRelease)
            .where(
                CfgRelease.release_type == release_type,
                CfgRelease.target_code == target_code,
                CfgRelease.status == "published",
            )
            .order_by(CfgRelease.id.desc())
            .limit(1)
        )
        cursor = await self._session.execute(stmt)
        return cursor.scalar_one_or_none()

    async def add(self, release: CfgRelease) -> CfgRelease:
        self._session.add(release)
        await self._session.commit()
        await self._session.refresh(release)
        return release