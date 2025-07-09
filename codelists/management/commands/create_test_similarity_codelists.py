"""
Django management command to create 50 test codelists with varying similarities.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction

from codelists.actions import create_codelist_with_codes
from codelists.coding_systems import most_recent_database_alias
from codelists.models import Status
from opencodelists.models import User


class Command(BaseCommand):
    help = "Create 50 test codelists with varying similarities for matrix testing"

    # All available SNOMED CT codes from fixtures - using only real codes
    ALL_CODES = [
        "429554009",  # Arthropathy of elbow
        "128133004",  # Disorder of elbow
        "202855006",  # Lateral epicondylitis
        "439656005",  # Arthritis of elbow
        "73583000",  # Epicondylitis
        "35185008",  # Enthesopathy of elbow region
        "239964003",  # Soft tissue lesion of elbow region
        "156659008",  # (Epicondylitis &/or tennis elbow) or (golfers' elbow)
        "3723001",  # Arthritis
        "116309007",  # Finding of elbow region
        "298869002",  # Finding of elbow joint
        "298163003",  # Elbow joint inflamed
        "238484001",  # Tennis toe
    ]

    # Core elbow codes (higher similarity base)
    CORE_ELBOW_CODES = [
        "429554009",  # Arthropathy of elbow
        "128133004",  # Disorder of elbow
        "202855006",  # Lateral epicondylitis
        "439656005",  # Arthritis of elbow
        "73583000",  # Epicondylitis
        "35185008",  # Enthesopathy of elbow region
        "239964003",  # Soft tissue lesion of elbow region
    ]

    # Extended codes (for lower similarity)
    EXTENDED_CODES = [
        "156659008",  # (Epicondylitis &/or tennis elbow) or (golfers' elbow)
        "3723001",  # Arthritis
        "116309007",  # Finding of elbow region
        "298869002",  # Finding of elbow joint
        "298163003",  # Elbow joint inflamed
        "238484001",  # Tennis toe
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--owner-username",
            type=str,
            default="localdev",
            help="Username of the codelist owner (default: localdev)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating",
        )
        parser.add_argument(
            "--prefix",
            type=str,
            default="TestSim",
            help="Prefix for codelist names (default: TestSim)",
        )

    def handle(self, *args, **options):
        username = options["owner_username"]
        dry_run = options["dry_run"]
        prefix = options["prefix"]

        try:
            owner = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{username}' not found"))
            return

        if dry_run:
            self.stdout.write("DRY RUN - No codelists will be created")

        self.stdout.write(f"Creating 50 test codelists with owner: {username}")

        # Get database alias
        db_alias = most_recent_database_alias("snomedct")

        # Generate code combinations with varying similarity
        code_combinations = self._generate_code_combinations()

        if not dry_run:
            with transaction.atomic():
                for i, (codes, description) in enumerate(code_combinations, 1):
                    name = f"{prefix} {i:02d}"

                    try:
                        create_codelist_with_codes(
                            owner=owner,
                            name=name,
                            coding_system_id="snomedct",
                            coding_system_database_alias=db_alias,
                            codes=codes,
                            description=description,
                            methodology=f"Generated test codelist {i} with {len(codes)} codes for similarity testing",
                            status=Status.PUBLISHED,
                        )

                        self.stdout.write(
                            f"Created: {name} ({len(codes)} codes) - {description}"
                        )

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Failed to create {name}: {e}")
                        )
        else:
            # Dry run - just show what would be created
            for i, (codes, description) in enumerate(code_combinations, 1):
                name = f"{prefix} {i:02d}"
                self.stdout.write(
                    f"Would create: {name} ({len(codes)} codes) - {description}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Would create' if dry_run else 'Created'} {len(code_combinations)} test codelists"
            )
        )

    def _generate_code_combinations(self):
        """Generate 50 different code combinations with varying similarities."""
        combinations_list = []

        # Set random seed for reproducible results
        random.seed(42)

        # 1. High similarity (80-100%) - mostly core elbow codes
        for i in range(15):
            if i == 0:
                # Full set for 100% similarity reference
                codes = self.ALL_CODES.copy()
            else:
                # Variations of core codes
                core_count = random.randint(5, 7)  # Most core codes
                core_subset = random.sample(self.CORE_ELBOW_CODES, core_count)
                extended_count = random.randint(0, 3)  # Few extended codes
                extended_subset = random.sample(self.EXTENDED_CODES, extended_count)
                codes = core_subset + extended_subset

            combinations_list.append(
                (codes, f"High similarity variant {i + 1} - primarily elbow conditions")
            )

        # 2. Medium-high similarity (60-80%) - mix core with extended
        for i in range(12):
            core_count = random.randint(3, 5)  # Some core codes
            core_subset = random.sample(self.CORE_ELBOW_CODES, core_count)
            extended_count = random.randint(2, 4)  # More extended codes
            extended_subset = random.sample(self.EXTENDED_CODES, extended_count)
            codes = core_subset + extended_subset

            combinations_list.append(
                (
                    codes,
                    f"Medium-high similarity {i + 1} - mixed elbow and joint conditions",
                )
            )

        # 3. Medium similarity (40-60%) - balanced mix
        for i in range(12):
            core_count = random.randint(2, 4)  # Fewer core codes
            core_subset = random.sample(self.CORE_ELBOW_CODES, core_count)
            extended_count = random.randint(3, 5)  # More extended codes
            extended_subset = random.sample(self.EXTENDED_CODES, extended_count)
            codes = core_subset + extended_subset

            combinations_list.append(
                (codes, f"Medium similarity {i + 1} - balanced joint conditions")
            )

        # 4. Low similarity (20-40%) - mostly extended codes
        for i in range(11):
            core_count = random.randint(0, 2)  # Very few core codes
            core_subset = (
                random.sample(self.CORE_ELBOW_CODES, core_count)
                if core_count > 0
                else []
            )
            extended_count = random.randint(4, 6)  # Mostly extended codes
            extended_subset = random.sample(self.EXTENDED_CODES, extended_count)
            codes = core_subset + extended_subset

            combinations_list.append(
                (codes, f"Low similarity {i + 1} - mostly non-elbow conditions")
            )

        # Shuffle the combinations to mix similarity levels
        random.shuffle(combinations_list)

        return combinations_list
