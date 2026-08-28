"""流程配置管理路由：槽位 + 流程（含步骤/连线）。"""
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Query, status

from atuguigu.admin.dependencies import (
    AdminSessionDep,
    CfgFlowRepositoryDep,
    CfgSlotRepositoryDep,
    CurrentUserDep,
    OperatorUserDep,
)
from atuguigu.admin.models import CfgFlow, CfgFlowLink, CfgFlowStep, CfgSlot
from atuguigu.admin.schemas import (
    FlowCreate,
    FlowDetailOut,
    FlowLinkIn,
    FlowLinkOut,
    FlowOut,
    FlowStepIn,
    FlowStepOut,
    FlowUpdate,
    SlotCreate,
    SlotOut,
    SlotUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin-flow-config"])


# ---------- 槽位 ----------

@router.get("/slots", response_model=list[SlotOut])
async def list_slots(repo: CfgSlotRepositoryDep, current_user: CurrentUserDep):
    return await repo.list_all()


@router.post("/slots", response_model=SlotOut, status_code=status.HTTP_201_CREATED)
async def create_slot(data: SlotCreate, repo: CfgSlotRepositoryDep, current_user: OperatorUserDep):
    slot = CfgSlot(
        slot_code=data.slot_code,
        slot_name=data.slot_name,
        slot_type=data.slot_type,
        description=data.description,
        validate_rule=data.validate_rule,
    )
    return await repo.add(slot)


@router.put("/slots/{slot_id}", response_model=SlotOut)
async def update_slot(
    slot_id: int,
    data: SlotUpdate,
    repo: CfgSlotRepositoryDep,
    session: AdminSessionDep,
    current_user: OperatorUserDep,
):
    slot = await repo.get_by_id(slot_id)
    if slot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="槽位不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(slot, field, value)
    await session.commit()
    await session.refresh(slot)
    return slot


@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(
    slot_id: int,
    repo: CfgSlotRepositoryDep,
    session: AdminSessionDep,
    current_user: OperatorUserDep,
):
    slot = await repo.get_by_id(slot_id)
    if slot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="槽位不存在")
    slot.yn = 0  # 软删除
    await session.commit()


# ---------- 流程 ----------

@router.get("/flows", response_model=list[FlowOut])
async def list_flows(
    repo: CfgFlowRepositoryDep,
    current_user: CurrentUserDep,
    category: str | None = Query(default=None),
):
    return await repo.list_all(flow_category=category)


async def _load_flow_detail(flow_id: int, repo: CfgFlowRepositoryDep) -> FlowDetailOut | None:
    """读取单个流程完整结构（供路由与内部 create/update 复用）。"""
    flow = await repo.get_by_id(flow_id)
    if flow is None:
        return None
    steps = await repo.get_steps(flow_id)
    links = await repo.get_links(flow_id)
    return FlowDetailOut(
        **FlowOut.model_validate(flow).model_dump(),
        steps=[FlowStepOut.model_validate(s).model_dump() for s in steps],
        links=[FlowLinkOut.model_validate(l).model_dump() for l in links],
    )


@router.get("/flows/{flow_id}", response_model=FlowDetailOut)
async def get_flow(flow_id: int, repo: CfgFlowRepositoryDep, current_user: CurrentUserDep):
    detail = await _load_flow_detail(flow_id, repo)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="流程不存在")
    return detail


def _build_steps_and_links(flow_id: int, steps: list[FlowStepIn], links: list[FlowLinkIn]):
    """根据请求体构造步骤与连线 ORM 对象列表。"""
    step_rows = [
        CfgFlowStep(
            flow_id=flow_id,
            step_code=s.step_code,
            step_type=s.step_type,
            sort_no=s.sort_no,
            action_name=s.action_name,
            args_json=s.args_json,
            slot_code=s.slot_code,
            response_mode=s.response_mode,
            response_text=s.response_text,
            response_prompt=s.response_prompt,
            validate_condition=s.validate_condition,
            validate_fail_text=s.validate_fail_text,
            pos_x=s.pos_x,
            pos_y=s.pos_y,
        )
        for s in steps
    ]
    link_rows = [
        CfgFlowLink(
            flow_id=flow_id,
            from_step_code=l.from_step_code,
            link_type=l.link_type,
            condition_expr=l.condition_expr,
            to_step_code=l.to_step_code,
            sort_no=l.sort_no,
        )
        for l in links
    ]
    return step_rows, link_rows


@router.post("/flows", response_model=FlowDetailOut, status_code=status.HTTP_201_CREATED)
async def create_flow(
    data: FlowCreate,
    repo: CfgFlowRepositoryDep,
    session: AdminSessionDep,
    current_user: OperatorUserDep,
):
    flow = CfgFlow(
        flow_code=data.flow_code,
        flow_name=data.flow_name,
        description=data.description,
        flow_category=data.flow_category,
        created_by=current_user.user_id,
    )
    flow = await repo.add(flow)  # flush 后拿到 flow.id
    steps, links = _build_steps_and_links(flow.id, data.steps, data.links)
    session.add_all(steps)
    session.add_all(links)
    await session.commit()
    return await _load_flow_detail(flow.id, repo)


@router.put("/flows/{flow_id}", response_model=FlowDetailOut)
async def update_flow(
    flow_id: int,
    data: FlowUpdate,
    repo: CfgFlowRepositoryDep,
    session: AdminSessionDep,
    current_user: OperatorUserDep,
):
    flow = await repo.get_by_id(flow_id)
    if flow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="流程不存在")

    # 更新标量字段
    for field, value in data.model_dump(exclude_unset=True).items():
        if field in ("steps", "links"):
            continue
        setattr(flow, field, value)

    # 若显式传了 steps 或 links，则整体替换（缺失一侧视为清空）
    if "steps" in data.model_fields_set or "links" in data.model_fields_set:
        await repo.delete_steps(flow_id)
        await repo.delete_links(flow_id)
        steps, links = _build_steps_and_links(flow_id, data.steps or [], data.links or [])
        session.add_all(steps)
        session.add_all(links)

    await session.commit()
    return await _load_flow_detail(flow_id, repo)


@router.delete("/flows/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flow(
    flow_id: int,
    repo: CfgFlowRepositoryDep,
    session: AdminSessionDep,
    current_user: OperatorUserDep,
):
    flow = await repo.get_by_id(flow_id)
    if flow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="流程不存在")
    await repo.delete_steps(flow_id)
    await repo.delete_links(flow_id)
    await session.delete(flow)
    await session.commit()