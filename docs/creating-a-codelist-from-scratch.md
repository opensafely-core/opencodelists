## Creating a codelist from scratch with the builder

Our codelist builder tool helps you create a codelist from scratch,
by searching terms and choosing which matching concepts should be included.

When signed in, click _My codelists_ in the top right of any page.

        my-codelists.png

Then click _Create a codelist_.

        create-a-codelist-1.png

Choose a name for the codelist, and select a coding system from the dropdown.
We currently support codelists using the following coding systems:

- SNOMED-CT
- ICD-10
- CTV3 (Read V3)
- BNF (British National Formulary codes)

Then click _Create_.

        create-form-1.png

You'll be taken to a page that is nearly blank.

        blank.png

You build your codelist by searching for terms, and then choosing which of the matching concepts should be included in the codelist.

        search.png

Any concepts that match your search term, and their descendants, are shown in a hierarchy.

        hierarchy-1.png

In order to keep the page managable, only two levels of the hierarchy are initially visible.
You can drill down the hierarchy by clicking the `⊞` button next to a concept.

        hierarchy-2.png

You include a concept by clicking the `+` button, and exclude a concept by clicking the `-` button.
When you include or exclude a concept, all of its descendants are also included or excluded.
Explicity included/excluded concepts have buttons highlighted blue;
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

Once you have included or excluded every search result, you are able to save your changes.

        save-changes.png

This takes you to the codelist's homepage, where you can edit metadata to provide a description, methodology, and links to references.
