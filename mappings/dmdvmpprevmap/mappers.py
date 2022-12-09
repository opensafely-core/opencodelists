from mappings.dmdvmpprevmap.models import Mapping


def vmp_ids_to_previous():
    """
    Return any codes with previous IDs
    This applies to VMP IDs only
    """
    # Simple dict of vmp id: previous id from the mappings across historical dm+d releases
    # Filter out any where the current and previous are identical
    vmp_to_previous = {
        vpid: vpidprev
        for (vpid, vpidprev) in Mapping.objects.values_list("id", "vpidprev")
        if vpid != vpidprev
    }
    # Build list of (id, prev_id) tuples in case of codes with multiple previous ones that
    # we can trace back in the current coding system
    vmps_with_all_previous = []
    for vmp, previous in vmp_to_previous.items():
        all_previous = _get_all_previous_vmpids(vmp_to_previous, vmp, previous)
        for previous in all_previous:
            vmps_with_all_previous.append((vmp, previous))
    return vmps_with_all_previous


def _get_all_previous_vmpids(mapping, vmp, previous, all_previous=None):
    all_previous = all_previous or set()
    all_previous.add(previous)
    if previous not in mapping:
        return all_previous
    return _get_all_previous_vmpids(mapping, vmp, mapping[previous], all_previous)
