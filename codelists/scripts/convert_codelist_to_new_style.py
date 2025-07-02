"""Convert a Codelist to the new style, by creating a new CodelistVersion.

./manage.py runscript convert_codelist_to_new_style --script-args <organisation_slug> <codelist_slug>
"""

from codelists.actions import convert_codelist_to_new_style
from codelists.models import Handle


def run(organisation_slug, codelist_slug):
    handle = Handle.objects.get(organisation=organisation_slug, slug=codelist_slug)
    convert_codelist_to_new_style(codelist=handle.codelist)
