## Creating a codelist from a CSV file

As well as creating a codelist from scratch, you can create one by uploading a CSV file.

From the _My codelists_ page, click _Create a codelist_.

Choose a name for the codelist, select a coding system from the dropdown,
and choose a file to upload from your hard drive.  If you are a member of an organisation, you can also choose an owner for the codelist (your own account or an organisation account).

        create-a-codelist-1.png

The final codelist must be stored in CSV format to be imported 
into [OpenCodelists](https://www.opencodelists.org). The codes must be stored in exactly one column.
There is currently a soft requirement that the first column must contain codes in the chosen coding system, preferably named according to the CSV column names provided in the table above (this limitation will be lifted). The second column is typically a text description of the code. Before uploading a codelist CSV under your OpenSAFELY codelist profile, you should remove the header row as these will be automatically added in a standardised manner.

The codelist page will allow you to upload two columns (a code, and a text description of the code), however, some codelists may require a 'classification' or 'type' column, which classifies the codes into subcategories. For example, when using a codelist for venous thromboemobolism you may wish to classify these codes into deep vein thromboses and pulmonary embolisms, and keep this within a single codelist rather than uploading separate lists for each subcategory of the clinical condition. You can access subcategories of a codelist by using the `filter_codes_by_category` functionality when calling `with_these_clinical_events` as part of your `study_definition`. Uploading more than two columns is currently only possible for the OpenSAFELY core team, so in case this is required for your study please get in touch.

Finally, please avoid filtering on an include or exclude column in Excel when finalising a codelist. Any filters applied will be lost when converted to CSV, and you will end up with all of the codes being uploaded.

When you click _Create_ the codelist will be created and you will be taken to the codelist homepage.

From here, you can edit any metadata.
You can also edit the codelist.

### OPCS-4 codelists

OPCS-4 codelists can not currently be created using the form described above. To add an OPCS-4 codelist, you can navigate to https://www.opencodelists.org/codelist/user/{USERNAME}/add/, replacing {USERNAME} with your OpenCodelists username. Note that the decimal point in the OPCS-4 codes you upload should be excluded.

