import collections

from django.db.models import F, Q
from django.db.models.functions import Coalesce

from ..base.coding_system_base import BuilderCompatibleCodingSystem
from .models import AMP, AMPP, VMP, VMPP, VTM, Ing


class CodingSystem(BuilderCompatibleCodingSystem):
    id = "dmd"
    name = "Dictionary of Medicines and Devices"
    short_name = "dm+d"
    csv_headers = {
        "code": ["dmd_id", "code", "id", "snomed_id", "dmd"],
        "term": ["term", "dmd_name", "name", "nm", "description"],
    }
    is_experimental = False
    description = "Primary and Secondary Care prescribing"

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
        #
        # If the model type is AMP, we should prefer the `descr` field over the `nm` for the name
        # as this contains the supplier name which helps distinguish AMPs apart.
        # It appears to be populated in 100% of cases but coalese with `nm` just in case it is not.
        codes = set(codes)
        lookup = {}
        for model_cls in [AMP, VMP, AMPP, VMPP, VTM]:
            model_objs = model_cls.objects.using(self.database_alias).filter(
                id__in=codes
            )
            name_field = Coalesce("descr", "nm") if model_cls == AMP else F("nm")
            model_objs = model_objs.annotate(name=name_field)
            matched = dict(model_objs.values_list("id", "name"))
            for code, name in matched.items():
                lookup[code] = f"{name} ({model_cls.__name__})"
            codes = codes - set(matched.keys())
            if not codes:
                break
        return lookup

    def lookup_synonyms(self, codes):
        descriptions = (
            AMP.objects.using(self.database_alias)
            .filter(id__in=codes)
            .values("id", "nm")
        )

        result = collections.defaultdict(list)
        for d in descriptions:
            result[d["id"]].append(d["nm"])
        return dict(result)

    def lookup_references(self, codes):
        # OpenPrescribing's dm+d browser supports VTMs, VMPs, AMPs, VMPPs, and AMPPs
        # We need to know the type of the code to correctly form the URL for this.
        codes = set(codes)
        codes_and_types = []
        for model_cls in [AMP, VMP, AMPP, VMPP, VTM]:
            matched = (
                model_cls.objects.using(self.database_alias)
                .filter(id__in=codes)
                .values_list("id")
            )
            codes_and_types += [
                (code[0], model_cls.__name__.lower()) for code in matched
            ]

        return {
            code: [
                (
                    "OpenPrescribing dm+d browser",
                    f"https://openprescribing.net/dmd/{codetype}/{code}/",
                )
            ]
            for code, codetype in codes_and_types
        }

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
        type_to_codes = {"Product": known_codes}
        unknown_codes = list(set(codes) - set(known_codes))
        if unknown_codes:
            type_to_codes |= {"[unknown]": unknown_codes}

        return type_to_codes

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
