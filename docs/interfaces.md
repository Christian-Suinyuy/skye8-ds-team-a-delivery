# Interfaces — SKY8-DS-PR2-A Team A

**Status: DRAFT — for team review.** This should be agreed by Alieh Mae,
Ngeh Brice, and Banboye Christian before implementation continues, then
committed as the agreed version. Track changes to this file as PRs like
any other change (see the brief, Stage A).

## 1. Feature contract

Source of truth in code: `src/features/build_features.py`
(`NUMERIC_FEATURES`, `CATEGORICAL_FEATURES`).

Design decision: categorical encoding (one-hot etc.) is **not** done in
this module — it lives inside the trained sklearn `Pipeline` that gets
saved as the model artifact. Both training and serving call the same
`build_feature_frame` / `build_feature_record` functions and hand the
model raw, typed columns. This avoids a second encoder that could drift
out of sync with the one used at training time.

| Feature | Type | Source | Notes |
|---|---|---|---|
| `amount_xaf` | float | loans | parsed from 3 raw formats — see `src/data/clean.py` |
| `term_months` | int | loans | |
| `monthly_rate_pct` | float | loans | |
| `declared_income_xaf` | float | loans | parsed from 3 raw formats |
| `loan_to_income_ratio` | float | derived | `amount_xaf / declared_income_xaf` |
| `product` | categorical | loans | |
| `channel` | categorical | loans | |
| `collateral` | categorical | loans | |
| `age` | int | borrowers | |
| `sex` | categorical | borrowers | |
| `sector` | categorical | borrowers | |
| `household_size` | int | borrowers | |
| `years_in_business` | float | borrowers | |
| `has_bank_account` | bool | borrowers | parsed from 4 raw casings |
| `prior_loans` | int | borrowers | |
| `region` | categorical | branches | branch is the loan's disbursing branch, **not** the borrower's home branch — see note below |
| `branch_age_years` | int | derived | `disbursed_on.year - branches.opened_year` |
| `staff_count` | int | branches | |

**Open item to confirm with the team:** `borrowers.csv` has its own
`branch_id` column (the borrower's home branch) which can differ from
the `branch_id` on a given loan (the disbursing branch). The current
feature pipeline uses the **loan's** branch for region/branch features.
Flagging this because it's easy to merge on the wrong one silently.

## 2. Prediction request / response contract (proposed — Christian owns final)

**POST /predict**

Request body — a single application, raw (uncleaned) values as they'd
arrive from a loan officer's form:

```json
{
  "amount_xaf": "250,000",
  "term_months": 12,
  "monthly_rate_pct": 2.5,
  "declared_income_xaf": "XAF 120000",
  "product": "individual micro",
  "channel": "branch",
  "collateral": "group guarantee",
  "disbursed_on": "23/04/2026",
  "borrower_id": "BW512874",
  "branch_id": "BR-04"
}
```

Response:

```json
{
  "probability_of_default": 0.34,
  "decision": "review",
  "model_version": "3",
  "model_name": "skye8-credit-risk-model"
}
```

- `model_version` is **never optional** — every response carries it (acceptance criterion #3).
- Validation errors return 4xx naming the offending field (e.g. `{"error": "amount_xaf", "detail": "unrecognised amount format"}`), never a silent prediction.
- `src/data/clean.clean_single_record()` and `src/features/build_features.build_feature_record()` are the shared functions serving should call for cleaning/feature-building — do not re-implement parsing in the API layer.

## 3. Registry naming convention

- **Registered model name:** `skye8-credit-risk-model` (one name, versions increment automatically)
- **Production pointer:** MLflow alias `production` on the current live version (queried via `get_model_version_by_alias`), plus the legacy `Production` stage set in parallel for compatibility with tools that still read stages
- **Experiment name:** `skye8-credit-risk` (all training runs, all candidates, logged here)
- Promotions are done via `python -m src.training.registry --metric pr_auc`, never by manually copying a model file

## Revision history

| Date | Change | By |
|---|---|---|
| 2026-09-02 | Initial draft — feature contract, request/response proposal, registry naming | Ngeh Brice |
