## Diffing a codelist

You can compare which codes are present in two different codelist versions using the **diff** function.

By convention, the first codelist version you wish to compare is referred to as the "left hand side" (LHS) of the comparison and the second the "right hand side" (RHS).

Start by going to the page of the codelist version you wish to be the LHS, then append `/diff/` to its URL and then the _Version ID_ of the codelist version you wish to be the RHS.
This RHS version can be a different version of the same codelist, or a version of an entirely different codelist - so long as they are both defined in the same coding system.

For example, in order to compare these two versions of the same codelist:
[https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests-numerical-value/16fdc2da/](https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests-numerical-value/16fdc2da/) and
[https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests-numerical-value/78d4a307/](https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests-numerical-value/78d4a307/),
take the full URL of the first, add `/diff/` then the id of the second ("78d4a307" in this case) to give the diff URL of
[https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests-numerical-value/16fdc2da/diff/78d4a307/](https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests-numerical-value/16fdc2da/diff/78d4a307/).

To compare this codelist version [https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests-numerical-value/16fdc2da/](https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests-numerical-value/16fdc2da/)
to this version of a related but different codelist [https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests/11d2e678/](https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests/11d2e678/)
the resultant diff URL would be [https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests-numerical-value/16fdc2da/diff/11d2e678/](https://www.opencodelists.org/codelist/opensafely/alanine-aminotransferase-alt-tests-numerical-value/16fdc2da/diff/11d2e678/).

N.B: If a codelist version has been assigned a _Tag_, then the URL for that version will default to containing that _Tag_ rather than the _Version ID_.
For the LHS version, this is not a problem, but attempting to use a _Tag_ in place of a _Version ID_ in the diff URL for the RHS may result in unexpected errors.
The _Version ID_ for a codelist version is visible in the table of information at the top of its page.
