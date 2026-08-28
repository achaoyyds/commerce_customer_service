"""可观测性数据访问层：拆历史消息 + 轮次 trace + 会话汇总的落库与查询。"""
from datetime import date, datetime, timedelta
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.dialects.mysql import insert as mysql_insert

from atuguigu.domain.state import DialogueState
from atuguigu.observability.models import DialogueMessage, DialogueSession, DialogueTurn
from atuguigu.observability.trace import TurnTrace


def _to_datetime(timestamp: float | None) -> datetime | None:
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp)


class ObservabilityRepository:
    def __init__(self, session):
        self._session = session

    # ---------------- 落库 ----------------

    async def persist_turn(self, state: DialogueState, trace: TurnTrace) -> None:
        """把一轮对话拆成 message 明细 + turn trace，并 upsert 会话汇总。"""
        session = state.current_session()

        if session is not None:
            turn = session.turns[-1] if session.turns else None
            if turn is not None:
                # 用户消息行
                self._session.add(self._user_message_row(trace, turn.user_message))
                # 机器人回复行（可多条）
                for bot_message in turn.bot_messages:
                    self._session.add(self._bot_message_row(trace, bot_message))

        # 轮次 trace
        self._session.add(
            DialogueTurn(
                sender_id=trace.sender_id,
                session_id=trace.session_id,
                turn_id=trace.turn_id,
                message_id=trace.message_id,
                track=trace.track or "chitchat",
                flow_id=trace.flow_id,
                clarify_reason=trace.clarify_reason,
                user_text=trace.user_text,
                bot_text=trace.bot_text,
                latency_ms=trace.latency_ms,
                prompt_tokens=trace.prompt_tokens,
                completion_tokens=trace.completion_tokens,
                total_tokens=trace.total_tokens,
            )
        )

        # 会话汇总 upsert
        await self._upsert_session(state, session)

        await self._session.commit()

    def _user_message_row(self, trace: TurnTrace, user_message):
        return DialogueMessage(
            sender_id=trace.sender_id,
            session_id=trace.session_id,
            turn_id=trace.turn_id,
            message_id=user_message.message_id,
            role="user",
            msg_type=user_message.type.value if user_message and user_message.type else "text",
            text=user_message.text if user_message else None,
            object_id=(user_message.object.id if user_message and user_message.object else None),
            object_type=(user_message.object.type if user_message and user_message.object else None),
            object_title=(user_message.object.title if user_message and user_message.object else None),
            object_attrs=(user_message.object.attributes if user_message and user_message.object else None),
        )

    def _bot_message_row(self, trace: TurnTrace, bot_message):
        return DialogueMessage(
            sender_id=trace.sender_id,
            session_id=trace.session_id,
            turn_id=trace.turn_id,
            message_id=str(uuid4().hex),
            role="bot",
            msg_type="object" if bot_message.object is not None else "text",
            text=bot_message.text,
            object_id=bot_message.object.id if bot_message.object else None,
            object_type=bot_message.object.type if bot_message.object else None,
            object_title=bot_message.object.title if bot_message.object else None,
            object_attrs=bot_message.object.attributes if bot_message.object else None,
        )

    async def _upsert_session(self, state: DialogueState, session) -> None:
        if session is None:
            return
        turn_count = len(session.turns)
        message_count = sum(1 + len(turn.bot_messages) for turn in session.turns)
        now = datetime.now()

        stmt = mysql_insert(DialogueSession).values(
            sender_id=state.sender_id,
            session_id=session.session_id,
            started_at=_to_datetime(session.started_at) or now,
            last_active_at=now,
            closed_at=_to_datetime(session.closed_at),
            turn_count=turn_count,
            message_count=message_count,
        )
        stmt = stmt.on_duplicate_key_update(
            last_active_at=now,
            closed_at=stmt.inserted.closed_at,
            turn_count=turn_count,
            message_count=message_count,
        )
        await self._session.execute(stmt)

    # ---------------- 查询（看板） ----------------

    async def _scalar(self, sql: str, params: dict | None = None):
        cursor = await self._session.execute(text(sql), params or {})
        return cursor.scalar() or 0

    async def _group(self, sql: str) -> list[dict]:
        cursor = await self._session.execute(text(sql))
        return [{"name": row["name"], "value": int(row["value"])} for row in cursor.mappings().fetchall()]

    async def overview(self) -> dict:
        total_sessions = await self._scalar("SELECT COUNT(*) FROM dialogue_session")
        total_turns = await self._scalar("SELECT COUNT(*) FROM dialogue_turn")
        total_messages = await self._scalar("SELECT COUNT(*) FROM dialogue_message")
        total_tokens = await self._scalar("SELECT COALESCE(SUM(total_tokens),0) FROM dialogue_turn")
        avg_latency = await self._scalar("SELECT COALESCE(ROUND(AVG(latency_ms)),0) FROM dialogue_turn")

        track_dist = await self._group(
            "SELECT track AS name, COUNT(*) AS value FROM dialogue_turn GROUP BY track ORDER BY value DESC"
        )
        flow_dist = await self._group(
            "SELECT IFNULL(flow_id,'-') AS name, COUNT(*) AS value FROM dialogue_turn "
            "WHERE track='task' OR track='object' GROUP BY flow_id ORDER BY value DESC"
        )
        daily_trend = await self._daily_trend()

        return {
            "total_sessions": int(total_sessions),
            "total_turns": int(total_turns),
            "total_messages": int(total_messages),
            "total_tokens": int(total_tokens),
            "avg_latency_ms": int(avg_latency),
            "track_distribution": track_dist,
            "flow_distribution": flow_dist,
            "daily_trend": daily_trend,
        }

    async def _daily_trend(self) -> list[dict]:
        sql = (
            "SELECT DATE(created_at) AS day, COUNT(*) AS cnt FROM dialogue_turn "
            "WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY) GROUP BY DATE(created_at)"
        )
        cursor = await self._session.execute(text(sql))
        rows = {str(row["day"]): int(row["cnt"]) for row in cursor.mappings().fetchall()}
        result = []
        for offset in range(6, -1, -1):
            day = date.today() - timedelta(days=offset)
            result.append({"day": day.isoformat(), "count": rows.get(day.isoformat(), 0)})
        return result

    async def list_turns(
        self,
        offset: int = 0,
        limit: int = 20,
        track: str | None = None,
        flow_id: str | None = None,
        sender_id: str | None = None,
    ) -> dict:
        clauses: list[str] = []
        params: dict = {}
        if track:
            clauses.append("track = :track")
            params["track"] = track
        if flow_id:
            clauses.append("flow_id = :flow_id")
            params["flow_id"] = flow_id
        if sender_id:
            clauses.append("sender_id = :sender_id")
            params["sender_id"] = sender_id
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        total = await self._scalar(f"SELECT COUNT(*) FROM dialogue_turn {where_sql}", params)

        list_params = dict(params)
        list_params["limit"] = limit
        list_params["offset"] = offset
        sql = (
            f"SELECT id, sender_id, session_id, turn_id, track, flow_id, clarify_reason, "
            f"user_text, bot_text, latency_ms, prompt_tokens, completion_tokens, total_tokens, created_at "
            f"FROM dialogue_turn {where_sql} ORDER BY created_at DESC, id DESC LIMIT :limit OFFSET :offset"
        )
        cursor = await self._session.execute(text(sql), list_params)
        items = [dict(row) for row in cursor.mappings().fetchall()]
        return {"total": int(total), "items": items}

    async def list_messages(
        self,
        offset: int = 0,
        limit: int = 50,
        sender_id: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        clauses: list[str] = []
        params: dict = {}
        if sender_id:
            clauses.append("sender_id = :sender_id")
            params["sender_id"] = sender_id
        if session_id:
            clauses.append("session_id = :session_id")
            params["session_id"] = session_id
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        total = await self._scalar(f"SELECT COUNT(*) FROM dialogue_message {where_sql}", params)

        list_params = dict(params)
        list_params["limit"] = limit
        list_params["offset"] = offset
        sql = (
            f"SELECT sender_id, session_id, turn_id, message_id, role, msg_type, text, "
            f"object_id, object_type, object_title, created_at "
            f"FROM dialogue_message {where_sql} ORDER BY created_at DESC, id DESC LIMIT :limit OFFSET :offset"
        )
        cursor = await self._session.execute(text(sql), list_params)
        items = [dict(row) for row in cursor.mappings().fetchall()]
        return {"total": int(total), "items": items}

    async def list_sessions(
        self,
        offset: int = 0,
        limit: int = 20,
        sender_id: str | None = None,
    ) -> dict:
        clauses: list[str] = []
        params: dict = {}
        if sender_id:
            clauses.append("sender_id = :sender_id")
            params["sender_id"] = sender_id
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        total = await self._scalar(f"SELECT COUNT(*) FROM dialogue_session {where_sql}", params)

        list_params = dict(params)
        list_params["limit"] = limit
        list_params["offset"] = offset
        sql = (
            f"SELECT sender_id, session_id, started_at, last_active_at, closed_at, turn_count, message_count "
            f"FROM dialogue_session {where_sql} ORDER BY last_active_at DESC, id DESC LIMIT :limit OFFSET :offset"
        )
        cursor = await self._session.execute(text(sql), list_params)
        items = [dict(row) for row in cursor.mappings().fetchall()]
        return {"total": int(total), "items": items}