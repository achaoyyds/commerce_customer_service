"""运营后台业务逻辑层。

核心职责：
1. 流程整体读写（flow + steps + links 在一个事务内替换）
2. 发布：把当前所有流程配置序列化成 FlowList 等价结构，写入 cfg_release 快照
3. 回滚：把指定历史快照重新标记为最新发布
"""
import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from atuguigu.admin.cfg_repository import CfgFlowRepository, CfgReleaseRepository
from atuguigu.admin.models import CfgFlowLink, CfgFlowStep, CfgRelease


def _gen_no(prefix: str) -> str:
    """生成业务编号：前缀 + 时间戳（到毫秒）+ 随机后缀。"""
    import uuid

    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    return f"{prefix}{ts}{uuid.uuid4().hex[:4].upper()}"


def _step_row_to_dict(step: CfgFlowStep, links_by_from: dict[str, list[CfgFlowLink]]) -> dict[str, Any]:
    """把单个步骤行 + 其出边，还原为 YAML 等价结构中的一个 step 字典。"""
    step_dict: dict[str, Any] = {
        "id": step.step_code,
        "type": step.step_type,
    }

    if step.step_type == "action":
        step_dict["action"] = step.action_name
        if step.args_json is not None:
            step_dict["args"] = step.args_json
    elif step.step_type == "collect":
        step_dict["slot_name"] = step.slot_code
        response: dict[str, Any] = {"text": step.response_text or ""}
        if step.response_mode:
            response["mode"] = step.response_mode
        if step.response_prompt:
            response["prompt"] = step.response_prompt
        step_dict["response"] = response
        if step.validate_condition:
            validate: dict[str, Any] = {"condition": step.validate_condition}
            if step.validate_fail_text:
                validate["failure_response"] = {"text": step.validate_fail_text}
            step_dict["validate"] = validate

    step_dict["next"] = _links_to_next(links_by_from.get(step.step_code, []))
    return step_dict


def _links_to_next(links: list[CfgFlowLink]):
    """把若干出边还原为 next 字段（字符串 / 条件列表 / 空列表）。"""
    if not links:
        return []

    # 只有一条 static 边时，还原为字符串
    if len(links) == 1 and links[0].link_type == "static":
        return links[0].to_step_code

    next_value: list[dict[str, str]] = []
    for link in sorted(links, key=lambda l: l.sort_no):
        if link.link_type == "condition":
            next_value.append({"if": link.condition_expr, "then": link.to_step_code})
        else:  # fallback（else）
            next_value.append({"else": link.to_step_code})
    return next_value


class FlowConfigService:
    """流程配置领域服务。"""

    def __init__(
        self,
        session: AsyncSession,
        flow_repo: CfgFlowRepository,
        release_repo: CfgReleaseRepository,
    ):
        self._session = session
        self._flow_repo = flow_repo
        self._release_repo = release_repo

    # ---------- 发布快照 ----------

    async def build_snapshot(self) -> dict[str, Any]:
        """把全量 flow + steps + links + slots 序列化为 FlowList 等价 dict。"""
        from atuguigu.admin.cfg_repository import CfgSlotRepository

        flows = await self._flow_repo.list_all()
        slots = await CfgSlotRepository(self._session).list_all()

        flows_dict: dict[str, dict[str, Any]] = {}
        for flow in flows:
            steps = await self._flow_repo.get_steps(flow.id)
            links = await self._flow_repo.get_links(flow.id)

            links_by_from: dict[str, list[CfgFlowLink]] = {}
            for link in links:
                links_by_from.setdefault(link.from_step_code, []).append(link)

            flows_dict[flow.flow_code] = {
                "name": flow.flow_name,
                "description": flow.description,
                "steps": [_step_row_to_dict(s, links_by_from) for s in steps],
            }

        slots_dict = {
            slot.slot_code: {
                "type": slot.slot_type,
                "label": slot.slot_name,
                "description": slot.description,
            }
            for slot in slots
        }

        return {"flows": flows_dict, "slots": slots_dict}

    async def publish(
        self,
        release_type: str,
        target_code: str,
        published_by: int,
        remark: str | None,
    ) -> CfgRelease:
        """发布：生成全量快照并写入 cfg_release，同时把旧 published 置为 rolled_back。"""
        snapshot = await self.build_snapshot()

        # 先取当前最新已发布（版本号在其上递增），再将旧 published 全部置为 rolled_back
        latest = await self._release_repo.get_latest_published(release_type, target_code)
        next_version = (latest.version + 1) if latest else 1

        old_releases = await self._release_repo.list_all(release_type=release_type, limit=100)
        for old in old_releases:
            if old.status == "published":
                old.status = "rolled_back"

        release = CfgRelease(
            release_no=_gen_no("REL"),
            release_type=release_type,
            target_code=target_code,
            version=next_version,
            snapshot_json=json.dumps(snapshot, ensure_ascii=False),
            status="published",
            published_by=published_by,
            published_at=datetime.now(),
            remark=remark,
        )
        self._session.add(release)
        await self._session.commit()
        await self._session.refresh(release)
        return release

    async def rollback(self, release_no: str, published_by: int, remark: str | None) -> CfgRelease:
        """回滚：以历史快照为内容，生成一条新的 published 记录。"""
        target = await self._release_repo.get_by_release_no(release_no)
        if target is None:
            raise ValueError(f"发布记录不存在：{release_no}")

        # 先取当前最新已发布（回滚后版本号在其上递增），再将旧 published 置为 rolled_back
        latest = await self._release_repo.get_latest_published(target.release_type, target.target_code)
        next_version = (latest.version + 1) if latest else target.version + 1

        old_releases = await self._release_repo.list_all(release_type=target.release_type, limit=100)
        for old in old_releases:
            if old.status == "published":
                old.status = "rolled_back"

        release = CfgRelease(
            release_no=_gen_no("REL"),
            release_type=target.release_type,
            target_code=target.target_code,
            version=next_version,
            snapshot_json=target.snapshot_json,  # 复用历史快照
            status="published",
            published_by=published_by,
            published_at=datetime.now(),
            remark=remark or f"回滚自 {release_no}",
        )
        self._session.add(release)
        await self._session.commit()
        await self._session.refresh(release)
        return release