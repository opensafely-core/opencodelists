import subprocess


def test_import_usage_script_has_valid_bash_syntax():
    proc = subprocess.run(
        "bash -n deploy/bin/import_usage.sh",
        shell=True,
        capture_output=True,
        executable="/bin/bash",
    )

    assert proc.returncode == 0, proc.stderr.decode().strip("\n")
