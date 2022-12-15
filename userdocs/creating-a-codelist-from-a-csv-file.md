## Creating a codelist from a CSV file

As well as creating a codelist from scratch, you can create one by uploading a CSV file.

From the _My codelists_ page, click _Create a codelist_.

Choose a name for the codelist, select a coding system from the dropdown, and choose a file to upload from your hard drive.

To create an OPCS-4 codelist, please see the notes at the bottom of this page.

If you are a member of an organisation, you can also choose an owner for the codelist (your own account or an organisation account).

        create-a-codelist-1.png

### Requirements for uploading codelists to OpenCodelists

* Store the final codelist in CSV format.
* Store codes in exactly one column.
* Remove the header row. Standardised headers will automatically be added for you.
* There is currently a soft requirement that the first column must contain codes in the chosen coding system. These should preferably be named according to the CSV column names provided in the table above. (We plan to eventually remove this requirement.) The second column is typically a text description of the code.

### More about codelist columns

The codelist page allow you to upload two columns:

* a code
* a text description of the code

However, some codelists may require a 'classification' or 'type' column, which classifies the codes into subcategories. For example, when using a codelist for venous thromboembolism, you may wish to classify these codes into deep vein thromboses and pulmonary embolisms. By using subcategories, you can keep all the codes in a single codelist, rather than uploading separate lists for each clinical subcategory. In your study definition, the `filter_codes_by_category` functionality allows access to the subcategories of a codelist.

**Uploading more than two columns is currently only possible for the OpenSAFELY core team. If your study requires this feature, [please get in touch](https://www.opensafely.org/contact/).**

### Potential issues when editing codelists in spreadsheet software, such as Excel

Avoid:

* filtering on an include or exclude column when finalising a codelist. Applied filters are lost in CSV conversion: *all* of the codes will be uploaded.
* editing SNOMED CT codelists. The codes get rounded.

When you click _Create_ the codelist will be created and you will be taken to the codelist homepage.

From here, you can edit any metadata.
You can also edit the codelist.

### Adding an OPCS-4 or dm+d codelist

Note: OPCS-4 and dm+d codelists can not currently be created using the form described above.

To add an OPCS-4 or dm+d codelist, navigate to `https://www.opencodelists.org/codelist/{ACCOUNT}/add/` — where `{ACCOUNT}` in the URL is substituted with one of the following options:

* Either `user/{username}` where `username` is your OpenCodelists username, to add the codelist to your personal account
* Or the name of the organisation your account is associated with, to add the codelist under the organisation.

**The OPCS-4 codes you upload should NOT include the decimal point.**
