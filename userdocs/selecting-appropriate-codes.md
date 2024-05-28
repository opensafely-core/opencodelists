## Selecting appropriate codes for your codelist

Choosing which codes to include in your codelist can be challenging without understanding their usage in clinical practice. Some clinical activities are represented by a single code, while others may require a comprehensive list of codes to accurately capture the intended clinical activity. Even a single incorrectly included or omitted code could potentially lead to vastly different results when using the codelist to query electronic health record data.

Some of the common pitfalls when selecting appropriate codes include:

* **Including similar-sounding but unrelated codes**. For instance, ocular hypertension, which pertains to high fluid pressure within the eye, and is not appropriate for a codelist intended to capture high blood pressure.
* **Omitting synonyms**. For example, when defining a codelist for sore throat, it is essential to include clinical codes which describe pharyngitis as well.
* **Misunderstanding study intent**. Selecting an appropriate codelist requires careful consideration of which patients are relevant to the research aims. For example; the decision to include or exclude gestational diabetes in a diabetes codelist, for instance, may vary depending on the specific study or context.
* **Use of non-specific codes**. Some codes might be useful to improve sensitivity of a study but care needs to be taken to consider potential negative impact on specificity. For example, sore throat is a potential symptom of Group A Strep infection but is also a symptom of many other conditions, if including this in a study it is likely other codelists (for example antibiotics for Group A Strep treatment) would need to be used to maintain an appropriate level of specificity.

To avoid these pitfalls we recommend:

* Clearly defining your clinical feature of interest. This may include specific features you do not want to capture.
* Specifying the synonyms that may be used for your clinical feature of interest.
* Considering balacing sensitivity and specificity of the selected codes
* Looking for similar codelists on OpenCodelists and understanding what methodology they used for their selection of codes.
* Where available, using published data on code usage to understand how a clinical area is coded in practice. This doesn't exist for all code terminologies, but helpfully, [NHS Digital provides a dataset on SNOMED CT code usage in primary care](https://digital.nhs.uk/data-and-information/publications/statistical/mi-snomed-code-usage-in-primary-care), which includes data since 2011. This dataset includes annual counts of how often each SNOMED CT code is recorded in GP patient records across England. You can explore recorded usage of individual codes or entire codelists, including those on OpenCodelists, using [this prototype SNOMED CT code usage explorer](https://snomed-code-usage.streamlit.app/). Note, however, that low or no usage for a code may not be indicative of its future use.

You can read more about codelists and their construction in [the Bennett Institute blog series on clinical codes](https://www.bennett.ox.ac.uk/blog/series/clinical-codes/).
