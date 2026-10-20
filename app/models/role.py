from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Role(Base):
    __tablename__ = "role"

    role_id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(255), unique=True)
    perm_level: Mapped[Optional[int]] = mapped_column()