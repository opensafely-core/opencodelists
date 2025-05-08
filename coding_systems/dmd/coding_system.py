from django.db.models import Q

from ..base.coding_system_base import BaseCodingSystem
from .models import AMP, AMPP, VMP, VMPP, VTM, Ing


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
        vmps = VMP.objects.using(self.database_alias).filter(
            id__in=set(codes) | {amp.vmp_id for amp in amps}
        )

        return {(amp.vmp_id, amp.id) for amp in amps} | {
            (vmp.vtm_id, vmp.id) for vmp in vmps if vmp.vtm_id
        }

    def descendant_relationships(self, codes):
        vmps_from_vtms = VMP.objects.using(self.database_alias).filter(vtm__in=codes)
        amps_from_vmps = AMP.objects.using(self.database_alias).filter(vmp_id__in=codes)

        rv = (
            {(vmp.vtm_id, vmp.id) for vmp in vmps_from_vtms}
            | {(vmp.vtm_id, vmp.id) for vmp in vmps_from_vtms if vmp.vtm_id}
            | {(amp.vmp_id, amp.id) for amp in amps_from_vmps}
        )
        return rv

    def search_by_term(self, term):
        """
        Invalid codes are not excluded.
        We don't know whether invalid codes will appear in a patient's record,
        and if they do what the significance of that is.

        VTMs have a many-to-many relationship with Ings that we can't resolve
        to a simple hierarchy (e.g. two different salts of the same base ingredient
        will be considered the same VTM; a single ingredient may appear in multiple
        combinations as different VTMs). Additionally, there is no direct mapping
        from Ing to VTM so we must derive this via VMPs.
        """
        ings = (
            Ing.objects.using(self.database_alias)
            .filter(nm__contains=term)
            .values_list("id", flat=True)
        )
        vmps_from_ings = set(
            VMP.objects.using(self.database_alias)
            .filter(vpi__ing_id__in=ings)
            .values_list("id", flat=True)
        )
        vtms = set(
            VTM.objects.using(self.database_alias)
            .filter(Q(nm__contains=term) | Q(vmp__id__in=vmps_from_ings))
            .values_list("id", flat=True)
        )
        vmps = set(
            VMP.objects.using(self.database_alias)
            .filter(nm__contains=term)
            .values_list("id", flat=True)
        )
        vmps_from_vtms = set(
            VMP.objects.using(self.database_alias)
            .filter(vtm__id__in=vtms)
            .values_list("id", flat=True)
        )
        amps = set(
            AMP.objects.using(self.database_alias)
            .filter(Q(nm__contains=term) | Q(descr__contains=term))
            .values_list("id", flat=True)
        )

        return vtms | vmps | vmps_from_vtms | vmps_from_ings | amps

    def search_by_code(self, code):
        """
        Invalid codes are not excluded.
        We don't know whether invalid codes will appear in a patient's record,
        and if they do what the significance of that is.

        VTMs have a many-to-many relationship with Ings that we can't resolve
        to a simple hierarchy (e.g. two different salts of the same base ingredient
        will be considered the same VTM; a single ingredient may appear in multiple
        combinations as different VTMs). Additionally, there is no direct mapping
        from Ing to VTM so we must derive this via VMPs.
        """
        ings = (
            Ing.objects.using(self.database_alias)
            .filter(id=code)
            .values_list("id", flat=True)
        )
        vmps = set(
            VMP.objects.using(self.database_alias)
            .filter(Q(id=code) | Q(vpi__ing_id__in=ings))
            .values_list("id", flat=True)
        )
        vtms = set(
            VTM.objects.using(self.database_alias)
            .filter(Q(id=code) | Q(vmp__id__in=vmps))
            .values_list("id", flat=True)
        )
        return (
            vtms
            | vmps
            | set(
                AMP.objects.using(self.database_alias)
                .filter(id=code)
                .values_list("id", flat=True)
            )
        )

    def codes_by_type(self, codes, hierarchy):
        """
        The entities we search across are all different "types"
        but they share a common ancestor of a medicinal product.
        Since we build them all into a singular hierarchy,
        displaying them in separate "type" sections doesn't make
        sense.
        """
        codes = (
            list(
                Ing.objects.using(self.database_alias)
                .filter(id__in=codes)
                .values_list("id", flat=True)
            )
            + list(
                VTM.objects.using(self.database_alias)
                .filter(id__in=codes)
                .values_list("id", flat=True)
            )
            + list(
                VMP.objects.using(self.database_alias)
                .filter(id__in=codes)
                .values_list("id", flat=True)
            )
            + list(
                AMP.objects.using(self.database_alias)
                .filter(id__in=codes)
                .values_list("id", flat=True)
            )
        )

        return {"Product": codes}

    def matching_codes(self, codes):
        return (
            set(
                Ing.objects.using(self.database_alias)
                .filter(id__in=codes)
                .values_list("id", flat=True)
            )
            | set(
                VTM.objects.using(self.database_alias)
                .filter(id__in=codes)
                .values_list("id", flat=True)
            )
            | set(
                VMP.objects.using(self.database_alias)
                .filter(id__in=codes)
                .values_list("id", flat=True)
            )
            | set(
                AMP.objects.using(self.database_alias)
                .filter(id__in=codes)
                .values_list("id", flat=True)
            )
        )

    def lookup_names(self, codes):
        # A code is a unique identifier in dm+d which corresponds to a SNOMED-CT code
        # It could be the identifier for any of AMP, VMP, VTM, VMPP, AMPP
        # dm+d codelists generally only include AMPs and VMPs, so we attempt to match codes in
        # these models first
        # If not found, look up VTM, VMPP, AMPPs also, in case of user-uploaded codelists that
        # might contain these
        codes = set(codes)
        lookup = {}
        for model_cls in [AMP, VMP, AMPP, VMPP, VTM, Ing]:
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
