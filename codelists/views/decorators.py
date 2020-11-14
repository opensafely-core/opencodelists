from functools import wraps

from django.shortcuts import get_object_or_404

from opencodelists.models import Organisation

from ..models import Codelist, CodelistVersion


def load_organisation(view_fn):
    """Load an Organisation (or raise 404) and pass it to view function.

    Assumes that the view function get a single parameter from the URL,
    organisation_slug.
    """

    @wraps(view_fn)
    def wrapped_view(request, organisation_slug):
        org = get_object_or_404(Organisation, slug=organisation_slug)
        return view_fn(request, org)

    return wrapped_view


def load_codelist(view_fn):
    """Load a Codelist (or raise 404) and pass it to view function.

    Assumes that the view function get a two parameters from the URL,
    organisation_slug and codelist_slug.
    """

    @wraps(view_fn)
    def wrapped_view(request, organisation_slug, codelist_slug):
        cl = get_object_or_404(
            Codelist,
            organisation_id=organisation_slug,
            slug=codelist_slug,
        )

        return view_fn(request, cl)

    return wrapped_view


def load_version(view_fn):
    """Load a CodelistVersion (or raise 404) and pass it to view function.

    Assumes that the view function get a three parameters from the URL,
    organisation_slug, codelist_slug, and qualified_version_str.
    """

    @wraps(view_fn)
    def wrapped_view(request, organisation_slug, codelist_slug, qualified_version_str):
        if qualified_version_str[-6:] == "-draft":
            expect_draft = True
            version_str = qualified_version_str[:-6]
        else:
            expect_draft = False
            version_str = qualified_version_str

        clv = get_object_or_404(
            CodelistVersion.objects,
            codelist__organisation_id=organisation_slug,
            codelist__slug=codelist_slug,
            version_str=version_str,
        )

        return view_fn(request, clv, expect_draft)

    return wrapped_view
