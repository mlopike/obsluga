from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.department import Department

if TYPE_CHECKING:
    from app.models.request import Request


class Equipment(Base):
    __tablename__ = "equipment"

    equipment_id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("department.department_id"))
    name: Mapped[str] = mapped_column(String(255))

    department: Mapped[Department] = relationship(back_populates="equipment_items")
    requests: Mapped[list["Request"]] = relationship(back_populates="equipment")
