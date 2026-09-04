from io import StringIO

import mlflow
import mlflow.sklearn
import pandas as pd
from fastapi import status
from mlflow.tracking import MlflowClient

from api.schema.model import (
    BatchPredictionResponse,
    PredictionRequest,
    PredictionResponse,
)
from api.utils.prediction_data import PredictionDataError, prepare_prediction_dataframe

MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
MODEL_NAME = "skye8-credit-risk-model"

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
client = MlflowClient()
model_version = client.get_model_version_by_alias(MODEL_NAME, "production")
model = mlflow.sklearn.load_model("mlruns/1/models/m-777ba5a7a77e420d9aa99cb2a75ce742/artifacts")


class BatchPredictionError(Exception):
    def __init__(self, detail: object, status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT):
        self.detail = detail
        self.status_code = status_code
        super().__init__(str(detail))


def get_prediction(features: PredictionRequest) -> PredictionResponse:
    df = pd.DataFrame([features.model_dump()])
    response = model.predict_proba(df)
    probability = float(response[0, 1])
    return PredictionResponse(
        probability_of_default=probability,
        decision="review" if probability < 0.5 else "decline",
        model_version=str(model_version.version),
        model_stage=model_version.current_stage,
        model_name=MODEL_NAME,
    )


def get_batch_predictions(features: list[PredictionRequest]) -> list[PredictionResponse]:
    df = pd.DataFrame([feature.model_dump() for feature in features])
    probabilities = model.predict_proba(df)[:, 1]

    return [
        PredictionResponse(
            probability_of_default=float(probability),
            decision="review" if probability < 0.5 else "decline",
            model_version=str(model_version.version),
            model_stage=model_version.current_stage,
            model_name=MODEL_NAME,
        )
        for probability in probabilities
    ]


def predict_batch_csv(contents: bytes, content_type: str | None) -> BatchPredictionResponse:
    if content_type not in {"text/csv", "application/csv", None}:
        raise BatchPredictionError(
            "file must be a CSV",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    try:
        frame = pd.read_csv(StringIO(contents.decode("utf-8-sig")))
    except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as error:
        raise BatchPredictionError(f"invalid CSV file: {error}") from error

    if frame.empty:
        raise BatchPredictionError("file must contain at least one data row")

    try:
        prepared = prepare_prediction_dataframe(frame)
    except PredictionDataError as error:
        raise BatchPredictionError(error.detail) from error

    probabilities = model.predict_proba(prepared)[:, 1]
    predictions = [
        PredictionResponse(
            probability_of_default=float(probability),
            decision="review" if probability < 0.5 else "decline",
            model_version=str(model_version.version),
            model_stage=model_version.current_stage,
            model_name=MODEL_NAME,
        )
        for probability in probabilities
    ]
    return BatchPredictionResponse(predictions=predictions)
