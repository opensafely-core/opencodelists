from django.db.models import Q

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
            id__in=(set(codes) | {amp.vmp_id for amp in amps})
        )

        return {(amp.vmp_id, amp.id) for amp in amps} | {
            (vpi.ing_id, vmp.id) for vmp in vmps for vpi in vmp.vpi_set.all()
        }

    def descendant_relationships(self, codes):
        vmps_from_ings = VMP.objects.using(self.database_alias).filter(
            vpi__ing_id__in=codes
        )
        amps_from_ings = AMP.objects.using(self.database_alias).filter(
            vmp_id__in=[vmp.id for vmp in vmps_from_ings]
        )
        amps_from_vmps = AMP.objects.using(self.database_alias).filter(vmp_id__in=codes)

        rv = (
            {
                (vpi.ing_id, vmp.id)
                for vmp in vmps_from_ings
                for vpi in vmp.vpi_set.all()
            }
            | {(amp.vmp_id, amp.id) for amp in amps_from_ings}
            | {(amp.vmp_id, amp.id) for amp in amps_from_vmps}
        )
        return rv

    def search_by_term(self, term):
        return (
            set(
                Ing.objects.using(self.database_alias)
                .filter(nm__contains=term)
                .values_list("id", flat=True)
            )
            | set(
                VMP.objects.using(self.database_alias)
                .filter(nm__contains=term)
                .values_list("id", flat=True)
            )
            | set(
                AMP.objects.using(self.database_alias)
                .filter(Q(nm__contains=term) | Q(descr__contains=term))
                .values_list("id", flat=True)
            )
        )

    def search_by_code(self, code):
        return (
            set(
                Ing.objects.using(self.database_alias)
                .filter(id=code)
                .values_list("id", flat=True)
            )
            | set(
                VMP.objects.using(self.database_alias)
                .filter(id=code)
                .values_list("id", flat=True)
            )
            | set(
                AMP.objects.using(self.database_alias)
                .filter(id=code)
                .values_list("id", flat=True)
            )
        )

    def codes_by_type(self, codes, hierarchy):
        d = {
            "Ingredient": Ing.objects.using(self.database_alias)
            .filter(id__in=codes)
            .values_list("id", flat=True),
            "VMP": VMP.objects.using(self.database_alias)
            .filter(id__in=codes)
            .values_list("id", flat=True),
            "AMP": AMP.objects.using(self.database_alias)
            .filter(id__in=codes)
            .values_list("id", flat=True),
        }
        return {k: v for k, v in d.items() if v}

    def matching_codes(self, codes):
        return (
            set(
                Ing.objects.using(self.database_alias)
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

    def codes_by_type(self, codes, hierarchy):
        """
        The entities we search across are all different "types"
        but they share a common ancestor of a medicinal product.
        Since we build them all into a singular hierarchy,
        displaying them in separate "type" sections doesn't make
        sense.
        """
        known_codes = (
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

        return {
            "Product": known_codes,
            "[unknown]": list(set(codes) - set(known_codes)),
        }

    def search_by_term(self, term):
        # We search for VTMs, VMPs and AMPs using the search term.
        # Each object has some or all of the following - we search each when available:
        # - Name (nm)
        # - Description (descr)
        # - Abbreviated name (abbrevnm) - this allows things like "Hep B", and "dTAP" to return matches
        # - Previous name (nmprev / nm_prev) - this allows searches for "frusemide" to match the newer name of "furosemide"
        # We also search for ingregients and map them to their VMP and VTMs
        # We don't return AMPPs or VMPPs mainly because they don't exist in primary care data, but also because
        # the AMPPs would all appear twice in the hierarchy, as VMP > VMPP > AMPP and VMP > AMP > AMPP

        # We get all the AMPs that match nm, abbrevnm, descr and nm_prev
        amps = set(
            AMP.objects.using(self.database_alias)
            .filter(
                Q(nm__icontains=term)
                | Q(abbrevnm__icontains=term)
                | Q(descr__icontains=term)
                | Q(nm_prev__icontains=term)
            )
            .values_list("id", flat=True)
        )

        # We get all the VMPs that match nm, abbrevnm, and nmprev
        vmps = set(
            VMP.objects.using(self.database_alias)
            .filter(
                Q(nm__icontains=term)
                | Q(abbrevnm__icontains=term)
                | Q(nmprev__icontains=term)
            )
            .values_list("id", flat=True)
        )

        # We also get all VMPs from a matched ingredient
        vmps_from_ing = set(
            VMP.objects.using(self.database_alias)
            .filter(vpi__ing__nm__icontains=term)
            .values_list("id", flat=True)
            .distinct()
        )

        # We get all the VTMs that match nm, abbrevnm OR that are parents of any
        # VMPs found by ingredient. This is because there is only a mapping of
        # ingredient to VTM via VMP
        vtms = set(
            VTM.objects.using(self.database_alias)
            .filter(
                Q(nm__icontains=term)
                | Q(abbrevnm__icontains=term)
                | Q(vmp__id__in=vmps_from_ing)
            )
            .values_list("id", flat=True)
        )

        return amps | vmps | vmps_from_ing | vtms

    def search_by_code(self, code):
        # If the code is an AMP, VMP or VTM we return just that
        for model_cls in [AMP, VMP, VTM]:
            if model_cls.objects.using(self.database_alias).filter(id=code).exists():
                return {code}

        # If the code is an ingredient, we return the VMPs and VTMs with that ingredient
        try:
            ing = Ing.objects.using(self.database_alias).get(id=code)
            vmps = set(
                VMP.objects.using(self.database_alias)
                .filter(vpi__ing_id=ing.id)
                .values_list("id", flat=True)
                .distinct()
            )
            vtms = set(
                VTM.objects.using(self.database_alias)
                .filter(vmp__id__in=vmps)
                .values_list("id", flat=True)
                .distinct()
            )
            return vmps | vtms
        except Ing.DoesNotExist:
            return set()
