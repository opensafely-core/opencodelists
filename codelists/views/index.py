from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, render

from opencodelists.list_utils import flatten
from opencodelists.models import Organisation

from ..models import Handle, Status


def index(request, organisation_slug=None, status=Status.PUBLISHED):
    handles = Handle.objects.filter(is_current=True, codelist__is_private=False)

    q = request.GET.get("q")
    if q:
        # We search for codelists whose name/description contain all the words
        # in the query string, or the whole phrase if it is quoted. We then
        # rank the results as follows:
        # 1. Exact phrase match in name (rank 1)
        # 2. All words in name (rank 2)
        # 3. Any word in name (rank 3)
        # 4. Any word in description (rank 4)

        search_words = q.split()

        whole_phrase_in_name = Q(name__icontains=q)
        all_words_in_name = Q()
        any_word_in_name = Q()
        any_word_in_desc = Q()
        combined_search_query = Q()
        for word in search_words:
            word_in_name = Q(name__icontains=word)
            word_in_desc = Q(codelist__description__icontains=word)
            all_words_in_name &= word_in_name
            any_word_in_name |= word_in_name
            any_word_in_desc |= word_in_desc
            combined_search_query &= word_in_name | word_in_desc

        handles = handles.annotate(
            rank=Case(
                When(whole_phrase_in_name, then=Value(1)),
                When(all_words_in_name, then=Value(2)),
                When(any_word_in_name, then=Value(3)),
                When(any_word_in_desc, then=Value(4)),
                default=Value(5),
                output_field=IntegerField(),
            )
        ).filter(combined_search_query)

    if organisation_slug:
        organisation = get_object_or_404(Organisation, slug=organisation_slug)
        handles = handles.filter(organisation=organisation)
    else:
        organisation = None
        # For now, we only want to show codelists that come from organisations.
        handles = handles.filter(organisation_id__isnull=False)

    if q:
        handles = handles.order_by("rank", "name")
    else:
        handles = handles.order_by("name")

    page_number = request.GET.get("page")
    if status == Status.PUBLISHED:
        codelists = _all_published_codelists(handles)
        ctx = {
            "codelists_page": _get_page_obj(codelists, page_number, 15),
            "organisation": organisation,
            "q": q,
        }
        return render(request, "codelists/index.html", ctx)
    else:
        assert status == Status.UNDER_REVIEW
        versions = _all_under_review_codelist_versions(handles)
        ctx = {
            "versions_page": _get_page_obj(versions, page_number),
            "organisation": organisation,
            "q": q,
            "page_obj": _get_page_obj(versions, page_number),
        }
        return render(request, "codelists/under_review_index.html", ctx)


def _get_page_obj(objects, page_number, paginate_by=30):
    paginator = Paginator(objects, paginate_by)
    page_obj = paginator.get_page(page_number)
    return page_obj


def _all_published_codelists(handles):
    return [
        handle.codelist
        for handle in handles
        if handle.codelist.has_published_versions()
    ]


def _all_under_review_codelist_versions(handles):
    return flatten(
        [
            list(handle.codelist.versions.filter(status=Status.UNDER_REVIEW))
            for handle in handles
        ]
    )
