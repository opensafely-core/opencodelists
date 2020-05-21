from .models import Mapping


def read_code_to_snomedct_concepts(read_codes):
    # We don't use a defaultdict, because we want to know which codes haven't
    # been mapped.
    mapper = {read_code: [] for read_code in read_codes}
    for mapping in Mapping.objects.filter(ctv3_concept__in=read_codes).select_related(
        "sct_concept"
    ):
        mapper[mapping.ctv3_concept_id].append(mapping.sct_concept)
    return mapper
