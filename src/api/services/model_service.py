from io import StringIO

import mlflow
import mlflow.sklearn
import pandas as pd
from fastapi import status
from sqlalchemy.orm import Session

from api.schema.model import (
    BatchPredictionResponse,
    PredictionRequest,
    PredictionResponse,
)
from api.utils.model_registry import get_loaded_model_details
from api.utils.prediction_data import PredictionDataError, prepare_prediction_dataframe

# Resolve the production alias once when the service starts so every response
# identifies the exact model version used for that process.
model_details = get_loaded_model_details()
model = mlflow.sklearn.load_model("mlruns/1/models/m-777ba5a7a77e420d9aa99cb2a75ce742/artifacts")


class BatchPredictionError(Exception):
    """Service-level error containing an HTTP status and client-safe detail."""

    def __init__(self, detail: object, status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT):
        self.detail = detail
        self.status_code = status_code
        super().__init__(str(detail))


def get_prediction(features: PredictionRequest) -> PredictionResponse:
    """Predict one already-validated, model-shaped application record."""
    df = pd.DataFrame([features.model_dump()])
    response = model.predict_proba(df)
    probability = float(response[0, 1])
    return PredictionResponse(
        probability_of_default=probability,
        decision="review" if probability < 0.5 else "decline",
        model_version=model_details["model_version"],
        model_stage=model_details["model_stage"],
        model_name=model_details["model_name"],
    )


def get_batch_predictions(features: list[PredictionRequest]) -> list[PredictionResponse]:
    """Predict multiple already-validated application records in one call."""
    # A single DataFrame lets sklearn transform and score the complete batch.
    df = pd.DataFrame([feature.model_dump() for feature in features])
    probabilities = model.predict_proba(df)[:, 1]

    return [
        PredictionResponse(
            probability_of_default=float(probability),
            decision="review" if probability < 0.5 else "decline",
            model_version=model_details["model_version"],
            model_stage=model_details["model_stage"],
            model_name=model_details["model_name"],
        )
        for probability in probabilities
    ]


def predict_batch_csv(
    contents: bytes,
    content_type: str | None,
    session: Session,
) -> BatchPredictionResponse:
    """Parse, enrich, validate, and score an uploaded CSV file."""
    if content_type not in {"text/csv", "application/csv", None}:
        raise BatchPredictionError(
            "file must be a CSV",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    # Decode UTF-8 CSV files, including files with a UTF-8 BOM from Excel.
    try:
        frame = pd.read_csv(StringIO(contents.decode("utf-8-sig")))
    except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as error:
        raise BatchPredictionError(f"invalid CSV file: {error}") from error

    if frame.empty:
        raise BatchPredictionError("file must contain at least one data row")

    # The utility supports both prepared feature files and raw loan files.
    # Raw loan files use the session to fetch borrower and branch features.
    try:
        prepared = prepare_prediction_dataframe(frame, session)
    except PredictionDataError as error:
        raise BatchPredictionError(error.detail) from error

    probabilities = model.predict_proba(prepared)[:, 1]
    # Keep response metadata consistent across every row in this batch.
    predictions = [
        PredictionResponse(
            probability_of_default=float(probability),
            decision="review" if probability < 0.5 else "decline",
            model_version=model_details["model_version"],
            model_stage=model_details["model_stage"],
            model_name=model_details["model_name"],
        )
        for probability in probabilities
    ]
    return BatchPredictionResponse(predictions=predictions)
