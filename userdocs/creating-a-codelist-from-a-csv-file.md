## Creating a codelist from a CSV file

As well as creating a codelist from scratch, you can create one by uploading a CSV file.

From the _My codelists_ page, click _Create a codelist_.

1. Choose a name for the codelist.
1. Select a coding system.
1. Press the `+` next to "Upload CSV" in the "Upload a CSV" section to show the CSV upload options.
1. Choose a file to upload from your hard drive.
1. Specify whether or not your CSV has a header row or not.

        create-new-codelist-page-csv.png

To create an OPCS-4 codelist, please see the [notes elsewhere on this documentation page](#adding-an-opcs-4-codelist).

If you are a member of an organisation, you can also choose an owner for the codelist (your own account or an organisation account).

        create-codelist-button.png

### Requirements for uploading codelists to OpenCodelists via the "Create a codelist" form

* Store the final codelist in CSV format.
* Store codes in the first column: only the first column is processed by the form.
* Check whether or not your codelist has a header row: you will need to specify this on upload.

### Potential issues when editing codelists in spreadsheet software, such as Excel

Avoid:

* filtering on an include or exclude column when finalising a codelist. Applied filters are lost in CSV conversion: *all* of the codes will be uploaded.
* editing SNOMED CT codelists. The codes get rounded.

When you click _Create_ the codelist will be created and you will be taken to the codelist homepage.

From here, you can edit any metadata.
You can also edit the codelist.

We are aware of an issue whereby Excel can truncate or round dm+d IDs, turning them into invalid IDs. This is due to Excel's interpretation of this column as a number type insufficiently large to contain a dm+d ID. For this reason, opening dm+d codelist files in Excel should be avoided wherever possible.

Where it is unavoidable to do so, rather than opening a dm+d codelist csv file directly in Excel (such as through the Open dialogue or from the file explorer), we recommend opening a blank Excel workbook and using the "Import data from Text/CSV" feature. To avoid the problematic rounding/truncation behaviour described above, specify the data type of the dm+d id column as "Text" during the import process.

### Adding an OPCS-4 codelist

Note: OPCS-4 codelists can not currently be created using the "Create a codelist" form described above.

To add an OPCS-4 codelist, navigate to `https://www.opencodelists.org/codelist/{ACCOUNT}/add/` — where `{ACCOUNT}` in the URL is substituted with one of the following options:

* Either `user/{username}` where `username` is your OpenCodelists username, to add the codelist to your personal account
* Or the name of the organisation your account is associated with, to add the codelist under the organisation.

**The OPCS-4 codes you upload should NOT include the decimal point.**

#### More about codelist columns

The codelist `/add/` page allow you to upload multiple columns such as:

* a code
* a text description of the code

Some codelists may require a 'classification' or 'type' column, which classifies the codes into subcategories. For example, when using a codelist for venous thromboembolism, you may wish to classify these codes into deep vein thromboses and pulmonary embolisms. By using subcategories, you can keep all the codes in a single codelist, rather than uploading separate lists for each clinical subcategory. The OpenSAFELY documentation has [guidance for using category columns with OpenSAFELY ehrQL dataset definition](https://docs.opensafely.org/ehrql/how-to/examples/#using-codelists-with-category-columns).
