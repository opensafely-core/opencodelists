## Creating a codelist from scratch with the codelist builder

Our codelist builder tool helps you create a codelist from scratch,
by searching terms and choosing which matching concepts should be included.

When signed in, click _My codelists_ in the top right of any page.

        my-codelists.png

Then click _Create a codelist_.

        create-codelist-button.png

This will take you to a form to create a new codelist.

        create-new-codelist-page.png

Choose a name for the codelist, and select a coding system. We currently support codelists using the following coding systems:

- SNOMED CT
- ICD-10
- CTV3 (Read V3)
- BNF (British National Formulary codes)
- [Dictionary of Medicines and Devices](#notes-on-building-dmd-codelists)

If you are a member of an organisation, you can also choose an owner for the codelist (your own account or an organisation account).

Then click _Create_.

You'll be taken to the codelist builder tool, with instructions displayed.

        codelist-builder-empty.png

Build your codelist by searching for terms or codes, and then choosing which of the matching concepts should be included in the codelist. Choose between searching for a code and a term with the __Term__ and __Code__ buttons above the search text entry.

        codelist-builder-search.png

Any concepts that match your search term, and their descendants, are shown in a hierarchy.

        hierarchy-initial.png

To keep the page manageable, only two levels of the hierarchy are initially visible.
You can further expand the hierarchy by clicking the `⊞` button next to concepts.

        hierarchy-expanded.png

Include a concept by clicking the `+` button, and exclude a concept by clicking the `−` button.
When you include or exclude a concept, all of its descendants are also included or excluded.
Explicitly included/excluded concepts have buttons highlighted blue;
their descendants have buttons highlighted grey.

        hierarchy-include-exclude.png

To undo inclusion or exclusion of a result, click on the include or exclude button again.

Sometimes a code can be _in conflict_.
This happens when one of its ancestors in included and another is excluded.
For instance, _Arthritis of elbow_ is in conflict
because it is both a descendant of the included _Arthropathy of elbow_, and the excluded _Elbow joint inflamed_.

        hierarchy-conflict.png

Hover on a conflicted code and click  _More info_ to the right of the term to see the conflict details.

        more-info-hover.png

        more-info-conflict-modal.png

Under _Concepts found_ there are a link to filter the builder view to conflicted or unresolved concepts.

        concepts-filter.png

All the searches used to build the codelist are displayed under __Previous searches__. View the results of specific searches again by clicking on them. The  _show all_ button returns to the combined results of all searches.

        previous-searches.png

Delete a search by clicking the __Remove__ button next to it. If you have already included some concepts from that search, they will not be removed.

The save buttons are at the top of the builder:

        save-buttons.png

If you have not yet completed your codelist, you can _Save draft_ at any time, and return to edit it later.
Once you have included or excluded every search result and have no remaining conflicts, the __Save for review__ button will be enabled.
The __Save for review__ button takes you to the codelist's homepage, where you can edit metadata to provide:

* a description
* methodology
* links to references
* codelist sign offs

The codelist is still not publicly available to allow for it to be reviewed and signed off. You can copy its URL and send it to a another OpenCodelists user to review. The reviewer signs off by editing the codelist's metadata, and adding their user and the date in the sign offs section.

        sign-off.png

Procedures for reviewing and signing off codelists may vary between organisations. For more
information on procedures for building codelists to use in OpenSAFELY research, see the
[OpenSAFELY documentation](https://docs.opensafely.org/en/latest/codelist-intro/).

Once the codelist is reviewed, it can be published, using the __Publish version__ button from the codelist's homepage:

        version-buttons.png

Publishing a codelist version will make that version permanent, and will delete any other draft or in-review versions.

### Notes on building dm+d codelists

The builder functions largely the same with the dm+d coding system as with any other coding system, save for few minor details listed here.

Searches will be executed across **Ingredient**, **VTM** (Virtual Therapeutic Moeity), **VMP** (Virtual Medicinal Product), and **AMP** (Actual Medicinal Products) entities' codes or names (and descriptions, where available).\
Whilst Ingredients are searched, they are not displayed in the results. However, any VMPs containing an Ingredient that matches a search will be displayed (along with their related VTMs and AMPs).

Codes are arranged in the tree view based on a hierarchy of VTM -> VMP -> AMP.\
Due to the large number of AMPs for many VMPs, this part of the tree is not expanded by default but can be by clicking the small plus arrow next to the VMP whose AMPs you wish to view.

Historical dm+d codelists uploaded from csv or converted from Pseudo-BNF codelists are not fully enabled for editing in the builder.\
By default, it is only possible to create new versions of these codelists by uploading a new csv file, or by re-running a conversion from Pseudo-BNF.\
We can, on request, convert these historical codelists into ones that _are_ fully enabled in the builder for creation of new versions.
