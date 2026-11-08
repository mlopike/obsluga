from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentAccount, DbSession
from app.models.department import Department
from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentOut

router = APIRouter()


@router.get("", response_model=list[EquipmentOut])
async def list_equipment(_: CurrentAccount, db: DbSession) -> list[EquipmentOut]:
    result = await db.execute(
        select(Equipment.equipment_id, Equipment.name, Department.name)
        .join(Department, Equipment.department_id == Department.department_id)
        .order_by(Equipment.name)
    )
    return [
        EquipmentOut(id=equipment_id, name=name, department=department)
        for equipment_id, name, department in result.all()
    ]
