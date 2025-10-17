import pickle
import re
from pathlib import Path
from zipfile import ZipFile

from django.core.management import BaseCommand

from coding_systems.icd10.import_data import extract_document, load_concepts
from coding_systems.icd10.models import Concept


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "release_zipfiles", help="Path to local releases to combine", nargs=2
        )
        parser.add_argument(
            "combined_release_dir", help="Path for output of combined release"
        )

    def handle(self, release_zipfiles, combined_release_dir, **kwargs):
        docs = (
            extract_document(release_zipfile) for release_zipfile in release_zipfiles
        )
        concept_sets = (
            {Concept(**record) for record in load_concepts(doc)} for doc in docs
        )

        concepts_combined = set()
        for concept_set in concept_sets:
            concepts_combined |= concept_set

        pat = re.compile(r"(20\d\d)+")
        release_names = (
            pat.match(Path(release_zipfile).name).group()
            for release_zipfile in release_zipfiles
        )

        combined_release_dir = Path(combined_release_dir)
        combined_release_dir.mkdir(parents=True, exist_ok=True)
        combined_filename = (
            combined_release_dir / f"{'_'.join(release_names)}_combined.pickle"
        )
        with combined_filename.open(mode="wb") as f:
            pickle.dump(concepts_combined, f)
        combined_release_zip = ZipFile(combined_filename.with_suffix(".zip"), mode="w")
        combined_release_zip.write(combined_filename)
        combined_filename.unlink()
