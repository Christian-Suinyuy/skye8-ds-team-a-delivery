from typing import Literal

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    amount_xaf: float
    term_months: int = Field(ge=3, le=24)
    monthly_rate_pct: float
    declared_income_xaf: float = Field(gt=0)
    loan_to_income_ratio: float
    age: int
    household_size: int = Field(ge=1, le=12)
    years_in_business: float
    prior_loans: int = Field(ge=0)
    branch_age_years: int
    staff_count: int
    product: Literal[
        "digital nano",
        "asset finance",
        "group solidarity",
        "individual micro",
        "working capital",
    ]
    channel: Literal["mobile", "field agent", "branch"]
    collateral: Literal["land title", "equipment", "group guarantee", "none"]
    sex: Literal["M", "F"]
    sector: Literal[
        "farming",
        "tailoring",
        "retail shop",
        "teaching",
        "food vending",
        "petty trade",
        "hairdressing",
        "transport",
        "carpentry",
        "poultry",
        "masonry",
        "phone repair",
    ]
    has_bank_account: bool
    region: str


class PredictionResponse(BaseModel):
    probability_of_default: float
    decision: str
    model_version: str
    model_name: str
    model_stage: str


class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]
