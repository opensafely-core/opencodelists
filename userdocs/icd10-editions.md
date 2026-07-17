## ICD-10 editions and updating codelists

OpenCodelists combines the two ICD-10 editions used in OpenSAFELY data:

* the [NHS-modified 2016 edition](https://classbrowser.nhs.uk/#/book/ICD-10-5TH-Edition) used in HES/APCS hospital admissions data; and
* the [WHO 2019 edition](https://icd.who.int/browse10/2019/en) used in ONS deaths data.

### Why have you combined the two editions?

Most ICD-10 codes have the same meaning in both editions. Codelists are also
often reused with more than one dataset. Asking people to choose an edition
when creating a codelist would likely be confusing, and would lead to parallel
codelists. It would be easy to use a codelist built against the wrong edition,
which could lead to missed events.

OpenCodelists therefore provides a single ICD-10 dictionary containing codes
from both editions. This means that in most cases, a single codelist can be
used against any dataset. Where there are differences, OpenCodelists provides
warnings and guidance.
<!-- alerting users to the small number of differences that need review. The NHS 2016
description is displayed by default because ICD-10 codelists are most often
used with admissions data. Where descriptions differ, select **More info** for
the code to see both editions. -->

### How have you combined them?

Most codes are identical in both editions. The differences that need further
attention are:

1. **Moved codes:** Concepts with _different codes_ in different editions
1. **Changed definitions:** Codes with a _different definition_

#### Moved codes

There are ~20 codes that have moved between the two editions. For example, the
concept of "Pneumocystosis" is coded as
[B59 in the 2016 edition](https://classbrowser.nhs.uk/#/book/ICD-10-5TH-Edition/vol1/block-b50-b64.htm+B59)
, but
[B48.5 in the 2019 edition](https://icd.who.int/browse10/2019/en#/B48.5).
Fortunately, there are no instances where a code has been reused for a different
concept in the other edition. This means that it is safe to include the code
from both editions in a codelist, irrespective of which edition is used in the
dataset being queried. A codelist with both `B59` and `B48.5` will match events
in ONS deaths with `B48.5` and events in admissions data with `B59`.

#### Changed definitions

There are two categories of changed definition:

- minor wording differences/typos, and
- clinically significant differences.

The former are not a concern, e.g.
["Cow milk"](https://icd.who.int/browse10/2019/en#/P71.0) vs
["Cow's milk"](https://classbrowser.nhs.uk/#/book/ICD-10-5TH-Edition/vol1/block-p70-p74.htm+P71.0).
However, the latter can lead to a codelist including events incorrectly. For
example, the code `X59.0` will match fractures in ONS deaths because the 2019 edition defines it as
["Exposure to unspecified factor _**causing fracture**_"](https://icd.who.int/browse10/2019/en#/X59.0)
but that same code in admissions data is defined in the 2016 edition as
["Exposure to unspecified factor (occurrence at home)"](https://classbrowser.nhs.uk/#/book/ICD-10-5TH-Edition/vol1/block-x50-x59.htm+X59.0).
A codelist for fractures would want to include that code for ONS deaths, but
exclude it for admissions data.

Where the same code has a different definition we:

- store both definitions in the OpenCodelists dictionary,
- display the NHS 2016 definition by default,
- provide both definitions in the **More info** panel, and
- if the definitions are more than minor wording differences, we display a
 warning banner with instructions on how to proceed.


### Understanding the warning messages

We provide warnings when:

- a codelist includes a code that has moved between editions, and does not also
 contain the code for the other edition, or
- a codelist includes a code that has conflicting definitions in the two
 editions.

Warnings mean that a codelist needs review. They do not necessarily mean that
the codelist is wrong.

### If a concept moved to a different code

The warning looks like this:

        icd10-incomplete-codelist-warning.png

The warning lists the codes used for the concept in each edition and highlights
the codes missing from the codelist.

For a codelist intended to work across admissions and deaths data, the safest
approach is normally to include all the listed codes. Codes identified as moved
are not reused for unrelated conditions in the other edition.

Check every suggested code against the purpose of the codelist before adding
it. Some groups need a more specific decision. For example, the 2019 edition
divides irritable bowel syndrome into more detailed subcategories, so a
codelist specifically about diarrhoea or constipation may need only part of the
group.

If there is a valid reason to not include all codes for a concept, then the
warning will remain. It is therefore important to update the codelist methodology
to explain the reason for the decision for future reference.

### If a code has conflicting definitions

The warning looks like this:

        icd10-conflicting-definitions-warning.png

The warning lists the code and both definitions. It is important to check the
definitions against the purpose of the codelist and the dataset(s) it will be
used with. The codelist may need to be updated to exclude the code, depending
on which of the following situations applies:

* **Both definitions are relevant:** If the purpose of the codelist is such
 that both definitions are appropriate, then retain the code in the codelist.
 The warning will remain, so it is important to record the reason for the
 decision in the codelist methodology for future reference.
* **Only the NHS 2016 definition is relevant:**
  * If the codelist is intended for **admissions data only**, then include the code
   in the codelist. Please clearly state in the methodology that the codelist
   is intended for admissions data only, and that it should not be used for deaths data.
  * If the codelist is intended for **ONS deaths data only**, then exclude the code
   from the codelist. Please clearly state in the methodology that the codelist
   is intended for deaths data only, and that it should not be used for admissions data.
  * If the codelist is intended for **both admissions and deaths data** then you
   will need to create separate codelists for each dataset. Please clearly state
   in the methodology of each which dataset it is intended for, and that it should not be used for the other dataset.
* **Only the WHO 2019 definition is relevant:**
  * If the codelist is intended for **ONS deaths data only**, then include the code
   in the codelist. Please clearly state in the methodology that the codelist
   is intended for deaths data only, and that it should not be used for admissions data.
  * If the codelist is intended for **admissions data only**, then exclude the code
   from the codelist. Please clearly state in the methodology that the codelist
   is intended for admissions data only, and that it should not be used for deaths data.
  * If the codelist is intended for **both admissions and deaths data** then you
   will need to create separate codelists for each dataset. Please clearly state
   in the methodology of each which dataset it is intended for, and that it should not be used for the other dataset.
