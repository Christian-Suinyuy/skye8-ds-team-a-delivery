import pandas as pd
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config.models.borrower import Borrower
from api.config.models.branch import Branch
from api.schema.model import PredictionRequest


class PredictionDataError(ValueError):
    """Raised when a prediction DataFrame cannot be made model-ready."""

    def __init__(self, detail: object):
        self.detail = detail
        super().__init__(str(detail))


RAW_LOAN_FIELDS = {
    "amount_xaf",
    "term_months",
    "monthly_rate_pct",
    "declared_income_xaf",
    "product",
    "channel",
    "collateral",
    "disbursed_on",
    "borrower_id",
    "branch_id",
}


def _parse_amount(value: object) -> float:
    """Convert plain and XAF-prefixed amounts into model-ready floats."""
    return float(str(value).replace("XAF", "").replace(",", "").strip())


def _enrich_raw_loans(frame: pd.DataFrame, session: Session) -> pd.DataFrame:
    """Join raw loan rows with borrower and disbursing-branch database data."""
    # Fetch dependency rows in bulk instead of querying once per loan row.
    borrower_ids = {str(value) for value in frame["borrower_id"].dropna()}
    branch_ids = {str(value) for value in frame["branch_id"].dropna()}
    borrowers = session.scalars(
        select(Borrower).where(Borrower.borrower_id.in_(borrower_ids))
    ).all()
    branches = session.scalars(select(Branch).where(Branch.branch_id.in_(branch_ids))).all()
    borrower_map = {borrower.borrower_id: borrower for borrower in borrowers}
    branch_map = {branch.branch_id: branch for branch in branches}

    enriched = []
    errors = []
    for row_number, record in enumerate(frame.to_dict(orient="records"), start=2):
        borrower_id = str(record.get("borrower_id"))
        branch_id = str(record.get("branch_id"))
        borrower = borrower_map.get(borrower_id)
        branch = branch_map.get(branch_id)
        row_errors = []
        if borrower is None:
            row_errors.append({"loc": ["borrower_id"], "msg": "borrower not found"})
        if branch is None:
            row_errors.append({"loc": ["branch_id"], "msg": "branch not found"})
        if row_errors:
            errors.append({"row": row_number, "errors": row_errors})
            continue
        assert borrower is not None
        assert branch is not None

        # Build the same derived features used by the training pipeline.
        try:
            disbursed_year = pd.to_datetime(
                str(record["disbursed_on"]), dayfirst=True, errors="raise"
            ).year
            enriched.append(
                {
                    "amount_xaf": _parse_amount(record["amount_xaf"]),
                    "term_months": record["term_months"],
                    "monthly_rate_pct": record["monthly_rate_pct"],
                    "declared_income_xaf": _parse_amount(record["declared_income_xaf"]),
                    "loan_to_income_ratio": _parse_amount(record["amount_xaf"])
                    / _parse_amount(record["declared_income_xaf"]),
                    "age": borrower.age,
                    "household_size": borrower.household_size,
                    "years_in_business": borrower.years_in_business,
                    "prior_loans": borrower.prior_loans,
                    "branch_age_years": disbursed_year - branch.opened_year,
                    "staff_count": branch.staff_count,
                    "product": record["product"],
                    "channel": record["channel"],
                    "collateral": record["collateral"],
                    "sex": borrower.sex,
                    "sector": borrower.sector,
                    "has_bank_account": borrower.has_bank_account,
                    "region": branch.region,
                }
            )
        except (KeyError, TypeError, ValueError) as error:
            errors.append(
                {
                    "row": row_number,
                    "errors": [{"loc": ["data"], "msg": str(error)}],
                }
            )

    if errors:
        raise PredictionDataError(errors)
    return pd.DataFrame(enriched)


def prepare_prediction_dataframe(
    frame: pd.DataFrame,
    session: Session | None = None,
) -> pd.DataFrame:
    """Validate input and return only the model's required columns.

    A frame can be either a prepared 18-feature frame or raw loans data when
    a database session is supplied. Extra columns such as loan_id, officer_id,
    and defaulted are ignored.
    """
    if frame.empty:
        raise PredictionDataError("file must contain at least one data row")

    required_fields = set(PredictionRequest.model_fields)
    missing_fields = required_fields - set(frame.columns)
    # Raw loan files need borrower and branch lookups before validation.
    if missing_fields and session is not None and RAW_LOAN_FIELDS <= set(frame.columns):
        frame = _enrich_raw_loans(frame, session)
        missing_fields = required_fields - set(frame.columns)
    missing_field_names = sorted(missing_fields)
    if missing_field_names:
        raise PredictionDataError({"missing_fields": missing_field_names})

    # Validate each row so errors identify both the CSV row and field.
    features = []
    validation_errors = []
    for row_number, record in enumerate(frame.to_dict(orient="records"), start=2):
        try:
            features.append(PredictionRequest.model_validate(record))
        except ValidationError as error:
            validation_errors.append({"row": row_number, "errors": error.errors()})

    if validation_errors:
        raise PredictionDataError(validation_errors)

    return pd.DataFrame([feature.model_dump() for feature in features])
