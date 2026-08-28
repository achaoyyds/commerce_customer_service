"""看板 API：概览统计 + 轮次 trace / 消息明细 / 会话列表查询。

复用在运营后台的 JWT 鉴权（任何已登录后台用户均可查看）。
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from atuguigu.admin.dependencies import AdminSessionDep, CurrentUserDep
from atuguigu.observability.repository import ObservabilityRepository

router = APIRouter(prefix="/api/admin/dashboard", tags=["dashboard"])


def get_observability_repository(session: AdminSessionDep) -> ObservabilityRepository:
    return ObservabilityRepository(session)


ObservabilityRepositoryDep = Annotated[ObservabilityRepository, Depends(get_observability_repository)]


@router.get("/overview")
async def overview(repo: ObservabilityRepositoryDep, current_user: CurrentUserDep):
    return await repo.overview()


@router.get("/turns")
async def list_turns(
    repo: ObservabilityRepositoryDep,
    current_user: CurrentUserDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    track: str | None = Query(default=None),
    flow_id: str | None = Query(default=None),
    sender_id: str | None = Query(default=None),
):
    return await repo.list_turns(offset=offset, limit=limit, track=track, flow_id=flow_id, sender_id=sender_id)


@router.get("/messages")
async def list_messages(
    repo: ObservabilityRepositoryDep,
    current_user: CurrentUserDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    sender_id: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
):
    return await repo.list_messages(offset=offset, limit=limit, sender_id=sender_id, session_id=session_id)


@router.get("/sessions")
async def list_sessions(
    repo: ObservabilityRepositoryDep,
    current_user: CurrentUserDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    sender_id: str | None = Query(default=None),
):
    return await repo.list_sessions(offset=offset, limit=limit, sender_id=sender_id)