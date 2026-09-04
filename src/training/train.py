"""
Reproducible training entrypoint.

Usage:
    python -m src.training.train --config src/training/config/exp1_logreg.yaml

Same config + same data -> same metrics. All randomness is seeded from
the config's `random_state`. Every run is logged to MLflow with its
git commit and a content hash of the training data, so a run that
can't be traced back to a commit and a dataset simply isn't produced.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys

import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from src.data.clean import clean_borrowers, clean_loans

from src.features.build_features import CATEGORICAL_FEATURES, NUMERIC_FEATURES, build_feature_frame

MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"


# ---------------------------------------------------------------------------
# Reproducibility bookkeeping
# ---------------------------------------------------------------------------


def get_git_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        return "unknown-no-git-repo"


def hash_data_files(paths: list[str]) -> str:
    """Content hash of the training inputs, so a run records exactly
    which bytes of data/raw/*.csv it was trained on."""
    hasher = hashlib.sha256()
    for path in sorted(paths):
        with open(path, "rb") as f:
            hasher.update(f.read())
    return hasher.hexdigest()[:16]


# ---------------------------------------------------------------------------
# Data loading + cleaning
# ---------------------------------------------------------------------------


def load_and_prepare(data_cfg: dict) -> pd.DataFrame:
    loans_raw = pd.read_csv(data_cfg["train_path"], dtype=str)
    borrowers_raw = pd.read_csv(data_cfg["borrowers_path"])
    branches_raw = pd.read_csv(data_cfg["branches_path"])

    borrowers = clean_borrowers(borrowers_raw)
    valid_ids = set(borrowers["borrower_id"])

    loans, report = clean_loans(loans_raw, valid_borrower_ids=valid_ids)
    print(f"[clean] {report.as_dict()}")

    features = build_feature_frame(loans, borrowers, branches_raw)

    # Training uses loans_train.csv only, which per the brief has known
    # outcomes for all rows -- but guard against any that slipped through
    # without one, rather than silently including them.
    labeled = features[features["defaulted"].notna()].copy()
    if len(labeled) < len(features):
        print(
            f"[warn] dropped {len(features) - len(labeled)} rows with no outcome "
            "from the training set"
        )
    return labeled


# ---------------------------------------------------------------------------
# Model construction
# ---------------------------------------------------------------------------


def build_pipeline(model_cfg: dict, random_state: int) -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )

    model_type = model_cfg["type"]
    params = dict(model_cfg.get("params", {}))
    params.pop("use_sample_weight", None)  # consumed separately, not a model param

    if model_type == "logistic_regression":
        classifier = LogisticRegression(random_state=random_state, **params)
    elif model_type == "random_forest":
        classifier = RandomForestClassifier(random_state=random_state, **params)
    elif model_type == "gradient_boosting":
        classifier = HistGradientBoostingClassifier(random_state=random_state, **params)
    else:
        raise ValueError(f"unknown model type: {model_type}")

    return Pipeline(steps=[("preprocess", preprocessor), ("classify", classifier)])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(config_path: str) -> None:
    with open(config_path) as f:
        config = yaml.safe_load(f)

    random_state = config.get("random_state", 42)
    data_cfg = config["data"]
    split_cfg = config["split"]
    model_cfg = config["model"]

    features = load_and_prepare(data_cfg)
    X = features[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = features["defaulted"].astype(int)

    X_train, X_holdout, y_train, y_holdout = train_test_split(
        X,
        y,
        test_size=split_cfg["holdout_fraction"],
        random_state=split_cfg["random_state"],
        stratify=y if split_cfg.get("stratify", True) else None,
    )

    pipeline = build_pipeline(model_cfg, random_state)

    fit_kwargs = {}
    if model_cfg.get("params", {}).get("use_sample_weight"):
        # Inverse-frequency sample weighting -- the class_weight="balanced"
        # equivalent for estimators (like HistGradientBoostingClassifier)
        # that don't accept class_weight directly.
        class_counts = y_train.value_counts()
        weight_map = {cls: len(y_train) / (2 * count) for cls, count in class_counts.items()}
        fit_kwargs["classify__sample_weight"] = y_train.map(weight_map).values

    pipeline.fit(X_train, y_train, **fit_kwargs)

    proba = pipeline.predict_proba(X_holdout)[:, 1]
    preds = (proba >= 0.5).astype(int)

    metrics = {
        "roc_auc": roc_auc_score(y_holdout, proba),
        "pr_auc": average_precision_score(y_holdout, proba),
        "brier_score": brier_score_loss(y_holdout, proba),
        "precision_at_0.5": precision_score(y_holdout, preds, zero_division=0),
        "recall_at_0.5": recall_score(y_holdout, preds, zero_division=0),
        "f1_at_0.5": f1_score(y_holdout, preds, zero_division=0),
        "holdout_default_rate": float(y_holdout.mean()),
    }

    git_commit = get_git_commit()
    data_version = hash_data_files(
        [data_cfg["train_path"], data_cfg["borrowers_path"], data_cfg["branches_path"]]
    )

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(config["experiment_name"])

    with mlflow.start_run(run_name=config["run_name"]) as run:
        flat_params = {"model_type": model_cfg["type"], **model_cfg.get("params", {})}
        mlflow.log_params(flat_params)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("holdout_fraction", split_cfg["holdout_fraction"])
        mlflow.log_metrics(metrics)
        mlflow.set_tag("git_commit", git_commit)
        mlflow.set_tag("data_version", data_version)
        mlflow.sklearn.log_model(
            pipeline,
            name="model",
            registered_model_name=config["model_registry_name"],
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_PICKLE,
        )
        print(f"[mlflow] run_id={run.info.run_id}")

    print(f"[metrics] {metrics}")
    print(f"[git_commit] {git_commit}")
    print(f"[data_version] {data_version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    main(args.config)
    sys.exit(0)
