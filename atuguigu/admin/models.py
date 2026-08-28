"""
运营后台（能力配置中心）数据模型
对应 sql/admin_tables.sql 中的 8 张表：sys_user / kb_category / kb_faq /
cfg_slot / cfg_flow / cfg_flow_step / cfg_flow_link / cfg_release
"""
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, Double, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from atuguigu.repository.base import Base


class SysUser(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_no: Mapped[str] = mapped_column(String(64), nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    user_type: Mapped[str] = mapped_column(String(16), nullable=False)  # admin/operator/agent
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class KbCategory(Base):
    __tablename__ = "kb_category"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_code: Mapped[str] = mapped_column(String(64), nullable=False)
    category_name: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    yn: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class KbFaq(Base):
    __tablename__ = "kb_faq"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    faq_no: Mapped[str] = mapped_column(String(64), nullable=False)
    category_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    question: Mapped[str] = mapped_column(String(255), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hit_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CfgSlot(Base):
    __tablename__ = "cfg_slot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slot_code: Mapped[str] = mapped_column(String(64), nullable=False)
    slot_name: Mapped[str] = mapped_column(String(64), nullable=False)
    slot_type: Mapped[str] = mapped_column(String(16), nullable=False, default="text")
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    validate_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    yn: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CfgFlow(Base):
    __tablename__ = "cfg_flow"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    flow_code: Mapped[str] = mapped_column(String(64), nullable=False)
    flow_name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    flow_category: Mapped[str] = mapped_column(String(16), nullable=False, default="business")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CfgFlowStep(Base):
    __tablename__ = "cfg_flow_step"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    flow_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    step_code: Mapped[str] = mapped_column(String(64), nullable=False)
    step_type: Mapped[str] = mapped_column(String(16), nullable=False)  # start/end/action/collect
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    action_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    args_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    slot_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response_mode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    validate_condition: Mapped[str | None] = mapped_column(String(255), nullable=True)
    validate_fail_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    pos_x: Mapped[float | None] = mapped_column(Double, nullable=True)
    pos_y: Mapped[float | None] = mapped_column(Double, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CfgFlowLink(Base):
    __tablename__ = "cfg_flow_link"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    flow_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_step_code: Mapped[str] = mapped_column(String(64), nullable=False)
    link_type: Mapped[str] = mapped_column(String(16), nullable=False)  # static/condition/fallback
    condition_expr: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_step_code: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CfgRelease(Base):
    __tablename__ = "cfg_release"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    release_no: Mapped[str] = mapped_column(String(64), nullable=False)
    release_type: Mapped[str] = mapped_column(String(16), nullable=False)  # flow/intent/faq/knowledge/full
    target_code: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="published")
    published_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())