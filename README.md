# skye8-ds-team-a-delivery
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

```bash
uv run dev
```

### Batch predictions

The API provides an authenticated CSV batch endpoint:

```text
POST /predict/batch
```

The CSV must contain one row per application and these columns:

```text
amount_xaf,term_months,monthly_rate_pct,declared_income_xaf,
loan_to_income_ratio,age,household_size,years_in_business,prior_loans,
branch_age_years,staff_count,product,channel,collateral,sex,sector,
has_bank_account,region
```

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


