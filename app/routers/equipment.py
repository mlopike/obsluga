from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import DbSession
from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentOut

router = APIRouter()


@router.get("", response_model=list[EquipmentOut])
async def list_equipment(db: DbSession) -> list[EquipmentOut]:
    result = await db.execute(
        select(Equipment.equipment_id, Equipment.name).order_by(Equipment.name)
    )
    return [EquipmentOut(id=equipment_id, name=name) for equipment_id, name in result.all()]
