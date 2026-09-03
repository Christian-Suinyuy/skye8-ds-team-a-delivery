from typing import Literal

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    amount_xaf: float
    term_months: int = Field(ge=3, le=24)
    monthly_rate_pct: float
    declared_income_xaf: float = Field(gt=0)
    loan_to_income_ratio: float
    age: int
    household_size: int
    years_in_business: float
    prior_loans: int
    branch_age_years: int
    staff_count: int
    product: Literal[
        "asset finance",
        "group solidarity",
        "individual micro",
        "working capital",
    ]
    channel: str
    collateral: str
    sex: str
    sector: str
    has_bank_account: bool
    region: str


class PredictionResponse(BaseModel):
    probability_of_default: float
    decision: str
    model_version: str
    model_name: str
    # model_stage: str | None




 