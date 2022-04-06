## Viewing a codelist

The homepage of a codelist shows information about what the codelist contains and how it was created,
as well as links to any references and details of who created the codelist.

        codelist-homepage.png


The left hand side of the page displays the codelist's ID and current version information.

A codelist has a __Codelist ID__, which is the canonical ID for the codelist and determines the URL of its homepage.  E.g. the above codelist can be found at <https://opencodelists.org/codelist/opensafely/asplenia>.  This URL will always go to the latest visible version; if you are logged in and you have a version of the codelist in draft or review, this will be shown.  Otherwise, it will go to the latest published version.

A codelist can have multiple versions, each of which has a __Version ID__ (and also a __Version Tag__ for some older codelists). The ID and tag (if applicable) for the version that you are currently viewing is also displayed under the Codelist ID.


The _Full list_ tab shows a searchable list of codes and terms.

        full-list.png

Most codelists have a _Tree_ tab, showing all of the codes in the codelist in the context of other codes in the coding system.
Codes that are not in the codelist are shown greyed out.
This is helpful for seeing whether there are any accidental gaps in the codelist.

        tree.png

For codelists that were created with the builder, there will also be a _Searches_ tab,
showing the search terms that were used to create the codelist.

        searches.png

For all codelists, there are links for downloading a CSV of the codelist and a CSV containing a definition of the codelist.

        download-buttons.png

If there are multiple versions of a codelist, links to these will be displayed on the left hand side.

        versions.png
