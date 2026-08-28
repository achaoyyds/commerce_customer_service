"""可观测性（看板）数据模型：拆历史消息 + 会话 + 轮次 trace。"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from atuguigu.repository.base import Base


class DialogueMessage(Base):
    __tablename__ = "dialogue_message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sender_id: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    turn_id: Mapped[str] = mapped_column(String(64), nullable=False)
    message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user/bot
    msg_type: Mapped[str] = mapped_column(String(16), nullable=False, default="text")  # text/object
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    object_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    object_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    object_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    object_attrs: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class DialogueSession(Base):
    __tablename__ = "dialogue_session"
    __table_args__ = (UniqueConstraint("session_id", name="uk_mon_session"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sender_id: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class DialogueTurn(Base):
    __tablename__ = "dialogue_turn"
    __table_args__ = (UniqueConstraint("turn_id", name="uk_mon_turn"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sender_id: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    turn_id: Mapped[str] = mapped_column(String(64), nullable=False)
    message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    track: Mapped[str] = mapped_column(String(32), nullable=False)  # task/knowledge/chitchat/clarify/object
    flow_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    clarify_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    bot_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prompt_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())