"""
Feature engineering for the Skye8 credit-risk model.

Design choice: this module produces a *raw* feature frame (joined,
derived columns computed, but categoricals left as strings/bools). The
categorical encoding (one-hot etc.) lives inside the sklearn Pipeline
that gets trained and saved as the model artifact — see
src/training/train.py. That means:

  - Training and serving both call `build_feature_frame` /
    `build_feature_record` and get identical raw columns.
  - The encoding logic exists in exactly one place (baked into the
    saved model), so there's no separate encoder to keep in sync
    between training and serving.

This is the contract documented in docs/interfaces.md — the feature
list and dtypes here ARE that contract. Any change to this module is a
change to interfaces.md and should go through the same PR-and-review
process as any other cross-cutting change.
"""

from __future__ import annotations

import pandas as pd

# The feature contract. Keep this in sync with docs/interfaces.md.
NUMERIC_FEATURES = [
    "amount_xaf",
    "term_months",
    "monthly_rate_pct",
    "declared_income_xaf",
    "loan_to_income_ratio",
    "age",
    "household_size",
    "years_in_business",
    "prior_loans",
    "branch_age_years",
    "staff_count",
]

CATEGORICAL_FEATURES = [
    "product",
    "channel",
    "collateral",
    "sex",
    "sector",
    "has_bank_account",
    "region",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Columns that pass through for bookkeeping but are never fed to the model.
ID_COLUMNS = ["loan_id", "borrower_id", "branch_id", "disbursed_on"]


def build_feature_frame(
    loans: pd.DataFrame,
    borrowers: pd.DataFrame,
    branches: pd.DataFrame,
) -> pd.DataFrame:
    """Join cleaned loans + borrowers + branches into one feature frame.

    Expects `loans` and `borrowers` to already be output of
    src.data.clean.clean_loans / clean_borrowers (typed dates, floats,
    bools — not raw strings).

    Returns a dataframe with ID_COLUMNS + FEATURE_COLUMNS + "defaulted"
    (the last one is None for loans with no outcome yet).
    """
    # borrowers.csv also carries a branch_id (the borrower's home branch),
    # which can differ from the branch_id on this specific loan. The loan's
    # own branch_id is the one that determines which branch disbursed it,
    # so that's the one used for the branches join.
    borrowers_for_merge = borrowers.drop(columns=["branch_id"], errors="ignore")

    merged = loans.merge(borrowers_for_merge, on="borrower_id", how="inner", validate="many_to_one")
    merged = merged.merge(branches, on="branch_id", how="inner", validate="many_to_one")

    merged["loan_to_income_ratio"] = merged["amount_xaf"] / merged["declared_income_xaf"]
    merged["branch_age_years"] = merged["disbursed_on"].dt.year - merged["opened_year"]

    keep = ID_COLUMNS + FEATURE_COLUMNS
    if "defaulted" in merged.columns:
        keep = keep + ["defaulted"]

    return merged[keep].reset_index(drop=True)


def build_feature_record(
    cleaned_loan: dict,
    borrower: dict,
    branch: dict,
) -> dict:
    """Build one raw feature record for a single serving-time prediction.

    `cleaned_loan` should already have been through
    src.data.clean.clean_single_record. `borrower` and `branch` are the
    matching rows looked up by the serving layer (by borrower_id /
    branch_id) — this function does not do the lookup itself, since
    serving owns where that lookup data lives (e.g. a cache, a DB call).
    """
    loan_to_income_ratio = cleaned_loan["amount_xaf"] / cleaned_loan["declared_income_xaf"]
    branch_age_years = cleaned_loan["disbursed_on"].year - branch["opened_year"]

    record = {
        "amount_xaf": cleaned_loan["amount_xaf"],
        "term_months": cleaned_loan["term_months"],
        "monthly_rate_pct": cleaned_loan["monthly_rate_pct"],
        "declared_income_xaf": cleaned_loan["declared_income_xaf"],
        "loan_to_income_ratio": loan_to_income_ratio,
        "product": cleaned_loan["product"],
        "channel": cleaned_loan["channel"],
        "collateral": cleaned_loan["collateral"],
        "age": borrower["age"],
        "sex": borrower["sex"],
        "sector": borrower["sector"],
        "household_size": borrower["household_size"],
        "years_in_business": borrower["years_in_business"],
        "has_bank_account": borrower["has_bank_account"],
        "prior_loans": borrower["prior_loans"],
        "region": branch["region"],
        "branch_age_years": branch_age_years,
        "staff_count": branch["staff_count"],
    }
    return record
