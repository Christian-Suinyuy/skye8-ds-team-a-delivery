# skye8-ds-team-a-delivery

[![CI](https://github.com/Christian-Suinyuy/skye8-ds-team-a-delivery/actions/workflows/ci.yml/badge.svg?branch=backend)](https://github.com/Christian-Suinyuy/skye8-ds-team-a-delivery/actions/workflows/ci.yml)

End-to-end ML platform for credit risk prediction, model serving, deployment, and production monitoring.

## Development Setup

### Install dependencies

```bash
uv sync

```
#### Add a new package
```bash
uv add package_name
```

### Database requirements

The API requires a running PostgreSQL database before the server starts. Add
the connection string to a local `.env` file in the repository root:

```env
DATABASE_STRING=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/DATABASE_NAME
JWT_SECRET_KEY=replace-with-a-secret-at-least-32-characters-long
JWT_ALGORITHM=HS256
```

Do not commit `.env` or real credentials. The database user must be allowed to
create tables and insert rows. On startup, the API creates these tables:

- `users`
- `branches`
- `borrowers`

The startup loader reads `data/raw/branches.csv` and
`data/raw/borrowers.csv` into the dependency tables. Loading is idempotent:
existing branch and borrower IDs are skipped. `loans_train.csv` and
`loans_live.csv` are not loaded into the database during API startup.

### Start the FastAPI server
```bash
uv run dev
```

The server listens on `http://127.0.0.1:8005` and provides interactive API
documentation at `http://127.0.0.1:8005/docs`.

The authenticated `GET /` health endpoint reports the loaded model metadata:

```json
{
  "message": "server is running. Everything is Good",
  "model": {
    "model_name": "skye8-credit-risk-model",
    "model_version": "3",
    "model_stage": "Production",
    "model_alias": "production"
  }
}
```

## Single prediction

`POST /api/v1/predict` requires a bearer token and a JSON body containing the
18 model features:

```json
{
  "amount_xaf": 250000,
  "term_months": 12,
  "monthly_rate_pct": 2.5,
  "declared_income_xaf": 120000,
  "loan_to_income_ratio": 2.0833,
  "age": 34,
  "household_size": 5,
  "years_in_business": 4,
  "prior_loans": 1,
  "branch_age_years": 7,
  "staff_count": 10,
  "product": "individual micro",
  "channel": "branch",
  "collateral": "group guarantee",
  "sex": "F",
  "sector": "farming",
  "has_bank_account": true,
  "region": "Mezam"
}
```

The response includes the probability, decision, model version, and MLflow
stage. Every response also includes an `X-Request-ID` header. The server logs
that ID with the UTC timestamp, status code, and request duration.

### Batch predictions

The API provides an authenticated CSV batch endpoint. It accepts a raw loans
CSV and loads the borrower and branch features from the database using
`borrower_id` and `branch_id`:

```text
POST /predict/batch
```

The raw loans CSV must contain these columns:

```text
loan_id,borrower_id,branch_id,disbursed_on,product,channel,amount_xaf,
term_months,monthly_rate_pct,declared_income_xaf,collateral
```

Extra columns such as `officer_id` and `defaulted` are ignored. The service
calculates `loan_to_income_ratio` and `branch_age_years`, and adds borrower
fields (`age`, `sex`, `sector`, `household_size`, `years_in_business`,
`has_bank_account`, `prior_loans`) and branch fields (`region`, `staff_count`).

The endpoint also accepts a prepared CSV containing the 18 model features:

```text
amount_xaf,term_months,monthly_rate_pct,declared_income_xaf,
loan_to_income_ratio,age,household_size,years_in_business,prior_loans,
branch_age_years,staff_count,product,channel,collateral,sex,sector,
has_bank_account,region
```

Rows with an unknown borrower or branch, missing columns, invalid categories,
or invalid numeric values return `422` with the row number and offending field.

Example request from PowerShell:

```powershell
curl.exe -X POST "http://127.0.0.1:8005/predict/batch" `
	-H "Authorization: Bearer YOUR_TOKEN" `
	-F "file=@batch.csv"
```

Each row produces a probability, decision, model version, and model stage.

### Pre-commit

Install the development dependencies and enable the lint hook:

```bash
uv sync --extra dev
uv run pre-commit install
```

Run it manually across the repository with:

```bash
uv run pre-commit run --all-files
```

### Continuous integration

The CI workflow installs dependencies from `uv.lock` with Python 3.12 and
runs Ruff, Black, and mypy. Pytest is temporarily disabled until the missing
`src/data/clean.py` module is restored; the tests remain in `tests/` and can
be run locally with:

```bash
uv run --extra dev pytest tests/ -v
```


