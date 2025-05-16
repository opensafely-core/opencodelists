from pathlib import Path

from django.conf import settings

from ..views import SCREENSHOT_RE


def test_docs_screenshots_are_used():
    screenshots = [
        filepath.stem for filepath in Path(settings.SCREENSHOT_DIR).glob("**/*.png")
    ]

    docs = Path(settings.BASE_DIR / "userdocs").glob("**/*.md")
    screenshots_in_docs = []
    for filepath in docs:
        matches = SCREENSHOT_RE.findall(filepath.read_text())
        screenshots_in_docs.extend(matches)

    unused_screenshots = set(screenshots) - set(screenshots_in_docs)
    assert not unused_screenshots, (
        f"Found screenshot files that are not used in docs: {unused_screenshots}"
    )

    not_found_screenshots = set(screenshots_in_docs) - set(screenshots)
    assert not not_found_screenshots, (
        f"Missing screenshot files referenced in docs: {not_found_screenshots}"
    )
