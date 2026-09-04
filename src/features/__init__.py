# Serving — owned by Banboye Christian.
#
# This package should expose the FastAPI app: prediction endpoint,
# batch endpoint, health endpoint, request validation, and request
# logging (Stage C of the brief).
#
# It should load the production model via:
#   mlflow.sklearn.load_model("models:/skye8-credit-risk-model@production")
# and call src.data.clean.clean_single_record() and
# src.features.build_features.build_feature_record() for cleaning/
# feature-building, rather than re-implementing either — see
# docs/interfaces.md for the agreed request/response contract.
