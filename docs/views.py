import os
import re
from functools import lru_cache

from django.conf import settings
from django.shortcuts import render

from codelists.models import Codelist

doc_sections = [
    "status-of-the-project",
    "viewing-a-codelist",
    "creating-an-account",
    "creating-a-codelist-from-scratch",
    "creating-a-codelist-from-a-csv-file",
    "editing-a-codelist",
    "using-a-codelist-in-opensafely-research",
    "future-plans",
    "reporting-bugs-requesting-features-and-asking-for-help",
]


def xindex(request):
    with open(os.path.join(settings.BASE_DIR, "docs", "content.md")) as f:
        content = f.read()

    content = re.sub(
        r"\n        (.*).png\n",
        r'\n<img src="/static/img/docs/\1.png" class="border m-3" />\n',
        content,
    )

    content = content.replace("{numcodelists}", str(Codelist.objects.count()))

    ctx = {"content": content}
    return render(request, "docs/index.html", ctx)


def index(request):
    pages = load_pages()
    ctx = {"pages": pages}
    return render(request, "docs/index.html", ctx)


# Until https://code.djangoproject.com/ticket/32314 lands, comment out @lru_cache() in
# development.
@lru_cache()
def load_pages():
    pages = []
    for section in doc_sections:
        with open(os.path.join(settings.BASE_DIR, "docs", f"{section}.md")) as f:
            content = f.read()

        # Extract title
        title = content.splitlines()[0]
        assert title[:3] == "## "
        title = title[3:]

        # Remove title from start of content
        content = "\n".join(content.splitlines()[2:])

        # Add number of codelists
        if section == "status-of-project":
            content = content.replace("{numcodelists}", str(Codelist.objects.count()))

        # Insert img tags
        content = re.sub(
            r"\n        (.*).png",
            r'\n<img src="/static/img/docs/\1.png" class="border m-3" />\n',
            content,
        )

        pages.append({"section": section, "title": title, "content": content})

    return pages
