from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models.department import Department

class Equipment(Base):
    __tablename__ = "equipment"

    equipment_id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("equipment.equipment_id"))
    name: Mapped[str] = mapped_column(String(255))

    department: Mapped[Department] = relationship(back_populates="equipment_items")
