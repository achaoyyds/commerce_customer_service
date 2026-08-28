"""知识库管理路由：分类 + FAQ。"""
from fastapi import APIRouter, HTTPException, Query, status

from atuguigu.admin.dependencies import (
    AdminSessionDep,
    CurrentUserDep,
    KbCategoryRepositoryDep,
    KbFaqRepositoryDep,
)
from atuguigu.admin.models import KbCategory, KbFaq
from atuguigu.admin.schemas import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    FaqCreate,
    FaqOut,
    FaqStatusUpdate,
    FaqUpdate,
)
from atuguigu.admin.services import _gen_no

router = APIRouter(prefix="/api/admin", tags=["admin-knowledge"])


# ---------- 分类 ----------

@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(repo: KbCategoryRepositoryDep):
    return await repo.list_all()


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, repo: KbCategoryRepositoryDep):
    category = KbCategory(
        category_code=data.category_code,
        category_name=data.category_name,
        parent_id=data.parent_id,
        sort_no=data.sort_no,
    )
    return await repo.add(category)


@router.put("/categories/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    repo: KbCategoryRepositoryDep,
    session: AdminSessionDep,
):
    category = await repo.get_by_id(category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    await session.commit()
    await session.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, repo: KbCategoryRepositoryDep, session: AdminSessionDep):
    category = await repo.get_by_id(category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    category.yn = 0  # 软删除
    await session.commit()


# ---------- FAQ ----------

@router.get("/faqs")
async def list_faqs(
    repo: KbFaqRepositoryDep,
    category_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    items, total = await repo.list(category_id=category_id, status=status_filter, offset=offset, limit=limit)
    return {"total": total, "items": [FaqOut.model_validate(f).model_dump() for f in items]}


@router.post("/faqs", response_model=FaqOut, status_code=status.HTTP_201_CREATED)
async def create_faq(data: FaqCreate, repo: KbFaqRepositoryDep, current_user: CurrentUserDep):
    faq = KbFaq(
        faq_no=_gen_no("FAQ"),
        category_id=data.category_id,
        question=data.question,
        answer=data.answer,
        keywords=data.keywords,
        sort_no=data.sort_no,
        created_by=current_user.user_id,
    )
    return await repo.add(faq)


@router.put("/faqs/{faq_id}", response_model=FaqOut)
async def update_faq(
    faq_id: int,
    data: FaqUpdate,
    repo: KbFaqRepositoryDep,
):
    faq = await repo.get_by_id(faq_id)
    if faq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ 不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(faq, field, value)
    await repo.add(faq)  # add 内含 commit + refresh
    return faq


@router.patch("/faqs/{faq_id}/status", response_model=FaqOut)
async def update_faq_status(faq_id: int, data: FaqStatusUpdate, repo: KbFaqRepositoryDep):
    faq = await repo.get_by_id(faq_id)
    if faq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ 不存在")
    faq.status = data.status
    await repo.add(faq)
    return faq


@router.delete("/faqs/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(faq_id: int, repo: KbFaqRepositoryDep):
    faq = await repo.get_by_id(faq_id)
    if faq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ 不存在")
    await repo.delete(faq)