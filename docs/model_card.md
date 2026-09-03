# Model Card — Skye8 Credit Risk Model

## What the model does

Given a loan application's terms (amount, term, rate, product, channel,
collateral) plus the borrower's profile (sex, age, sector, household
size, years in business, bank account status, prior loans) and the
disbursing branch's context (region, age, staff count), the model
outputs a calibrated probability that the loan will default. This
probability is thresholded to a decision at serving time (see
`docs/interfaces.md`); the model itself only produces the score.

- **Registry name:** `skye8-credit-risk-model`
- **Promoted version:** 3 (also aliased `production`)
- **Promoted via:** `python -m src.training.registry --metric pr_auc`, an explicit MLflow stage transition + alias assignment (not a manual file copy)
- **Underlying algorithm:** Histogram-based gradient boosting (`sklearn.ensemble.HistGradientBoostingClassifier`), `max_depth=4`, `learning_rate=0.05`, `max_iter=200`
- **Run ID:** `9312ed45996d41de8d856291d6fa7d6f`
- **Git commit at training time:** `942c655022429417c7a25de470db3ab3e1c89c71`
- **Data version (content hash of loans_train.csv + borrowers.csv + branches.csv):** `598a595c5a8bdbbf`

## What it was trained on

- **Source:** `loans_train.csv` only — 30,440 raw rows, disbursed January 2024 – June 2025, all with known outcomes.
- **Cleaning applied before training:** 180 exact duplicate rows dropped, 260 rows referencing a `borrower_id` not present in `borrowers.csv` dropped. Final training population: 30,000 loans.
- **`loans_live.csv` was never used in any training run** — training only ever reads `data/raw/loans_train.csv`, enforced by the pipeline's config, not by convention alone.
- **Held-out evaluation:** stratified 20% holdout of the training population (random_state=42), 6,000 loans, default rate 20.85% (matching the training population's own ~1-in-5 rate).
- **Class imbalance handling:** roughly 1 loan in 5 defaults. `HistGradientBoostingClassifier` has no native `class_weight` parameter, so imbalance was handled via inverse-frequency `sample_weight` at fit time (equivalent in effect to `class_weight="balanced"`, which was used for the two other candidates — logistic regression and random forest — for comparison).

## How it performs

Three candidates were trained, tracked, and compared on the same held-out split:

| Candidate | ROC-AUC | PR-AUC | Brier score | Precision@0.5 | Recall@0.5 |
|---|---|---|---|---|---|
| Logistic regression (balanced) | 0.735 | 0.502 | 0.200 | 0.369 | 0.637 |
| Random forest (balanced) | 0.732 | 0.506 | 0.200 | 0.414 | 0.544 |
| **Gradient boosting (sample-weighted)** — *promoted* | **0.739** | **0.523** | **0.194** | 0.391 | 0.583 |

**Promotion metric: PR-AUC**, not ROC-AUC — with only ~21% of loans defaulting, ROC-AUC is optimistic under imbalance, while PR-AUC reflects ranking quality specifically on the minority (defaulting) class, which is what a credit committee actually cares about. Gradient boosting also had the best (lowest) Brier score, meaning its probability outputs are the best-calibrated of the three, which matters because the API returns a probability the committee will read directly, not just a rank.

### Performance by borrower/branch subgroup (held-out set)

| Group | n | Default rate | ROC-AUC |
|---|---|---|---|
| Sex: F | 3,600 | 21.1% | 0.740 |
| Sex: M | 2,400 | 20.4% | 0.736 |
| Region: Boyo (best) | 255 | 17.6% | 0.808 |
| Region: North | 214 | 16.4% | 0.805 |
| Region: Donga-Mantung (worst) | 511 | 22.1% | 0.688 |
| Region: Littoral | 480 | 21.0% | 0.717 |

Sex shows no material performance gap. **Region does** — ROC-AUC ranges from 0.688 (Donga-Mantung) to 0.808 (Boyo), a 12-point spread. The model is measurably less discriminating for applicants in Donga-Mantung, Littoral, South-West, and West than for Boyo, North, and Menchum.

## Who it may disadvantage

- **Applicants in lower-performing regions** (Donga-Mantung, Littoral, South-West, West — ROC-AUC 0.69–0.72) are scored less reliably than applicants elsewhere. A false-positive or false-negative decision is more likely for these applicants purely because the model discriminates less well there, not because they are inherently riskier.
- **Any group under-represented relative to training volume.** Regions with the smallest holdout counts (North: 214, Boyo: 255, Menchum: 259) have the least statistical confidence behind their reported AUC, even where the point estimate looks strong.
- No sex-based performance gap was found in this evaluation, but this was only checked on the training-period holdout — Stage E's drift analysis on `loans_live.csv` should re-check this, since a shift in the borrower population could reintroduce or reveal a gap not visible here.

## Conditions under which this model must not be used

- **Must not be used on `loans_live.csv` for training** — doing so invalidates the entire monitoring exercise described in Stage E.
- **Must not be used to make final credit decisions unsupervised in regions with ROC-AUC below ~0.70** (currently Donga-Mantung) without a compensating manual review step, until a region-aware retraining or recalibration is done.
- **Must not be used past the retraining trigger defined in `docs/retraining_policy.md`** — see that document for the specific PSI/performance threshold.
- **Must not be used without the version tag in the response** — any deployment path that strips the model version from the API response breaks traceability and violates the acceptance criteria.
