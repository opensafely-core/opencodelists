import os
import re
from functools import lru_cache

from django.conf import settings
from django.shortcuts import render

from codelists.models import Codelist


SCREENSHOT_RE = re.compile(r"\n        (.*).png")

doc_sections = [
    "status-of-the-project",
    "what-is-a-codelist",
    "viewing-a-codelist",
    "creating-an-account",
    "organisations",
    "creating-a-codelist-from-scratch",
    "creating-a-codelist-from-a-csv-file",
    "selecting-appropriate-codes",
    "editing-a-codelist",
    "viewing-your-codelists",
    "diffing-codelists",
    "converting-pseudo-bnf-codelists-to-dmd",
    "using-a-codelist-in-opensafely-research",
    "reporting-bugs-requesting-features-and-asking-for-help",
]


def index(request):
    pages = load_pages()
    ctx = {"pages": pages}
    return render(request, "docs/index.html", ctx)


@lru_cache
def load_pages():
    pages = []
    for section in doc_sections:
        with open(os.path.join(settings.BASE_DIR, "userdocs", f"{section}.md")) as f:
            content = f.read()

        # Extract title
        title = content.splitlines()[0]
        assert title[:3] == "## "
        title = title[3:]

        # Remove title from start of content
        content = "\n".join(content.splitlines()[2:])

        # Add number of codelists
        if section == "status-of-the-project":
            content = content.replace("{numcodelists}", str(Codelist.objects.count()))

        # Insert img tags
        content = re.sub(
            SCREENSHOT_RE,
            r'\n<img src="/static/img/docs/\1.png" class="border m-3" />\n',
            content,
        )

        pages.append({"section": section, "title": title, "content": content})

    return pages
