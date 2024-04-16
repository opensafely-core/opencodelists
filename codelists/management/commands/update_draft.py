from collections import defaultdict

import structlog
from django.core.management import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from ...actions import add_new_descendants, cache_hierarchy
from ...models import CodelistVersion, CodeObj, SearchResult
from ...search import do_search


logger = structlog.get_logger()


class Command(BaseCommand):
    """
    Update a draft's codeset; required if a coding system has changed since the draft was created.

    It reruns the draft's searches, then checks for new matching concepts and ensures the codeset
    is up to date so the builder frontend can display it

    The recreated search will have added any new concepts that are returned by a search.
    The builder frontend can't deal with new concepts (with unresolved status) if they have
    a parent that is included/excluded.

    Update all code statuses with the known statuses that are explicitly included
    or excluded.  This will assign statuses to unresolved codes that have included/excluded
    parents.  It will also update any previously implicitly included/excluded status that
    are no longer applicable.

    e.g. On the initial draft, B inherited from A;
     - A was explicitly included, so B was implicitly included
    After a coding system update, now A and B have swapped, so A inherits from B
     - A is still explicitly included
     - B is now unresolved as it has no parents that are explicitly included or
       excluded (the fronted can deal with that)
    """

    def add_arguments(self, parser):
        parser.add_argument("version_hash")

    @transaction.atomic
    def handle(self, version_hash, **kwargs):
        draft = next(
            (
                version
                for version in CodelistVersion.objects.all()
                if version.hash == version_hash
            ),
            None,
        )
        if draft is None:
            self.stderr.write(f"No CodelistVersion found with hash '{version_hash}'")
        elif not draft.is_draft:
            self.stderr.write(
                f"CodelistVersion '{version_hash}' is not a draft ({draft.status})"
            )
        else:
            original_codeset = draft.codeset
            logger.info("Updating draft", hash=version_hash)
            logger.info(
                "Original codeset", code_to_status=original_codeset.code_to_status
            )
            logger.info("Updating searches")
            self.update_searches(draft)
            logger.info("Deleting removed codes")
            self.delete_removed_codes(draft)
            logger.info("Checking for new descendants")
            add_new_descendants(version=draft)
            logger.info("Updating statatus")
            self.update_code_statuses(draft)
            logger.info("Geting diff")
            updates = self.diff(draft.codeset, original_codeset)
            cache_hierarchy(version=draft)

            if any(updates.values()):
                self.stdout.write(f"CodelistVersion {version_hash} updated:")
                if updates["added"]:
                    for code, status in updates["added"]:
                        self.stdout.write(f"{code} - {status} (new)")
                if updates["changed"]:
                    for code, old_status, new_status in updates["changed"]:
                        self.stdout.write(
                            f"{code} - {new_status} (changed from {old_status})"
                        )
                if updates["removed"]:
                    for code in updates["removed"]:
                        self.stdout.write(f"{code} (removed)")
            else:
                self.stdout.write(
                    f"CodelistVersion {version_hash}: no changes required"
                )

    def update_searches(self, draft):
        for search in draft.searches.all():
            codes = do_search(draft.coding_system, term=search.term, code=search.code)[
                "all_codes"
            ]
            self.update_search(
                draft=draft, term=search.term, code=search.code, codes=codes
            )

    def update_search(self, *, draft, term=None, code=None, codes):
        """
        Note: this is more or less a copy of builder.actions.create_search, modifed to
        update searches on an existing draft
        """
        assert bool(term) != bool(code)
        if term is not None:
            slug = slugify(term)
        else:
            slug = f"code:{code}"

        search = draft.searches.get(term=term, code=code, slug=slug)
        # Ensure that there is a CodeObj object linked to this draft for each code.
        codes_with_existing_code_objs = set(
            draft.code_objs.filter(code__in=codes).values_list("code", flat=True)
        )
        codes_without_existing_code_objs = set(codes) - codes_with_existing_code_objs
        CodeObj.objects.bulk_create(
            CodeObj(version=draft, code=code)
            for code in codes_without_existing_code_objs
        )

        # Create a SearchResult for each new code which doesn't already have one.
        code_obj_ids = draft.code_objs.filter(code__in=codes).values_list(
            "id", flat=True
        )
        existing_results = SearchResult.objects.filter(
            search=search, code_obj_id__in=code_obj_ids
        ).values_list("code_obj_id", flat=True)
        # find the set of code_obj_ids that don't already exist in the search results
        to_create = set(code_obj_ids) - set(existing_results)
        # find code_objs that no longer match a search
        to_delete = set(existing_results) - set(code_obj_ids)

        SearchResult.objects.bulk_create(
            SearchResult(search=search, code_obj_id=id) for id in to_create
        )
        SearchResult.objects.filter(search=search, code_obj_id__in=to_delete).delete()

        logger.info("Updated Search", search_pk=search.pk)

    def delete_removed_codes(self, draft):
        """
        Identify any code objs on the draft that are no longer in the coding system,
        and delete them
        """
        codes_in_coding_system = draft.coding_system.matching_codes(
            draft.codeset.all_codes()
        )
        old_codes = draft.codeset.all_codes() - codes_in_coding_system
        if old_codes:
            CodeObj.objects.filter(version=draft, code__in=old_codes).delete()
            logger.info(
                "Old codes no longer in coding system removed from draft",
                draft=draft,
                coding_system=draft.coding_system,
                removed_codes=old_codes,
            )

    def update_code_statuses(self, draft):
        """
        Update a draft's a codeset that may be out of date following a coding system update,
        by clearing all code statuses and reapplying any explicitly included/excluded codes

        Note: this is more or less a copy of builder.actions.update_code_statuses,
        except that it creates the new codeset by reapplying the draft's current directly
        included/excluded codes
        """
        new_codeset = draft.codeset.reapply_statuses()
        status_to_new_code = defaultdict(list)
        for code, status in new_codeset.code_to_status.items():
            status_to_new_code[status].append(code)

        for status, codes in status_to_new_code.items():
            draft.code_objs.filter(code__in=codes).update(status=status)

    def diff(self, updated_codeset, original_codeset):
        """
        Compare the updated codeset to the original codeset, and return a dict of codes that
        have been added, changed and removed in the updated one
        """
        original_codes = set(original_codeset.code_to_status)
        updated_codes = set(updated_codeset.code_to_status)

        removed_codes = original_codes - updated_codes
        new_codes = updated_codes - original_codes
        all_changed_and_new_codes = {
            code
            for code, _ in set(updated_codeset.code_to_status.items())
            - set(original_codeset.code_to_status.items())
        }
        changed_codes = all_changed_and_new_codes - new_codes

        new_code_statuses = {
            (code, status)
            for code, status in updated_codeset.code_to_status.items()
            if code in new_codes
        }
        changed_statuses = {
            (
                code,
                original_codeset.code_to_status[code],
                updated_codeset.code_to_status[code],
            )
            for code in changed_codes
        }

        return {
            "added": new_code_statuses,
            "changed": changed_statuses,
            "removed": removed_codes,
        }
