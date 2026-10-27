from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.deps import CurrentAccount, DbSession, require_perm
from app.models.request import Request
from app.schemas.request import RequestCreate, RequestOut, RequestPatch

router = APIRouter()


async def _load_request(db: AsyncSession, request_id: int) -> Optional[Request]:
    result = await db.execute(
        select(Request)
        .where(Request.request_id == request_id)
        .options(
            joinedload(Request.equipment),
            joinedload(Request.reporter),
            joinedload(Request.engineer),
        )
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


def _to_out(request: Request) -> RequestOut:
    return RequestOut(
        id=request.request_id,
        equipment=request.equipment.name,
        description=request.malfunction,
        reporter=request.reporter.full_name,
        engineer=request.engineer.full_name if request.engineer is not None else None,
        status=request.status,
        updated=request.updated_at.isoformat() if request.updated_at is not None else "",
        diagnosis=request.diagnosis,
        work_done=request.work_done,
    )


@router.get("", response_model=list[RequestOut])
async def list_tickets(db: DbSession) -> list[RequestOut]:
    result = await db.execute(
        select(Request)
        .options(
            joinedload(Request.equipment),
            joinedload(Request.reporter),
            joinedload(Request.engineer),
        )
        .order_by(Request.updated_at.desc().nulls_last(), Request.created_at.desc())
    )
    return [_to_out(request) for request in result.scalars().all()]


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(data: RequestCreate, current: CurrentAccount, db: DbSession) -> RequestOut:
    request = Request(
        equipment_id=data.equipment_id,
        reporter_id=current.account_id,
        status="new",
        malfunction=data.description,
        updated_at=func.now(),
    )
    db.add(request)
    await db.commit()
    return _to_out(await _load_request(db, request.request_id))


@router.patch("/{request_id}", response_model=RequestOut, dependencies=[Depends(require_perm(2))])
async def patch_ticket(request_id: int, data: RequestPatch, current: CurrentAccount, db: DbSession) -> RequestOut:
    request = await _load_request(db, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    if data.status is not None:
        request.status = data.status.value
    if data.diagnosis is not None:
        request.diagnosis = data.diagnosis
    if data.work_done is not None:
        request.work_done = data.work_done
    if request.engineer_id is None and request.status != "new":
        request.engineer_id = current.account_id

    await db.commit()
    return _to_out(await _load_request(db, request_id))
