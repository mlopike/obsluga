from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.account import Account
from app.models.equipment import Equipment


class Request(Base):
    __tablename__ = "request"

    request_id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.equipment_id"))
    reporter_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    engineer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id", ondelete="SET NULL"))
    malfunction: Mapped[str] = mapped_column(String(2048))
    diagnosis: Mapped[Optional[str]] = mapped_column(String(2048))
    work_done: Mapped[Optional[str]] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    equipment: Mapped[Equipment] = relationship(back_populates="requests")
    reporter: Mapped[Account] = relationship(foreign_keys="Request.reporter_id")
    engineer: Mapped[Optional[Account]] = relationship(foreign_keys="Request.engineer_id")
