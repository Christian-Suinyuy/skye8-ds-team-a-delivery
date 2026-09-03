import pandas as pd
from api.schema.model import PredictionRequest, PredictionResponse
import mlflow
import sklearn
import mlflow.sklearn


mlflow.set_tracking_uri("sqlite:///mlflow.db")
model = mlflow.sklearn.load_model("mlruns/1/models/m-777ba5a7a77e420d9aa99cb2a75ce742/artifacts")

def get_prediction(features: PredictionRequest) -> PredictionResponse:
    df = pd.DataFrame([features.model_dump()])
    response = model.predict_proba(df)
    probability = float(response[0, 1])
    return PredictionResponse(
      probability_of_default=probability,
      decision="review" if probability < 0.5 else "decline",
      model_version="3",
      model_name="skye8-credit-risk-model"
    )




