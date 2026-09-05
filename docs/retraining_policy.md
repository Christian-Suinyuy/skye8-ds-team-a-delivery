Retraining trigger



The production model must be reviewed for retraining when either condition occurs:



1\. PSI for any critical input feature exceeds 0.25 (severe drift), or

2\. F1 score on labelled production outcomes falls below 0.65.



The model should be withdrawn from automated decisions if production F1 falls below 0.55 or if severe drift persists across two consecutive monitoring periods.



Rationale:

The current production F1 is 0.5866, compared with 0.7511 on the training-period evaluation. This represents a substantial degradation in model performance. The production data also shows severe PSI for amount\_xaf (0.4380) and branch\_age\_years (0.7599). These thresholds therefore provide an early warning before model reliability deteriorates further.

