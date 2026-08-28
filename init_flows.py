"""把 flow_config 下的 YAML 流程迁移到能力配置中心的数据库表。

用法：uv run init_flows.py

行为（整库重建，便于反复执行）：
1. 清空 cfg_slot / cfg_flow / cfg_flow_step / cfg_flow_link / cfg_release
2. 解析 system_flows.yml(系统流) / user_flows.yml(业务流) 写入对应表
3. 生成一版初始发布快照（release_type=flow, target_code=ALL）
"""
import asyncio
import sys
from pathlib import Path

import yaml
from sqlalchemy import delete

from atuguigu.admin.models import CfgFlow, CfgFlowLink, CfgFlowStep, CfgRelease, CfgSlot
from atuguigu.infrastructure import db_client

PROJECT_ROOT = Path(__file__).resolve().parent
FLOW_CONFIG_DIR = PROJECT_ROOT / "flow_config"
# 文件名 -> 流程类别（business 业务流 / system 系统流）
CONFIG_FILES = [
    ("system_flows.yml", "system"),
    ("user_flows.yml", "business"),
]


def _slot_rows(flow_dict: dict) -> list[CfgSlot]:
    rows: list[CfgSlot] = []
    for code, s in (flow_dict.get("slots") or {}).items():
        rows.append(
            CfgSlot(
                slot_code=code,
                slot_name=s.get("label") or code,
                slot_type=s.get("type", "text"),
                description=s.get("description", ""),
            )
        )
    return rows


def _parse_next(flow_id: int, from_code: str, next_value) -> list[CfgFlowLink]:
    """把步骤的 next 字段（str / 条件列表 / 空列表）转成连线行。"""
    links: list[CfgFlowLink] = []
    if isinstance(next_value, str):
        links.append(
            CfgFlowLink(
                flow_id=flow_id,
                from_step_code=from_code,
                link_type="static",
                to_step_code=next_value,
                sort_no=0,
            )
        )
    elif isinstance(next_value, list):
        for i, item in enumerate(next_value):
            if not isinstance(item, dict):
                continue
            if "if" in item:
                links.append(
                    CfgFlowLink(
                        flow_id=flow_id,
                        from_step_code=from_code,
                        link_type="condition",
                        condition_expr=item["if"],
                        to_step_code=item["then"],
                        sort_no=i,
                    )
                )
            elif "else" in item:
                links.append(
                    CfgFlowLink(
                        flow_id=flow_id,
                        from_step_code=from_code,
                        link_type="fallback",
                        to_step_code=item["else"],
                        sort_no=i,
                    )
                )
    return links


def _step_and_link_rows(flow_id: int, steps: list[dict]) -> tuple[list[CfgFlowStep], list[CfgFlowLink]]:
    step_rows: list[CfgFlowStep] = []
    link_rows: list[CfgFlowLink] = []
    for i, s in enumerate(steps):
        step_type = s.get("type")
        row = CfgFlowStep(flow_id=flow_id, step_code=s["id"], step_type=step_type, sort_no=i)

        if step_type == "action":
            row.action_name = s.get("action")
            row.args_json = s.get("args")  # dict 或字符串引用（如 context.response）
        elif step_type == "collect":
            row.slot_code = s.get("slot_name")
            response = s.get("response") or {}
            row.response_text = response.get("text")
            row.response_mode = response.get("mode")
            row.response_prompt = response.get("prompt")
            validate = s.get("validate") or {}
            row.validate_condition = validate.get("condition")
            fail_resp = validate.get("failure_response") or {}
            row.validate_fail_text = fail_resp.get("text")

        step_rows.append(row)
        link_rows.extend(_parse_next(flow_id, s["id"], s.get("next")))
    return step_rows, link_rows


async def _reset_tables(session) -> None:
    await session.execute(delete(CfgFlowLink))
    await session.execute(delete(CfgFlowStep))
    await session.execute(delete(CfgFlow))
    await session.execute(delete(CfgSlot))
    await session.execute(delete(CfgRelease))


async def main():
    db_client.init_db_engine()
    async with db_client.session_factory() as session:
        await _reset_tables(session)

        for filename, category in CONFIG_FILES:
            path = FLOW_CONFIG_DIR / filename
            flow_dict = yaml.safe_load(path.read_text(encoding="utf-8"))

            for slot in _slot_rows(flow_dict):
                session.add(slot)

            for flow_code, fd in (flow_dict.get("flows") or {}).items():
                flow = CfgFlow(
                    flow_code=flow_code,
                    flow_name=fd.get("name") or flow_code,
                    description=fd.get("description", ""),
                    flow_category=category,
                    status="published",  # 迁移即视为已生效
                    created_by=0,
                )
                session.add(flow)
                await session.flush()  # 拿到 flow.id
                step_rows, link_rows = _step_and_link_rows(flow.id, fd.get("steps") or [])
                session.add_all(step_rows)
                session.add_all(link_rows)

        await session.commit()
        print("流程与槽位已写入数据库。")

        # 生成初始发布快照
        from atuguigu.admin.cfg_repository import CfgFlowRepository, CfgReleaseRepository
        from atuguigu.admin.services import FlowConfigService

        svc = FlowConfigService(session, CfgFlowRepository(session), CfgReleaseRepository(session))
        release = await svc.publish("flow", "ALL", published_by=0, remark="初始化迁移自 YAML")
        print(f"已发布初始快照：{release.release_no} v{release.version}")

    await db_client.dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)