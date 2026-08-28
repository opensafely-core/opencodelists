import csv
import time
from collections.abc import Generator
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from markdown2 import markdown

from opencodelists.models import User


"""Taken from codelist rot notifier https://github.com/opensafely/dmd-codelist-report/blob/main/notifier/send_email.py"""

FROM_ADDRESS = "OpenCodelists <no-reply@opencodelists.org>"
REPLY_TO = "bennett@phc.ox.ac.uk"
SEED_EMAILS = [
    "jon.massey@thedatalab.org",
    "jon.massey@phc.ox.ac.uk",
]

SUBJECT = "Action recommended: review your ICD-10 codelists on OpenCodelists"

GUIDANCE_PDF_PATH = Path(
    "scripts/icd10_reports/Guidance on updating Codelists after ICD-10 update.pdf"
)
EMAIL_BODY_MD_PATH = Path("scripts/icd10_reports/email_body.md")


def send_email(
    to: str,
    subject: str,
    text: str | None = None,
    html: str | None = None,
    attachments: list[Path] | None = None,
) -> tuple[int, str] | None:
    data = {
        "from": FROM_ADDRESS,
        "to": to,
        "subject": subject,
        "text": text,
        "html": html,
        "h:Reply-To": REPLY_TO,
    }
    attempts = 0
    while True:
        files = (
            [("attachment", a.read_bytes()) for a in attachments] if attachments else []
        )
        response = requests.post(
            settings.ANYMAIL["MAILGUN_API_URL"] + "messages",
            auth=("api", settings.ANYMAIL["MAILGUN_API_KEY"]),
            files=files,
            data=data,
        )
        # 429 codes are either rate exceeded (2 types), or too large
        # https://documentation.mailgun.com/en/latest/api-sending.html#rate-limits
        # with message "<why> limit exceeded, try again" where why=[bytes|request|recipient]
        if response.status_code == "429":
            if response.text.lower().startswith("bytes"):
                raise Exception("Email body or html too large")
            else:
                if attempts >= 5:
                    raise Exception(
                        f"Retry attempts exceeded.\nLast status {response.status_code}:{response.text}"
                    )
                attempts += 1
                time.sleep(0.1)
                continue
        return (response.status_code, response.text)


def check_status():
    rq = requests.get(
        settings.ANYMAIL["MAILGUN_API_URL"] + "events",
        auth=("api", settings.ANYMAIL["MAILGUN_API_KEY"]),
        params={"limit": 5},
    )
    return (rq.status_code, rq.text)


def send_emails(
    path_to_recipients_csv: Path,
    pdfs_dir: Path,
    bypass_name_lookup: bool = False,
    only_seeds: bool = True,
) -> Generator[tuple[str, str, tuple[int, str] | str]]:
    if bypass_name_lookup:
        assert only_seeds, (
            "Name lookup bypass mode only available when sending to seed emails"
        )
    recipients = list(csv.DictReader(path_to_recipients_csv.read_text()))
    for recipient in recipients:
        try:
            email = recipient["email"]
            if only_seeds and email.lower() not in SEED_EMAILS:
                continue
            name = (
                "Name lookup bypassed"
                if bypass_name_lookup
                else User.objects.get(email=email).name
            )
            html = markdown(EMAIL_BODY_MD_PATH.read_text().replace(r"{{Name}}", name))

            resp = send_email(
                to=email,
                subject=SUBJECT.format(recipient["codelist"]),
                attachments=[pdfs_dir / recipient["pdf_filename"], GUIDANCE_PDF_PATH],
                html=html,
                text=BeautifulSoup(html).get_text(),
            )
            if resp:
                yield (recipient["email"], recipient["codelist"], resp)
        except Exception as e:
            yield (recipient["email"], recipient["codelist"], str(e))
