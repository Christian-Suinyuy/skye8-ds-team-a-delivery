from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.config.database import Base


class Branch(Base):
    __tablename__ = "branches"

    branch_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    branch_name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    opened_year: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_count: Mapped[int] = mapped_column(Integer, nullable=False)
