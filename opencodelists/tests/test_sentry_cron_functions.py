import json
import subprocess


# Dummy organisation and project identifiers in URL
SENTRY_DSN = "https://ecae920f60aa7a6a3e16d50d121ce4f2@o123456.ingest.sentry.io/7891023"
SENTRY_CRON_URL = "https://ecae920f60aa7a6a3e16d50d121ce4f2@o123456.ingest.sentry.io/api/7891023/cron/test_monitor"
CRONTAB = "5 23 * * 1 "


def test_extract_crontab_json(tmp_path):
    app_json = tmp_path / "app.json"
    with app_json.open("w") as f:
        cron_dict = {
            "cron": [
                {
                    "command": "test_command",
                    "schedule": CRONTAB,
                }
            ]
        }
        json.dump(cron_dict, f, indent=1)

    proc = subprocess.run(
        f"source deploy/bin/sentry_cron_functions.sh; extract_crontab test_command {app_json}",
        shell=True,
        capture_output=True,
        executable="/bin/bash",
    )

    assert proc.stdout.decode().strip("\n") == CRONTAB


def test_extract_crontab_cronfile(tmp_path):
    cronfile = tmp_path / "cronfile"
    with cronfile.open("w") as f:
        lines = [
            "#test comment",
            "ENV_VAR=VAR_ENV",
            "5 23 * * 2 test_user test_command arg_test",
            f"{CRONTAB} test_user test_command test_arg",
            "5 23 * * 2 test_user test_command test_arg_1234",
        ]
        f.writelines([line + "\n" for line in lines])

    proc = subprocess.run(
        f"source deploy/bin/sentry_cron_functions.sh; extract_crontab test_arg {cronfile}",
        shell=True,
        capture_output=True,
        executable="/bin/bash",
    )

    assert proc.stdout.decode().strip("\n") == CRONTAB


def test_sentry_cron_url():
    proc = subprocess.run(
        f"source deploy/bin/sentry_cron_functions.sh; sentry_cron_url {SENTRY_DSN} test_monitor",
        shell=True,
        capture_output=True,
        executable="/bin/bash",
    )

    assert proc.stdout.decode().strip("\n") == SENTRY_CRON_URL
