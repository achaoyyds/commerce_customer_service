"""运营后台认证安全工具：密码哈希 + JWT 签发/校验。

- 密码：bcrypt 哈希
- Token：PyJWT（HS256），payload 内含 user_id / user_no / user_type
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from atuguigu.config.settings import settings


def hash_password(plain_password: str) -> str:
    """bcrypt 哈希密码。"""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int, user_no: str, user_type: str, display_name: str) -> str:
    """签发 JWT，有效期由 settings.jwt_expire_minutes 决定。"""
    now = datetime.now(timezone.utc)
    expire_at = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "user_no": user_no,
        "user_type": user_type,
        "display_name": display_name,
        "iat": now,
        "exp": expire_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """校验并解析 JWT，非法/过期时抛出 jwt 相关异常。"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])