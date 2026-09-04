import pandas as pd
from pydantic import ValidationError

from api.schema.model import PredictionRequest


class PredictionDataError(ValueError):
    def __init__(self, detail: object):
        self.detail = detail
        super().__init__(str(detail))


def prepare_prediction_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate a DataFrame and return only the model's required columns.

    Extra columns, such as loan_id or officer_id, are ignored. Each row must
    contain the complete PredictionRequest feature contract.
    """
    if frame.empty:
        raise PredictionDataError("file must contain at least one data row")

    required_fields = set(PredictionRequest.model_fields)
    missing_fields = sorted(required_fields - set(frame.columns))
    if missing_fields:
        raise PredictionDataError({"missing_fields": missing_fields})

    features = []
    validation_errors = []
    for row_number, record in enumerate(frame.to_dict(orient="records"), start=2):
        try:
            features.append(PredictionRequest.model_validate(record))
        except ValidationError as error:
            validation_errors.append({"row": row_number, "errors": error.errors()})

    if validation_errors:
        raise PredictionDataError(validation_errors)

    return pd.DataFrame([feature.model_dump() for feature in features])
