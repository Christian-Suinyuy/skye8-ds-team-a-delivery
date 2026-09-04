from pathlib import Path

import pandas as pd
from sqlalchemy import select

from api.config.database import Base, SessionLocal, engine
from api.config.models.borrower import Borrower
from api.config.models.branch import Branch
from api.config.models.user import User  # noqa: F401

RAW_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def _parse_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _load_branches() -> None:
    branches = pd.read_csv(RAW_DATA_DIR / "branches.csv")
    with SessionLocal.begin() as session:
        existing_ids = set(session.scalars(select(Branch.branch_id)).all())
        rows = [
            Branch(
                branch_id=str(row.branch_id),
                branch_name=str(row.branch_name),
                region=str(row.region),
                opened_year=int(str(row.opened_year)),
                staff_count=int(str(row.staff_count)),
            )
            for row in branches.itertuples(index=False)
            if str(row.branch_id) not in existing_ids
        ]
        session.add_all(rows)


def _load_borrowers() -> None:
    borrowers = pd.read_csv(RAW_DATA_DIR / "borrowers.csv")
    with SessionLocal.begin() as session:
        existing_ids = set(session.scalars(select(Borrower.borrower_id)).all())
        rows = [
            Borrower(
                borrower_id=str(row.borrower_id),
                branch_id=str(row.branch_id),
                sex=str(row.sex),
                age=int(str(row.age)),
                sector=str(row.sector),
                household_size=int(str(row.household_size)),
                years_in_business=float(str(row.years_in_business)),
                has_bank_account=_parse_bool(row.has_bank_account),
                prior_loans=int(str(row.prior_loans)),
            )
            for row in borrowers.itertuples(index=False)
            if str(row.borrower_id) not in existing_ids
        ]
        session.add_all(rows)


def load_models():
    """Create tables and load dependency data required by the API."""
    Base.metadata.create_all(bind=engine)
    _load_branches()
    _load_borrowers()
