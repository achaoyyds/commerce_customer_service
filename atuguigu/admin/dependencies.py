"""运营后台依赖注入：会话 + 当前登录用户。

复用 infra 层的 session_factory，通过 Bearer token 解析当前后台用户。
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from atuguigu.admin.cfg_repository import CfgFlowRepository, CfgReleaseRepository, CfgSlotRepository
from atuguigu.admin.kb_repository import KbCategoryRepository, KbFaqRepository
from atuguigu.admin.repository import SysUserRepository
from atuguigu.admin.schemas import CurrentUser
from atuguigu.admin.security import decode_access_token
from atuguigu.admin.services import FlowConfigService
from atuguigu.infrastructure import db_client

# Bearer token 提取器（不自动抛 403，便于自定义错误信息）
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_session():
    async with db_client.session_factory() as session:
        yield session


AdminSessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_current_user(
    session: AdminSessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(
        user_id=int(payload["sub"]),
        user_no=payload["user_no"],
        user_type=payload["user_type"],
        display_name=payload.get("display_name", payload["user_no"]),
    )


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(allowed_roles: list[str]):
    """生成基于角色的访问控制依赖：用户类型不在白名单内则返回 403。"""

    def checker(current_user: CurrentUserDep) -> CurrentUser:
        if current_user.user_type not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return current_user

    return checker


# admin：全部权限；operator：可维护槽位/流程/发布
AdminUserDep = Annotated[CurrentUser, Depends(require_roles(["admin"]))]
OperatorUserDep = Annotated[CurrentUser, Depends(require_roles(["admin", "operator"]))]


def get_sys_user_repository(session: AdminSessionDep) -> SysUserRepository:
    return SysUserRepository(session)


SysUserRepositoryDep = Annotated[SysUserRepository, Depends(get_sys_user_repository)]


def get_kb_category_repository(session: AdminSessionDep) -> KbCategoryRepository:
    return KbCategoryRepository(session)


KbCategoryRepositoryDep = Annotated[KbCategoryRepository, Depends(get_kb_category_repository)]


def get_kb_faq_repository(session: AdminSessionDep) -> KbFaqRepository:
    return KbFaqRepository(session)


KbFaqRepositoryDep = Annotated[KbFaqRepository, Depends(get_kb_faq_repository)]


def get_cfg_slot_repository(session: AdminSessionDep) -> CfgSlotRepository:
    return CfgSlotRepository(session)


CfgSlotRepositoryDep = Annotated[CfgSlotRepository, Depends(get_cfg_slot_repository)]


def get_cfg_flow_repository(session: AdminSessionDep) -> CfgFlowRepository:
    return CfgFlowRepository(session)


CfgFlowRepositoryDep = Annotated[CfgFlowRepository, Depends(get_cfg_flow_repository)]


def get_cfg_release_repository(session: AdminSessionDep) -> CfgReleaseRepository:
    return CfgReleaseRepository(session)


CfgReleaseRepositoryDep = Annotated[CfgReleaseRepository, Depends(get_cfg_release_repository)]


def get_flow_config_service(
    session: AdminSessionDep,
    flow_repo: CfgFlowRepositoryDep,
    release_repo: CfgReleaseRepositoryDep,
) -> FlowConfigService:
    return FlowConfigService(session, flow_repo, release_repo)


FlowConfigServiceDep = Annotated[FlowConfigService, Depends(get_flow_config_service)]