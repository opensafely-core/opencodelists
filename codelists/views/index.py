import re

from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import render

from ..models import Handle, Status


def _parse_search_query(query):
    """Parse search query to extract quoted phrases and individual words."""
    # Find all quoted phrases
    quoted_phrases = re.findall(r'"([^"]*)"', query)

    # Remove quoted phrases from query to get remaining words
    remaining_query = re.sub(r'"[^"]*"', "", query)
    individual_words = remaining_query.split()

    return quoted_phrases, individual_words


def index(request):
    # For now, we only want to show codelists that come from organisations.
    handles = _current_public_handles().filter(organisation_id__isnull=False)
    handles, q = _search_handles(handles, request.GET.get("q"))
    codelists = _all_published_codelists(handles)
    ctx = {
        "codelists_page": _get_page_obj(codelists, request.GET.get("page"), 15),
        "q": q,
    }
    return render(request, "codelists/index.html", ctx)


def _current_public_handles():
    return Handle.objects.filter(is_current=True, codelist__is_private=False)


def _search_handles(handles, q):
    if q:
        # Parse the search query to handle quoted phrases
        quoted_phrases, individual_words = _parse_search_query(q.strip())
        all_search_terms = quoted_phrases + individual_words

        if not all_search_terms:
            # If no valid search terms, skip search and just order by name
            handles = handles.order_by("name")
        else:
            # We search for codelists whose name/description contain all the words
            # in the query string. Quoted phrases are treated as single terms. We then
            # rank the results as follows:
            # 1. Exact phrase match in name (rank 1)
            # 2. All words in name (rank 2)
            # 3. Any word in name (rank 3)
            # 4. Any word in description (rank 4)

            whole_phrase_in_name = Q(name__icontains=q.strip().strip('"'))
            all_terms_in_name = Q()
            any_term_in_name = Q()
            any_term_in_desc = Q()
            combined_search_query = Q()
            for term in all_search_terms:
                term_in_name = Q(name__icontains=term)
                term_in_desc = Q(codelist__description__icontains=term)
                all_terms_in_name &= term_in_name
                any_term_in_name |= term_in_name
                any_term_in_desc |= term_in_desc
                combined_search_query &= term_in_name | term_in_desc

            handles = (
                handles.annotate(
                    rank=Case(
                        When(whole_phrase_in_name, then=Value(1)),
                        When(all_terms_in_name, then=Value(2)),
                        When(any_term_in_name, then=Value(3)),
                        When(any_term_in_desc, then=Value(4)),
                        default=Value(5),
                        output_field=IntegerField(),
                    )
                )
                .filter(combined_search_query)
                .order_by("rank", "name")
            )
    else:
        handles = handles.order_by("name")

    return handles, q


def _get_page_obj(objects, page_number, paginate_by=30):
    paginator = Paginator(objects, paginate_by)
    page_obj = paginator.get_page(page_number)
    return page_obj


def _all_published_codelists(handles):
    handles = (
        handles.filter(codelist__versions__status=Status.PUBLISHED)
        .select_related("codelist")
        .distinct()
    )

    return [handle.codelist for handle in handles]
