"""Generic management command to import usage data for any coding system."""

import importlib
import inspect

import requests
import structlog
from django.core.management import BaseCommand, CommandError

from coding_systems.usage.importer import UsageImporter
from coding_systems.usage.models import CodeUsageRelease


logger = structlog.get_logger()


class Command(BaseCommand):
    """
    Import usage data for a specified coding system.

    Dynamically discovers and loads the UsageImporter implementation for the
    coding system, then scrapes and imports available periods.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--coding-system",
            default="snomedct",
            help="The coding system to import usage data for (default: snomedct)",
        )

    def handle(self, coding_system, **kwargs):
        run_logger = logger.bind(command="import_usage", coding_system=coding_system)
        imported_count = 0
        skipped_count = 0
        failed_count = 0

        run_logger.info("Usage import started")

        # Dynamically import the importer for this coding system
        try:
            importer_module = importlib.import_module(
                f"coding_systems.{coding_system}.usage"
            )
        except ModuleNotFoundError:
            raise CommandError(
                f"No usage importer found for coding system '{coding_system}'. "
                f"Expected module: coding_systems.{coding_system}.usage"
            )

        # Find the UsageImporter subclass in the module
        importer_class = None
        for attr_name in dir(importer_module):
            attr = getattr(importer_module, attr_name)
            if (
                inspect.isclass(attr)
                and issubclass(attr, UsageImporter)
                and attr is not UsageImporter
            ):
                importer_class = attr
                break

        if importer_class is None:
            raise CommandError(
                f"No UsageImporter subclass found in "
                f"coding_systems.{coding_system}.usage"
            )

        importer = importer_class()

        with requests.Session() as session:
            self.stdout.write(
                f"Checking for available {coding_system} usage periods..."
            )
            try:
                all_periods = importer.get_available_periods(session=session)
            except Exception as exc:
                raise CommandError(
                    f"Failed to discover available periods: {exc}"
                ) from exc

            if not all_periods:
                raise CommandError(
                    f"No {coding_system} usage periods were discovered. "
                    "This likely indicates the source page structure has changed."
                )

            imported = set(
                CodeUsageRelease.objects.filter(
                    coding_system=coding_system
                ).values_list("period", flat=True)
            )
            periods_to_check = [p for p in all_periods if p not in imported]

            run_logger.info(
                "Discovered usage periods",
                available_periods=len(all_periods),
                already_imported=len(imported),
                to_import=len(periods_to_check),
            )

            # Write table of available periods and whether they're already imported
            self.stdout.write("Available periods:")
            for p in all_periods:
                status = "imported" if p in imported else "not imported"
                self.stdout.write(f"  {p}: {status}")

            self.stdout.write(
                f"{len(periods_to_check)} period(s) to import "
                f"(of {len(all_periods)} available)."
            )

            if not periods_to_check:
                run_logger.info("No new periods to import")
                return

            for p in periods_to_check:
                period_logger = run_logger.bind(period=p)
                self.stdout.write(f"Period {p}: looking up download URL...")
                period_logger.info("Looking up download URL")

                try:
                    download_url = importer.find_txt_download_url(p, session=session)
                    imported_now = importer.import_period(
                        p, download_url, session=session
                    )
                except Exception as exc:
                    failed_count += 1
                    self.stderr.write(f"  ERROR importing {p}: {exc}")
                    period_logger.exception("Import failed")
                    continue

                if imported_now:
                    imported_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  Imported period {p}."))
                    period_logger.info("Imported period", download_url=download_url)
                else:
                    skipped_count += 1
                    self.stdout.write(f"  Period {p} already in database, skipped.")
                    period_logger.info("Skipped period (already imported)")

        run_logger.info(
            "Usage import completed",
            available_periods=len(all_periods),
            considered_periods=len(periods_to_check),
            imported_periods=imported_count,
            skipped_periods=skipped_count,
            failed_periods=failed_count,
        )

        self.stdout.write(
            f"Summary: imported={imported_count}, skipped={skipped_count}, failed={failed_count}."
        )

        if failed_count:
            raise CommandError(
                f"Usage import completed with {failed_count} failure(s)."
            )
