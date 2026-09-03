from pydantic import BaseModel


class PredictionRequest(BaseModel):
    amount_xaf: float
    term_months: int
    monthly_rate_pct: float
    declared_income_xaf: float
    loan_to_income_ratio: float
    age: int
    household_size: int
    years_in_business: float
    prior_loans: int
    branch_age_years: int
    staff_count: int
    product: str
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




 