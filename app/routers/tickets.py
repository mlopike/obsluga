"""Заявки. Права по ролям:

  Сотрудник     — создаёт заявки и видит только свои;
  Инженер       — видит очередь новых и свои заявки, берёт в работу, фиксирует диагноз и закрывает;
  Администратор — видит все заявки и назначает инженера (диагноз и закрытие — не его зона).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.deps import CurrentAccount, DbSession, require_roles
from app.core.roles import PERM_ADMIN, PERM_EMPLOYEE, PERM_ENGINEER
from app.models.account import Account
from app.models.equipment import Equipment
from app.models.request import Request
from app.schemas.request import RequestAssign, RequestCreate, RequestOut, RequestPatch, RequestStatus

router = APIRouter()

_REQUEST_OPTIONS = (
    joinedload(Request.equipment).joinedload(Equipment.department),
    joinedload(Request.reporter).joinedload(Account.department),
    joinedload(Request.engineer),
)


async def _load_request(db: AsyncSession, request_id: int) -> Optional[Request]:
    result = await db.execute(
        select(Request)
        .where(Request.request_id == request_id)
        .options(*_REQUEST_OPTIONS)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


async def _get_or_404(db: AsyncSession, request_id: int) -> Request:
    request = await _load_request(db, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    return request


def _to_out(request: Request) -> RequestOut:
    return RequestOut(
        id=request.request_id,
        equipment=request.equipment.name,
        department=request.equipment.department.name,
        description=request.malfunction,
        reporter=request.reporter.full_name,
        reporter_department=request.reporter.department.name,
        engineer_id=request.engineer_id,
        engineer=request.engineer.full_name if request.engineer is not None else None,
        status=request.status,
        updated=request.updated_at.isoformat() if request.updated_at is not None else "",
        diagnosis=request.diagnosis,
        work_done=request.work_done,
    )


@router.get("", response_model=list[RequestOut])
async def list_tickets(current: CurrentAccount, db: DbSession) -> list[RequestOut]:
    query = select(Request).options(*_REQUEST_OPTIONS)
    perm = current.role.perm_level
    if perm == PERM_EMPLOYEE:
        query = query.where(Request.reporter_id == current.account_id)
    elif perm == PERM_ENGINEER:
        query = query.where(or_(Request.status == "new", Request.engineer_id == current.account_id))
    query = query.order_by(Request.updated_at.desc().nulls_last(), Request.created_at.desc())
    result = await db.execute(query)
    return [_to_out(request) for request in result.scalars().all()]


@router.post(
    "",
    response_model=RequestOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(PERM_EMPLOYEE))],
)
async def create_ticket(data: RequestCreate, current: CurrentAccount, db: DbSession) -> RequestOut:
    if await db.get(Equipment, data.equipment_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Оборудование не найдено")
    request = Request(
        equipment_id=data.equipment_id,
        reporter_id=current.account_id,
        status="new",
        malfunction=data.description.strip(),
        updated_at=func.now(),
    )
    db.add(request)
    await db.commit()
    return _to_out(await _load_request(db, request.request_id))


@router.post(
    "/{request_id}/take",
    response_model=RequestOut,
    dependencies=[Depends(require_roles(PERM_ENGINEER))],
)
async def take_ticket(request_id: int, current: CurrentAccount, db: DbSession) -> RequestOut:
    """Инженер берёт новую заявку из очереди в работу."""
    request = await _get_or_404(db, request_id)
    if request.status != "new" or request.engineer_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Заявка уже взята в работу")
    request.engineer_id = current.account_id
    request.status = "progress"
    await db.commit()
    return _to_out(await _load_request(db, request_id))


@router.patch(
    "/{request_id}",
    response_model=RequestOut,
    dependencies=[Depends(require_roles(PERM_ENGINEER))],
)
async def patch_ticket(request_id: int, data: RequestPatch, current: CurrentAccount, db: DbSession) -> RequestOut:
    """Инженер фиксирует диагноз и работы по СВОЕЙ заявке и закрывает её."""
    request = await _get_or_404(db, request_id)
    if request.status == "closed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Заявка закрыта и не редактируется")
    if request.engineer_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Сначала возьмите заявку в работу")
    if request.engineer_id != current.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Заявка назначена другому инженеру")
    if data.status == RequestStatus.new:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вернуть заявку в статус «Новая» нельзя",
        )

    if data.diagnosis is not None:
        request.diagnosis = data.diagnosis.strip() or None
    if data.work_done is not None:
        request.work_done = data.work_done.strip() or None
    if data.status == RequestStatus.closed:
        if not request.diagnosis or not request.work_done:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Для закрытия заявки заполните диагноз и выполненные работы",
            )
        request.status = "closed"

    await db.commit()
    return _to_out(await _load_request(db, request_id))


@router.post(
    "/{request_id}/assign",
    response_model=RequestOut,
    dependencies=[Depends(require_roles(PERM_ADMIN))],
)
async def assign_ticket(request_id: int, data: RequestAssign, db: DbSession) -> RequestOut:
    """Администратор назначает (или переназначает) инженера."""
    request = await _get_or_404(db, request_id)
    if request.status == "closed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Заявка закрыта: инженера менять нельзя")
    engineer = (
        await db.execute(
            select(Account).where(Account.account_id == data.engineer_id).options(joinedload(Account.role))
        )
    ).scalar_one_or_none()
    if engineer is None or engineer.role.perm_level != PERM_ENGINEER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Назначить можно только инженера")

    request.engineer_id = engineer.account_id
    if request.status == "new":
        request.status = "progress"
    await db.commit()
    return _to_out(await _load_request(db, request_id))
