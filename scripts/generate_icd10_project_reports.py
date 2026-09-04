#!/usr/bin/env python3
"""Generate project-level ICD-10 codelist review reports."""

import sys
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.icd10_project_reports.generate_reports import main


if __name__ == "__main__":
    main()
