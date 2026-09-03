import csv
import os
import time
from collections.abc import Generator
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from markdown2 import markdown


"""Taken from codelist rot notifier https://github.com/opensafely/dmd-codelist-report/blob/main/notifier/send_email.py"""

FROM_ADDRESS = "OpenCodelists <no-reply@opencodelists.org>"
REPLY_TO = "bennett@phc.ox.ac.uk"
SUBJECT = "Action recommended: review your ICD-10 codelists on OpenCodelists"

GUIDANCE_PDF_PATH = Path(
    "scripts/icd10_reports/Guidance on updating Codelists after ICD-10 update.pdf"
)
EMAIL_BODY_MD_PATH = Path("scripts/icd10_reports/email_body.md")


def _mailgun_url(path: str) -> str:
    return f"{settings.ANYMAIL['MAILGUN_API_URL']}/{settings.ANYMAIL['MAILGUN_SENDER_DOMAIN']}/{path}"


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
            [("attachment", (a.name, a.read_bytes())) for a in attachments]
            if attachments
            else []
        )
        response = requests.post(
            _mailgun_url("messages"),
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
        _mailgun_url("events"),
        auth=("api", settings.ANYMAIL["MAILGUN_API_KEY"]),
        params={"limit": 5},
    )
    return (rq.status_code, rq.text)


def send_emails(
    path_to_recipients_csv: Path = Path("scripts/icd10_reports/reports/recipients.csv"),
    pdfs_dir: Path = Path("scripts/icd10_reports/reports/users"),
    only_seeds: bool = True,
    dry_run: bool = True,
) -> Generator[tuple[str, tuple[int, str] | str]]:
    seed_emails = os.environ.get("SEED_EMAILS", "").split(",")
    if only_seeds and not any(seed_emails):
        raise ValueError(
            "SEED_EMAILS environment variable must be set when only_seeds is True"
        )
    recipients = {
        (r["email"], r["org"], r["pdf_filename"])
        for r in csv.DictReader(path_to_recipients_csv.open())
        if r["type"] == "User"
    }
    for email, name, pdf_filename in recipients:
        if only_seeds and email.lower() not in seed_emails:
            continue
        if dry_run:
            print(
                f"Would send email to {name} at {email} with attachment {pdf_filename}"
            )
            continue
        try:
            html = markdown(EMAIL_BODY_MD_PATH.read_text().replace(r"{{Name}}", name))

            resp = send_email(
                to=email,
                subject=SUBJECT,
                attachments=[pdfs_dir / pdf_filename, GUIDANCE_PDF_PATH],
                html=html,
                text=BeautifulSoup(html, features="lxml").get_text(),
            )
            if resp:
                yield (email, resp)
        except Exception as e:
            yield (email, str(e))
