import mlflow
from mlflow.tracking import MlflowClient

MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
MODEL_NAME = "skye8-credit-risk-model"
MODEL_ALIAS = "production"

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
client = MlflowClient()

model_version = client.get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
LOADED_MODEL_DETAILS = {
    "model_name": MODEL_NAME,
    "model_version": str(model_version.version),
    "model_stage": model_version.current_stage or "None",
    "model_alias": MODEL_ALIAS,
}


def get_loaded_model_details() -> dict[str, str]:
    """Return the registry metadata for the model loaded by the API."""
    return dict(LOADED_MODEL_DETAILS)
