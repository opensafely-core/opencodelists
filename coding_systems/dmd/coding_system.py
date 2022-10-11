from .models import AMP, AMPP, VMP, VMPP, VTM

name = "Dictionary of Medicines and Devices"
short_name = "dm+d"


def lookup_codes(codes):
    # A code is a unique identifier in dm+d which corresponds to a SNOMED-CT code
    # It could be the identifier for any of AMP, VMP, VTM, VMPP, AMPP
    # dm+d codelists generally only include AMPs and VMPs, so we attempt to match codes in
    # these models first
    # If not found, look up VTM, VMPP, AMPPs also, in case of user-uploaded codelists that
    # might contain these
    for code in codes:
        for model_cls in [AMP, VMP, AMPP, VMPP, VTM]:
            try:
                yield code, model_cls.objects.get(id=code).nm
                continue
            except model_cls.DoesNotExist:
                ...


def code_to_term(codes):
    lookup = {code: term for code, term in lookup_codes(codes)}
    unknown = set(codes) - set(lookup)
    return {**lookup, **{code: "Unknown" for code in unknown}}
