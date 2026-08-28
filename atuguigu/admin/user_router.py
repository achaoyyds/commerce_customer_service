"""运营后台用户管理路由（三级 RBAC：仅 admin 可操作）。"""
from fastapi import APIRouter, HTTPException, Query, status

from atuguigu.admin.dependencies import AdminSessionDep, AdminUserDep, SysUserRepositoryDep
from atuguigu.admin.models import SysUser
from atuguigu.admin.schemas import PasswordReset, UserCreate, UserOut, UserUpdate
from atuguigu.admin.security import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin-user"])


@router.get("/users")
async def list_users(
    repo: SysUserRepositoryDep,
    current_user: AdminUserDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    items, total = await repo.list(offset=offset, limit=limit)
    return {"total": total, "items": [UserOut.model_validate(u).model_dump() for u in items]}


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, repo: SysUserRepositoryDep, current_user: AdminUserDep):
    if await repo.get_by_user_no(data.user_no):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="工号已存在")
    if await repo.get_by_username(data.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")

    user = SysUser(
        user_no=data.user_no,
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        user_type=data.user_type,
        status=data.status,
    )
    return await repo.add(user)


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    data: UserUpdate,
    repo: SysUserRepositoryDep,
    session: AdminSessionDep,
    current_user: AdminUserDep,
):
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "username" and value is not None:
            existed = await repo.get_by_username(value)
            if existed is not None and existed.id != user_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user


@router.put("/users/{user_id}/password", response_model=UserOut)
async def reset_password(
    user_id: int,
    data: PasswordReset,
    repo: SysUserRepositoryDep,
    session: AdminSessionDep,
    current_user: AdminUserDep,
):
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    user.password_hash = hash_password(data.password)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    repo: SysUserRepositoryDep,
    session: AdminSessionDep,
    current_user: AdminUserDep,
):
    if user_id == current_user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除当前登录账号")

    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    await session.delete(user)
    await session.commit()