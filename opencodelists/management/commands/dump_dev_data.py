from inspect import getmembers, isclass

from django.core import serializers
from django.core.management import BaseCommand
from django.db.models.base import Model

import codelists.models as codelists_models
import opencodelists.models as opencodelists_models
from codelists.coding_systems import CODING_SYSTEMS
from codelists.models import (
    CachedHierarchy,
    CodelistVersion,
    CodeObj,
    Collaboration,
    Handle,
    Reference,
    Search,
    SearchResult,
    SignOff,
)
from coding_systems.versioning.models import CodingSystemRelease
from opencodelists.models import Membership


class Command(BaseCommand):
    def add_arguments(self, parser):
        coding_systems = ",".join(CODING_SYSTEMS.keys())
        parser.add_argument(
            "codelists_per_release",
            help="How many codelists to add from each release of a coding system",
            default=10,
        )
        parser.add_argument(
            "max_codelists_per_system",
            help="Maximum number of codelists to be added from each system (give or take)",
            default=100,
        )
        parser.add_argument(
            "coding systems",
            help="Comma-separated list of coding systems to include in dump, defaults to all",
            default=coding_systems,
        )

    def handle(
        self,
        codelists_per_release,
        max_codelists_per_system,
        coding_systems,
        **kwargs,
    ):
        # what models do we want to export?
        def model_classes(module):
            return [
                c[0]
                for c in getmembers(module, isclass)
                if Model in c[1].__mro__ and module.__name__ in c[1].__module__
            ]

        class_names_to_dump = model_classes(opencodelists_models) + model_classes(
            codelists_models
        )

        to_dump = {}

        # get all the versions of up to 100 (ish) codelists from each coding system
        codelist_versions_to_dump = []
        to_dump["CodingSystemRelease"] = set()
        for cs in coding_systems.split(","):
            cs_releases = CodingSystemRelease.objects.filter(coding_system=cs).order_by(
                "-valid_from"
            )
            cs_codelists_to_dump = set()
            for csr in cs_releases:
                to_dump["CodingSystemRelease"].add(csr)
                csr_codelist_versions = CodelistVersion.objects.filter(
                    coding_system_release=csr
                )
                n = min(codelists_per_release, csr_codelist_versions.count())
                csr_codelist_versions = csr_codelist_versions[n:]
                codelist_versions_to_dump.extend(csr_codelist_versions)
                cs_codelists_to_dump |= {cv.codelist for cv in csr_codelist_versions}
                if len(cs_codelists_to_dump) >= max_codelists_per_system:
                    break

        # make sure we've got all the versions of the codelists for which we previously got versions
        to_dump["Codelist"] = {cv.codelist for cv in codelist_versions_to_dump}
        to_dump["CodelistVersion"] = CodelistVersion.objects.filter(
            codelist__in=to_dump["Codelist"]
        )

        # get supporting objects for our codelistversions
        to_dump["CachedHierarchy"] = CachedHierarchy.objects.filter(
            version__in=to_dump["CodelistVersion"]
        )
        to_dump["Codeobj"] = CodeObj.objects.filter(
            version__in=to_dump["CodelistVersion"]
        )
        to_dump["Search"] = Search.objects.filter(
            version__in=to_dump["CodelistVersion"]
        )
        to_dump["SearchResult"] = SearchResult.objects.filter(
            search__in=to_dump["Search"]
        )
        to_dump["Reference"] = Reference.objects.filter(
            codelist__in=to_dump["Codelist"]
        )

        # add in extra releases needed for "compatible releases"
        for cv in to_dump["CodelistVersion"]:
            to_dump["CodingSystemRelease"] |= set(
                cv.compatible_releases.all().distinct()
            )

        # get users directly and indirectly related (incl. relation objects)
        to_dump["User"] = {cv.author for cv in codelist_versions_to_dump}

        to_dump["Collaboration"] = Collaboration.objects.filter(
            codelist__in=to_dump["Codelist"]
        )
        to_dump["User"] |= {c.collaborator for c in to_dump["Collaboration"]}

        to_dump["SignOff"] = SignOff.objects.filter(codelist__in=to_dump["Codelist"])
        to_dump["User"] |= {s.user for s in to_dump["SignOff"]}

        to_dump["Handle"] = Handle.objects.filter(codelist__in=to_dump["Codelist"])
        to_dump["User"] |= {h.user for h in to_dump["Handle"]}

        # pseudonymise users before dumping
        for i, u in enumerate(to_dump["User"]):
            u.name = f"DummyUser{i}"
            u.email = f"dummy{i}@example.com"

        # get memberships and organisations for our selected users

        to_dump["Membership"] = Membership.objects.filter(user__in=to_dump["User"])
        to_dump["Organisation"] = {h.organisation for h in to_dump["Handle"]} | {
            m.organisation for m in to_dump["Membership"]
        }

        assert set(to_dump.keys()) == set(class_names_to_dump)
        # to_dump = [
        #     *codelists_to_dump,
        #     *codelist_versions_to_dump,
        #     *hierarchies_to_dump,
        #     *code_objs_to_dump,
        #     *searches_to_dump,
        #     *search_results_to_dump,
        #     *references_to_dump,
        #     *releases_to_dump,
        #     *collaborations_to_dump,
        #     *signoffs_to_dump,
        #     *handles_to_dump,
        #     *to_dump["User"],
        #     *memberships,
        #     *organisations_to_dump,
        # ]
        with open("file.json", "w") as out:
            serializers.serialize("json", *to_dump.values(), stream=out)

        print("Required coding system release database files:\n")
        for r in to_dump["CodingSystemRelease"]:
            print(r.database_alias + "\n")
