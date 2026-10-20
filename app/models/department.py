from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.equipment import Equipment

class Department(Base):
    __tablename__ = "department"

    department_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    equipment_items: Mapped[list["Equipment"]] = relationship(back_populates="department")
    

