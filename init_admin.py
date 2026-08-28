"""初始化运营后台管理员账号（幂等：已存在则跳过）。

用法：uv run init_admin.py
默认创建 admin / admin123（仅用于开发环境，生产务必修改）。
"""
import asyncio
import sys

from sqlalchemy import select

from atuguigu.admin.models import SysUser
from atuguigu.admin.security import hash_password
from atuguigu.infrastructure import db_client


async def main():
    db_client.init_db_engine()
    async with db_client.session_factory() as session:
        cursor = await session.execute(
            select(SysUser).where(SysUser.user_no == "admin")
        )
        exists = cursor.scalar_one_or_none()
        if exists is not None:
            print("admin 账号已存在，跳过。")
            return

        session.add(
            SysUser(
                user_no="admin",
                username="admin",
                password_hash=hash_password("admin123"),
                display_name="系统管理员",
                user_type="admin",
                status="active",
            )
        )
        await session.commit()
        print("已创建管理员账号 admin / admin123")

    await db_client.dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)