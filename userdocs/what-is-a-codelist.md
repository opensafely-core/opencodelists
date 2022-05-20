## What is a codelist?

A codelist is a set of codes which can be recorded in clinical systems, representing data such as:
* Patient Demographics - e.g. Age, Ethnicity
* Medicines - e.g. Paracetamol, Morphine
* Condition Diagnoses - e.g. Crohn's Disease, Bipolar disorder
* Symptoms - e.g. Headache, Blood in urine
* Test Results - e.g. Potassium level, Abnormal ECG
* Procedures - e.g. Coronary artery bypass graft, Hysterectomy
* Activities - e.g. Medication review, Consultation via video

Codelists are used in almost all studies in OpenSAFELY - and other health data research -
to select patients with activities and conditions of interest within the dataset(s) being used. 

* Codelists each use a _coding system_ such as SNOMED, DM&D (dictionary of medicines and devices), CTv3 (Clinical Terms v3), etc.
* Codelists can often be large, in order to capture the many possible codes that could represent a certain activity or condition.
* Creating or selecting a codelist can often be very nuanced, 
e.g. whether a codelist for "diabetes" should _include_ or _exclude_ gestational diabetes may vary according to the study. 
* Sometimes a combination of codelists of different types may be required to fully capture patients with certain conditions, 
e.g. _medications_ for asthma (DM&D), _diagnoses_ of asthma in primary care (SNOMED), _diagnoses_ of asthma in a hospital admission (ICD-10).
