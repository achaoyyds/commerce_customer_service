"""运营后台接口数据模型（Pydantic）。"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------- 认证 ----------

class LoginRequest(BaseModel):
    user_no: str
    password: str


class LoginUser(BaseModel):
    user_id: int
    user_no: str
    username: str
    display_name: str
    user_type: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: LoginUser


class CurrentUser(BaseModel):
    user_id: int
    user_no: str
    user_type: str
    display_name: str


# ---------- 用户管理 ----------

class UserCreate(BaseModel):
    user_no: str
    username: str
    password: str
    display_name: str
    user_type: str = "agent"  # admin/operator/agent
    status: str = "active"  # active/disabled


class UserUpdate(BaseModel):
    username: str | None = None
    display_name: str | None = None
    user_type: str | None = None
    status: str | None = None


class PasswordReset(BaseModel):
    password: str


class UserOut(BaseModel):
    id: int
    user_no: str
    username: str
    display_name: str
    user_type: str
    status: str
    last_login_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 知识分类 ----------

class CategoryCreate(BaseModel):
    category_code: str
    category_name: str
    parent_id: int | None = None
    sort_no: int = 0


class CategoryUpdate(BaseModel):
    category_code: str | None = None
    category_name: str | None = None
    parent_id: int | None = None
    sort_no: int | None = None


class CategoryOut(BaseModel):
    id: int
    category_code: str
    category_name: str
    parent_id: int | None
    sort_no: int

    class Config:
        from_attributes = True


# ---------- FAQ ----------

class FaqCreate(BaseModel):
    category_id: int
    question: str
    answer: str
    keywords: list[str] = Field(default_factory=list)
    sort_no: int = 0


class FaqUpdate(BaseModel):
    category_id: int | None = None
    question: str | None = None
    answer: str | None = None
    keywords: list[str] | None = None
    sort_no: int | None = None


class FaqStatusUpdate(BaseModel):
    status: str  # draft/published/offline


class FaqOut(BaseModel):
    id: int
    faq_no: str
    category_id: int
    question: str
    answer: str
    keywords: list[str] | None
    status: str
    sort_no: int
    hit_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 槽位 ----------

class SlotCreate(BaseModel):
    slot_code: str
    slot_name: str
    slot_type: str = "text"
    description: str
    validate_rule: str | None = None


class SlotUpdate(BaseModel):
    slot_code: str | None = None
    slot_name: str | None = None
    slot_type: str | None = None
    description: str | None = None
    validate_rule: str | None = None


class SlotOut(BaseModel):
    id: int
    slot_code: str
    slot_name: str
    slot_type: str
    description: str
    validate_rule: str | None

    class Config:
        from_attributes = True


# ---------- 流程 ----------

class FlowStepIn(BaseModel):
    step_code: str
    step_type: str  # start/end/action/collect
    sort_no: int = 0
    action_name: str | None = None
    args_json: Any | None = None  # dict 或 str（如 context.response）
    slot_code: str | None = None
    response_mode: str | None = None
    response_text: str | None = None
    response_prompt: str | None = None
    validate_condition: str | None = None
    validate_fail_text: str | None = None
    pos_x: float | None = None
    pos_y: float | None = None


class FlowLinkIn(BaseModel):
    from_step_code: str
    link_type: str  # static/condition/fallback
    condition_expr: str | None = None
    to_step_code: str
    sort_no: int = 0


class FlowCreate(BaseModel):
    flow_code: str
    flow_name: str
    description: str
    flow_category: str = "business"
    steps: list[FlowStepIn] = Field(default_factory=list)
    links: list[FlowLinkIn] = Field(default_factory=list)


class FlowUpdate(BaseModel):
    flow_name: str | None = None
    description: str | None = None
    flow_category: str | None = None
    steps: list[FlowStepIn] | None = None
    links: list[FlowLinkIn] | None = None


class FlowStepOut(BaseModel):
    id: int
    step_code: str
    step_type: str
    sort_no: int
    action_name: str | None
    args_json: Any | None
    slot_code: str | None
    response_mode: str | None
    response_text: str | None
    response_prompt: str | None
    validate_condition: str | None
    validate_fail_text: str | None
    pos_x: float | None
    pos_y: float | None

    class Config:
        from_attributes = True


class FlowLinkOut(BaseModel):
    id: int
    from_step_code: str
    link_type: str
    condition_expr: str | None
    to_step_code: str
    sort_no: int

    class Config:
        from_attributes = True


class FlowOut(BaseModel):
    id: int
    flow_code: str
    flow_name: str
    description: str
    flow_category: str
    status: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FlowDetailOut(FlowOut):
    steps: list[FlowStepOut]
    links: list[FlowLinkOut]


# ---------- 发布 / 回滚 ----------

class ReleaseOut(BaseModel):
    id: int
    release_no: str
    release_type: str
    target_code: str
    version: int
    status: str
    remark: str | None
    published_by: int
    published_at: datetime

    class Config:
        from_attributes = True


class ReleaseCreate(BaseModel):
    release_type: str = "flow"  # flow/intent/faq/knowledge/full
    target_code: str = "ALL"
    remark: str | None = None