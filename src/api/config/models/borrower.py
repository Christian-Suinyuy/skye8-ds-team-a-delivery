from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.config.database import Base


class Borrower(Base):
    __tablename__ = "borrowers"

    borrower_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.branch_id"), nullable=False)
    sex: Mapped[str] = mapped_column(String(1), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    household_size: Mapped[int] = mapped_column(Integer, nullable=False)
    years_in_business: Mapped[float] = mapped_column(Float, nullable=False)
    has_bank_account: Mapped[bool] = mapped_column(Boolean, nullable=False)
    prior_loans: Mapped[int] = mapped_column(Integer, nullable=False)
