## Creating a codelist from scratch with the builder

Our codelist builder tool helps you create a codelist from scratch,
by searching terms and choosing which matching concepts should be included.

When signed in, click _My codelists_ in the top right of any page.

        my-codelists.png

Then click _Create a codelist_.

        create-a-codelist-1.png

Choose a name for the codelist, and select a coding system from the dropdown.  If you are a member of an organisation, you can also choose an owner for the codelist (your own account or an organisation account).

We currently support codelists using the following coding systems:

- SNOMED CT
- ICD-10
- CTV3 (Read V3)
- BNF (British National Formulary codes)
- [Dictionary of Medicines and Devices](#notes-on-building-dmd-codelists)

Then click _Create_.

        create-form-1.png

You'll be taken to a page that is nearly blank.

        blank.png

You build your codelist by searching for terms or codes, and then choosing which of the matching concepts should be included in the codelist.  To search for a code, prefix it with "code:" in the search field.

        search.png

Any concepts that match your search term, and their descendants, are shown in a hierarchy.

        hierarchy-1.png

In order to keep the page manageable, only two levels of the hierarchy are initially visible.
You can drill down the hierarchy by clicking the `⊞` button next to a concept.

        hierarchy-2.png

You include a concept by clicking the `+` button, and exclude a concept by clicking the `-` button.
When you include or exclude a concept, all of its descendants are also included or excluded.
Explicitly included/excluded concepts have buttons highlighted blue;
their descendants have buttons highlighted grey.

        include-exclude.png

If you have included or excluded a result by mistake, you can undo this by clicking on the include or exclude button again.

Sometimes a code can be _in conflict_.
This happens when one of its ancestors in included and another is excluded.
For instance, _Acute severe exacerbation of mild persistent allergic asthma_
is a descendant of both _Mild asthma_ and _Acute asthma_.

        conflict-1.png

You can click on the _..._ to the right of the term to see more details.

        conflict-2.png

There is a link to see just the concepts that are unresolved or in conflict.

        summary.png

All the searches used to build the codelist are displayed, and you can view the results of specific searches again by clicking on them.  _Show all_ returns to the combined results of all searches.

        search-list.png

You can also delete a search by clicking the __x__ next to it.  If you have already included some concepts from that search, they will not be removed.

Once you have included or excluded every search result, you are able to save your changes.
If you are not done with building your codelists, you can _Save draft_ and come back to finish editing it later.

        save-changes.png

If you're done building the codelist, you can save it for review. Note that the __Save for review__ button will be disabled if you have unresolved or conflicting codes in the codelist.  __Save for review__  takes you to the codelist's homepage, where you can edit metadata to provide a description, methodology, links to references, and sign offs.


The codelist is still not publicly available to allow for it to be reviewed and signed off.  You can copy its URL and send it to a another OpenCodelists user to review. The reviewer signs off by editing the codelist's metadata and adding their user and the date in the sign offs section.

        signoffs.png

Procedures for reviewing and signing off codelists may vary between organisations.  For more
information on procedures for building codelists to use in OpenSAFELY research, see the
[OpenSAFELY documentation](https://docs.opensafely.org/en/latest/codelist-intro/).

Once the codelist is reviewed, it can be published, using the __Publish version__ link from the codelist's homepage.  Publishing a codelist version will make that version permanent, and will delete any other draft or in-review versions.

        publish.png

### Notes on building dm+d codelists

The builder functions largely the same with the dm+d coding system as with any other coding system, save for few minor details listed here.

Searches will be executed across **Ingredient**, **VTM** (Virtual Therapeutic Moeity), **VMP** (Virtual Medicinal Product), and **AMP** (Actual Medicinal Products) entities' codes or names (and descriptions, where available).\
Whilst Ingredients are searched, they are not displayed in the results. However, any VMPs containing an Ingredient that matches a search will be displayed (along with their related VTMs and AMPs).

Codes are arranged in the tree view based on a hierarchy of VTM -> VMP -> AMP.\
Due to the large number of AMPs for many VMPs, this part of the tree is not expanded by default but can be by clicking the small plus arrow next to the VMP whose AMPs you wish to view.

Historical dm+d codelists uploaded from csv or converted from Pseudo-BNF codelists are not fully enabled for editing in the builder.\
By default, it is only possible to create new versions of these codelists by uploading a new csv file, or by re-running a conversion from Pseudo-BNF.\
We can, on request, convert these historical codelists into ones that _are_ fully enabled in the builder for creation of new versions.
