"""流程配置发布 / 回滚路由。"""
from fastapi import APIRouter, HTTPException, Query, status

from atuguigu.admin.dependencies import (
    CfgReleaseRepositoryDep,
    CurrentUserDep,
    FlowConfigServiceDep,
    OperatorUserDep,
)
from atuguigu.admin.schemas import ReleaseCreate, ReleaseOut

router = APIRouter(prefix="/api/admin", tags=["admin-release"])


@router.get("/releases", response_model=list[ReleaseOut])
async def list_releases(
    repo: CfgReleaseRepositoryDep,
    current_user: CurrentUserDep,
    release_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    return await repo.list_all(release_type=release_type, limit=limit)


@router.get("/releases/{release_no}", response_model=ReleaseOut)
async def get_release(release_no: str, repo: CfgReleaseRepositoryDep, current_user: CurrentUserDep):
    release = await repo.get_by_release_no(release_no)
    if release is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发布记录不存在")
    return release


@router.post("/releases", response_model=ReleaseOut, status_code=status.HTTP_201_CREATED)
async def publish(
    data: ReleaseCreate,
    service: FlowConfigServiceDep,
    current_user: OperatorUserDep,
):
    return await service.publish(
        release_type=data.release_type,
        target_code=data.target_code,
        published_by=current_user.user_id,
        remark=data.remark,
    )


@router.post("/releases/{release_no}/rollback", response_model=ReleaseOut)
async def rollback(
    release_no: str,
    service: FlowConfigServiceDep,
    current_user: OperatorUserDep,
):
    try:
        return await service.rollback(release_no, current_user.user_id, None)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))