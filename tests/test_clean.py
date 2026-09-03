import pandas as pd
import pytest
from src.data.clean import (
    CleaningError,
    clean_borrowers,
    clean_loans,
    clean_single_record,
    parse_amount,
    parse_bool,
    parse_date,
)

# ---------------------------------------------------------------------------
# parse_amount
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("250000", 250000.0),
        ("250,000", 250000.0),
        ("XAF 250000", 250000.0),
        ("XAF 250,000", 250000.0),
        (250000, 250000.0),
        (250000.0, 250000.0),
    ],
)
def test_parse_amount_formats(raw, expected):
    assert parse_amount(raw) == expected


def test_parse_amount_rejects_empty():
    with pytest.raises(CleaningError):
        parse_amount("")


def test_parse_amount_rejects_missing():
    with pytest.raises(CleaningError):
        parse_amount(None)


# ---------------------------------------------------------------------------
# parse_date
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    ["2024-04-23", "23/04/2024", "23 Apr 2024"],
)
def test_parse_date_formats_agree(raw):
    assert parse_date(raw) == pd.Timestamp("2024-04-23")


def test_parse_date_rejects_garbage():
    with pytest.raises(CleaningError):
        parse_date("not-a-date")


# ---------------------------------------------------------------------------
# parse_bool
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("TRUE", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("YES", True),
        ("FALSE", False),
        ("False", False),
        ("0", False),
        ("no", False),
        (True, True),
        (False, False),
    ],
)
def test_parse_bool_casings(raw, expected):
    assert parse_bool(raw) is expected


def test_parse_bool_rejects_unrecognised():
    with pytest.raises(CleaningError):
        parse_bool("maybe")


# ---------------------------------------------------------------------------
# clean_loans (batch)
# ---------------------------------------------------------------------------


def _sample_loans_df() -> pd.DataFrame:
    rows = [
        # normal row, ISO date, plain amount
        dict(
            loan_id="L1",
            borrower_id="B1",
            disbursed_on="2024-01-05",
            amount_xaf="100000",
            declared_income_xaf="50000",
            defaulted="NO",
        ),
        # slash date, comma amount
        dict(
            loan_id="L2",
            borrower_id="B1",
            disbursed_on="12/02/2024",
            amount_xaf="200,000",
            declared_income_xaf="80000",
            defaulted="YES",
        ),
        # "DD Mon YYYY" date, XAF-prefixed amount
        dict(
            loan_id="L3",
            borrower_id="B2",
            disbursed_on="03 Mar 2024",
            amount_xaf="XAF 300000",
            declared_income_xaf="90000",
            defaulted="NO",
        ),
        # exact duplicate of L1 -> should be dropped
        dict(
            loan_id="L1",
            borrower_id="B1",
            disbursed_on="2024-01-05",
            amount_xaf="100000",
            declared_income_xaf="50000",
            defaulted="NO",
        ),
        # orphaned borrower -> should be dropped when valid_borrower_ids given
        dict(
            loan_id="L4",
            borrower_id="GHOST",
            disbursed_on="2024-04-01",
            amount_xaf="150000",
            declared_income_xaf="60000",
            defaulted="NO",
        ),
        # no outcome yet (live book) -> should be preserved as null, not dropped
        dict(
            loan_id="L5",
            borrower_id="B2",
            disbursed_on="2026-06-01",
            amount_xaf="120000",
            declared_income_xaf="70000",
            defaulted=None,
        ),
    ]
    return pd.DataFrame(rows)


def test_clean_loans_drops_exact_duplicates():
    df = _sample_loans_df()
    cleaned, report = clean_loans(df, valid_borrower_ids={"B1", "B2"})
    assert report.exact_duplicate_rows_dropped == 1
    assert (cleaned["loan_id"] == "L1").sum() == 1


def test_clean_loans_drops_orphaned_borrowers():
    df = _sample_loans_df()
    cleaned, report = clean_loans(df, valid_borrower_ids={"B1", "B2"})
    assert report.orphaned_borrower_rows_dropped == 1
    assert "GHOST" not in cleaned["borrower_id"].values


def test_clean_loans_parses_all_three_date_formats_to_same_type():
    df = _sample_loans_df()
    cleaned, _ = clean_loans(df, valid_borrower_ids={"B1", "B2"})
    assert all(isinstance(v, pd.Timestamp) for v in cleaned["disbursed_on"])


def test_clean_loans_parses_all_amount_formats():
    df = _sample_loans_df()
    cleaned, _ = clean_loans(df, valid_borrower_ids={"B1", "B2"})
    by_id = cleaned.set_index("loan_id")
    assert by_id.loc["L1", "amount_xaf"] == 100000.0
    assert by_id.loc["L2", "amount_xaf"] == 200000.0
    assert by_id.loc["L3", "amount_xaf"] == 300000.0


def test_clean_loans_preserves_missing_outcome_as_null_not_dropped():
    df = _sample_loans_df()
    cleaned, report = clean_loans(df, valid_borrower_ids={"B1", "B2"})
    row = cleaned[cleaned["loan_id"] == "L5"]
    assert len(row) == 1  # not dropped
    assert row.iloc[0]["defaulted"] is None
    assert report.unparseable_rows_dropped == 0


def test_clean_loans_without_valid_ids_keeps_all_borrowers():
    df = _sample_loans_df()
    cleaned, report = clean_loans(df, valid_borrower_ids=None)
    assert report.orphaned_borrower_rows_dropped == 0
    assert "GHOST" in cleaned["borrower_id"].values


def test_clean_loans_report_row_counts_are_consistent():
    df = _sample_loans_df()
    cleaned, report = clean_loans(df, valid_borrower_ids={"B1", "B2"})
    assert report.input_rows == len(df)
    assert report.output_rows == len(cleaned)
    assert (
        report.input_rows
        - report.exact_duplicate_rows_dropped
        - report.orphaned_borrower_rows_dropped
        - report.unparseable_rows_dropped
        == report.output_rows
    )


# ---------------------------------------------------------------------------
# clean_borrowers
# ---------------------------------------------------------------------------


def test_clean_borrowers_normalises_all_casings():
    df = pd.DataFrame(
        {
            "borrower_id": ["B1", "B2", "B3", "B4"],
            "has_bank_account": ["TRUE", "0", "yes", "False"],
        }
    )
    cleaned = clean_borrowers(df)
    assert cleaned["has_bank_account"].tolist() == [True, False, True, False]
    assert cleaned["has_bank_account"].dtype == bool


# ---------------------------------------------------------------------------
# clean_single_record (serving-time path)
# ---------------------------------------------------------------------------


def test_clean_single_record_matches_batch_parsing():
    record = {
        "disbursed_on": "23/04/2024",
        "amount_xaf": "XAF 250,000",
        "declared_income_xaf": "50000",
        "has_bank_account": "yes",
    }
    cleaned = clean_single_record(record)
    assert cleaned["disbursed_on"] == pd.Timestamp("2024-04-23")
    assert cleaned["amount_xaf"] == 250000.0
    assert cleaned["declared_income_xaf"] == 50000.0
    assert cleaned["has_bank_account"] is True


def test_clean_single_record_raises_on_bad_field_for_4xx_mapping():
    record = {"amount_xaf": "not-a-number"}
    with pytest.raises(CleaningError):
        clean_single_record(record)
