\# Production Model Drift Incident Report



\## Incident summary



The production credit-risk model showed significant degradation after deployment. The production period differs materially from the training period, with both substantial input drift and a higher observed default rate.



\## Evidence



Training default rate: 20.86%



Production known-outcome default rate: 31.44%



Training accuracy: 73.44%



Production accuracy: 57.13%



Training F1: 75.11%



Production F1: 58.66%



Severe PSI:

\- amount\_xaf: 0.4380

\- branch\_age\_years: 0.7599



Moderate PSI:

\- declared\_income\_xaf: 0.1604

\- loan\_to\_income\_ratio: 0.2486



\## Diagnosis



The production period exhibits clear covariate drift, especially in loan amount and branch age. The outcome distribution also changed: the overall default rate increased from 20.86% to 31.44%.



The increase in default rates within comparable channels provides evidence that the change is not only a shift in feature distributions. For example, mobile-channel defaults increased from 24.74% to 32.41%, branch defaults increased from 19.89% to 30.34%, and field-agent defaults increased from 20.34% to 28.75%.



This indicates a material change in the production environment and evidence of a change in the relationship between observed borrower/application characteristics and default risk.



\## Impact



The model's F1 score decreased from 75.11% to 58.66%, increasing the risk of incorrect credit decisions.



\## Response



Monitoring thresholds were defined to trigger retraining when severe PSI or unacceptable production performance is observed.



\## Prevention



The monitoring process should run periodically on production traffic, track feature drift and labelled performance, and trigger model review before performance deteriorates further.

