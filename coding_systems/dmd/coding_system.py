from ..base.coding_system_base import BaseCodingSystem
from .models import AMP, AMPP, VMP, VMPP, VTM


class CodingSystem(BaseCodingSystem):
    id = "dmd"
    name = "Dictionary of Medicines and Devices"
    short_name = "dm+d"
    csv_headers = {
        "code": ["dmd_id", "code", "id", "snomed_id", "dmd"],
        "term": ["term", "dmd_name", "name", "nm", "description"],
    }

    def ancestor_relationships(self, codes):
        amps = AMP.objects.using(self.database_alias).filter(id__in=codes)

        # get VMPs that are either in `codes` or are ancestors
        # of the AMPs in `codes`
        codes = set(codes) | {amp.vmp_id for amp in amps}
        vmps = VMP.objects.using(self.database_alias).filter(id__in=codes)

        # exclude null VTM-VMP relationships (i.e. VMPs with no VTM)
        return {(amp.vmp_id, amp.id) for amp in amps} | {
            (vmp.vtm_id, vmp.id) for vmp in vmps if vmp.vtm_id
        }

    def descendant_relationships(self, codes):
        vmps_from_vtms = VMP.objects.using(self.database_alias).filter(vtm__in=codes)

        # get AMPs that have ancestor VMPs that are either in `codes`
        # or are descendants of VTMs that are in `codes`
        codes = set(codes) | {vmp.id for vmp in vmps_from_vtms}
        amps_from_vmps = AMP.objects.using(self.database_alias).filter(vmp_id__in=codes)

        return {(vmp.vtm_id, vmp.id) for vmp in vmps_from_vtms} | {
            (amp.vmp_id, amp.id) for amp in amps_from_vmps
        }

    def lookup_names(self, codes):
        # A code is a unique identifier in dm+d which corresponds to a SNOMED-CT code
        # It could be the identifier for any of AMP, VMP, VTM, VMPP, AMPP
        # dm+d codelists generally only include AMPs and VMPs, so we attempt to match codes in
        # these models first
        # If not found, look up VTM, VMPP, AMPPs also, in case of user-uploaded codelists that
        # might contain these
        codes = set(codes)
        lookup = {}
        for model_cls in [AMP, VMP, AMPP, VMPP, VTM]:
            matched = dict(
                model_cls.objects.using(self.database_alias)
                .filter(id__in=codes)
                .values_list("id", "nm")
            )
            for code, name in matched.items():
                lookup[code] = f"{name} ({model_cls.__name__})"
            codes = codes - set(matched.keys())
            if not codes:
                break
        return lookup

    def code_to_term(self, codes):
        lookup = self.lookup_names(codes)
        unknown = set(codes) - set(lookup)
        return {**lookup, **{code: "Unknown" for code in unknown}}
