"""运营后台认证路由：登录 + 当前用户。"""
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from atuguigu.admin.dependencies import AdminSessionDep, CurrentUserDep, SysUserRepositoryDep
from atuguigu.admin.schemas import CurrentUser, LoginRequest, LoginResponse, LoginUser
from atuguigu.admin.security import create_access_token, verify_password

router = APIRouter(prefix="/api/admin", tags=["admin-auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, repo: SysUserRepositoryDep, session: AdminSessionDep):
    user = await repo.get_by_user_no(request.user_no)
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    token = create_access_token(
        user_id=user.id,
        user_no=user.user_no,
        user_type=user.user_type,
        display_name=user.display_name,
    )

    # 更新最后登录时间
    user.last_login_at = datetime.now()
    await session.commit()

    return LoginResponse(
        access_token=token,
        user=LoginUser(
            user_id=user.id,
            user_no=user.user_no,
            username=user.username,
            display_name=user.display_name,
            user_type=user.user_type,
        ),
    )


@router.get("/me", response_model=CurrentUser)
async def me(current_user: CurrentUserDep):
    return current_user