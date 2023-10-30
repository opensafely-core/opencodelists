from mappings.dmdvmpprevmap.models import Mapping


def vmp_ids_to_previous():
    """
    Return any codes with previous IDs
    This applies to VMP IDs only
    """
    # Simple dict of vmp id: previous id from the mappings across historical dm+d releases
    # Filter out any where the current and previous are identical
    mapping_objs = Mapping.objects.values_list("id", "vpidprev")
    vmp_to_previous = {
        vpid: vpidprev for (vpid, vpidprev) in mapping_objs if vpid != vpidprev
    }
    # Build list of (id, prev_id) tuples in case of codes with multiple previous ones that
    # we can trace back in the current coding system
    vmps_with_all_previous = []
    for vmp, previous in vmp_to_previous.items():
        all_previous = _get_all_previous_vmpids(vmp_to_previous, vmp, previous)
        for previous in all_previous:
            vmps_with_all_previous.append((vmp, previous))

    return vmps_with_all_previous


def vmpprev_full_mappings(codes):
    """
    For a set of codes, return a full set of previous and subsequent codes
    Returns a simple dict of id: prev pairs, where one of id or prev are in the provided
    codes, and also a set of (id, prev) tuples, where prev may be one or more steps away
    from id in the historical mappings
    """
    vmps_with_all_previous = vmp_ids_to_previous()
    # limit both the list of (id, prev) pairs and mapping to only those where one of the
    # pair is in the provided codes
    codes = set(codes)
    vmps_with_all_previous_for_codes = []

    for vmp_prev in vmps_with_all_previous:
        if not (set(vmp_prev) & codes):
            continue
        vmps_with_all_previous_for_codes.append(vmp_prev)
    return vmps_with_all_previous_for_codes


def _get_all_previous_vmpids(mapping, vmp, previous, all_previous=None):
    all_previous = all_previous or set()
    all_previous.add(previous)
    if previous not in mapping:
        return all_previous
    return _get_all_previous_vmpids(mapping, vmp, mapping[previous], all_previous)
