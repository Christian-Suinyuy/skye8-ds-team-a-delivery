from locust import HttpUser, task, between
import os
import dotenv

dotenv.load_dotenv()

class LoanApiUser(HttpUser):

    wait_time = between(1,2)

    TOKEN = os.getenv("API_BEARER_TOKEN")
    @task
    def test_predict(self):
        headers = {"Authorization": f"Bearer {self.TOKEN}"}

        payload = {
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
        "has_bank_account":True,
        "region": "Mezam"
        }

        self.client.post("/api/v1/predict", json=payload, headers=headers)