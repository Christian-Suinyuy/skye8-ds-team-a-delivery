import pandas as pd

from src.features.build_features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    build_feature_frame,
    build_feature_record,
)


def _loans_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            dict(
                loan_id="L1",
                borrower_id="B1",
                branch_id="BR-01",
                disbursed_on=pd.Timestamp("2024-06-01"),
                product="individual micro",
                channel="branch",
                amount_xaf=100000.0,
                term_months=12,
                monthly_rate_pct=2.0,
                declared_income_xaf=50000.0,
                collateral="none",
                defaulted=True,
            ),
            dict(
                loan_id="L2",
                borrower_id="B2",
                branch_id="BR-02",
                disbursed_on=pd.Timestamp("2025-01-15"),
                product="digital nano",
                channel="mobile",
                amount_xaf=200000.0,
                term_months=6,
                monthly_rate_pct=3.0,
                declared_income_xaf=100000.0,
                collateral="land title",
                defaulted=False,
            ),
        ]
    )


def _borrowers_df() -> pd.DataFrame:
    # Note: borrowers carry their OWN branch_id (home branch), deliberately
    # different from the loan's disbursing branch_id above, to exercise
    # the merge-collision fix.
    return pd.DataFrame(
        [
            dict(
                borrower_id="B1",
                branch_id="BR-99",
                sex="F",
                age=34,
                sector="farming",
                household_size=5,
                years_in_business=4.0,
                has_bank_account=True,
                prior_loans=1,
            ),
            dict(
                borrower_id="B2",
                branch_id="BR-98",
                sex="M",
                age=41,
                sector="tailoring",
                household_size=3,
                years_in_business=2.0,
                has_bank_account=False,
                prior_loans=0,
            ),
        ]
    )


def _branches_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            dict(
                branch_id="BR-01",
                branch_name="A",
                region="Mezam",
                opened_year=2019,
                staff_count=10,
            ),
            dict(
                branch_id="BR-02",
                branch_name="B",
                region="Bui",
                opened_year=2021,
                staff_count=6,
            ),
        ]
    )


def test_build_feature_frame_uses_loan_branch_not_borrower_home_branch():
    frame = build_feature_frame(_loans_df(), _borrowers_df(), _branches_df())
    # L1's loan branch is BR-01 (region Mezam), NOT the borrower's home
    # branch BR-99 which doesn't even exist in branches.csv here.
    row = frame[frame["loan_id"] == "L1"].iloc[0]
    assert row["region"] == "Mezam"


def test_build_feature_frame_has_all_contract_columns():
    frame = build_feature_frame(_loans_df(), _borrowers_df(), _branches_df())
    for col in NUMERIC_FEATURES + CATEGORICAL_FEATURES:
        assert col in frame.columns


def test_loan_to_income_ratio_is_correct():
    frame = build_feature_frame(_loans_df(), _borrowers_df(), _branches_df())
    row = frame[frame["loan_id"] == "L1"].iloc[0]
    assert row["loan_to_income_ratio"] == 100000.0 / 50000.0


def test_branch_age_years_is_correct():
    frame = build_feature_frame(_loans_df(), _borrowers_df(), _branches_df())
    row = frame[frame["loan_id"] == "L1"].iloc[0]
    assert row["branch_age_years"] == 2024 - 2019


def test_defaulted_outcome_preserved():
    frame = build_feature_frame(_loans_df(), _borrowers_df(), _branches_df())
    by_id = frame.set_index("loan_id")
    assert by_id.loc["L1", "defaulted"] == True  # noqa: E712
    assert by_id.loc["L2", "defaulted"] == False  # noqa: E712


def test_build_feature_record_matches_batch_path_for_same_inputs():
    """The single-record (serving-time) path and the batch (training-time)
    path must compute the same derived values from equivalent inputs."""
    cleaned_loan = {
        "amount_xaf": 100000.0,
        "term_months": 12,
        "monthly_rate_pct": 2.0,
        "declared_income_xaf": 50000.0,
        "product": "individual micro",
        "channel": "branch",
        "collateral": "none",
        "disbursed_on": pd.Timestamp("2024-06-01"),
    }
    borrower = {
        "age": 34,
        "sex": "F",
        "sector": "farming",
        "household_size": 5,
        "years_in_business": 4.0,
        "has_bank_account": True,
        "prior_loans": 1,
    }
    branch = {"region": "Mezam", "opened_year": 2019, "staff_count": 10}

    record = build_feature_record(cleaned_loan, borrower, branch)

    frame = build_feature_frame(_loans_df(), _borrowers_df(), _branches_df())
    batch_row = frame[frame["loan_id"] == "L1"].iloc[0]

    assert record["loan_to_income_ratio"] == batch_row["loan_to_income_ratio"]
    assert record["branch_age_years"] == batch_row["branch_age_years"]
    for col in NUMERIC_FEATURES + CATEGORICAL_FEATURES:
        assert record[col] == batch_row[col]
