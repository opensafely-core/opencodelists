"""
A script to retrieve all vmp xml files from every available release on OpenPrescribing,
extract the previous VMP ID for each VMP ID that has one and write them to a single
CSV file.

This script is intended to be run on a local machine, by a user with ssh access to
largeweb2. It retrieves data for historic VMP ID changes and should not need to be re-run,
as dm+d's import_data script now also updates the mapping for each new release.

It exists here for information only.

Run with:
    python scripts/fetch_vmp_prev.py
    -u <github username>
    -k /path/to/ed25519/key/file
    -p <largeweb2 password>
    -o path/to/local/output/dir
"""

import csv
import fnmatch
import gzip
import os
import shutil
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from stat import S_ISDIR

import paramiko
from lxml import etree
from tqdm import tqdm


def iter_vmps(vmp_filepath):
    with open(vmp_filepath) as f_in:
        doc = etree.parse(f_in)
    for vmp_element in list(doc.getroot())[1]:
        record = {e.tag: e.text for e in vmp_element}
        if record.get("VPIDPREV"):
            yield (record["VPID"], record.get("VPIDPREV"))


def get_ssh_creds(host, host_username, keyfile, keyfile_pwd):
    return {
        "host": host,
        "username": host_username,
        "keyfile": keyfile,
        "pwd": keyfile_pwd,
    }


def iter_vmp_files(ftp, download_folders, output_dir):
    for download_folder in tqdm(download_folders):
        for entry in ftp.listdir_attr(download_folder):
            mode = entry.st_mode
            if S_ISDIR(mode):
                download_subdir = os.path.join(download_folder, entry.filename)
                for filename in ftp.listdir(download_subdir):
                    if fnmatch.fnmatch(filename, "f_vmp2_*.xml"):
                        vmp_file = os.path.join(download_subdir, filename)
                        local_filepath = os.path.join(output_dir, filename)
                        ftp.get(vmp_file, local_filepath)
                        yield Path(local_filepath), vmp_file


def parse_vmp_xml_files(creds, remote_dir, output_dir):
    with paramiko.SSHClient() as ssh_client:
        # create the ssh connections and open ftp
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key = paramiko.Ed25519Key.from_private_key_file(
            creds["keyfile"], password=creds["pwd"]
        )
        ssh_client.connect(
            creds["host"], username=creds["username"], pkey=private_key, password=""
        )
        ftp = ssh_client.open_sftp()

        # make a list of all the dm+d release download folders in the largeweb2 remote_dir
        download_folders = []
        for entry in ftp.listdir_attr(remote_dir):
            mode = entry.st_mode
            if S_ISDIR(mode):
                download_folders.append(os.path.join(remote_dir, entry.filename))

        # For each download folder
        # 1) Find any file that matches the VMP xml pattern ("f_vmp2_*.xml")
        # 2) Download the xml file to the local output dir
        # 3) Open the xml file and find (vpid, vpidprev) pairs (only for VMPs that have a previous)
        # 4) Write each pair to an output CSV file, along with its remote filepath for reference
        # 5) Delete the locally downloaded file
        output_path = (
            Path(output_dir)
            / f"dmd_vpid_vpidprev_mapping_{datetime.today().date()}.csv"
        )
        with open(output_path, "w") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["vpid", "vpidprev", "source_file"])
            for locally_downloaded_file, remote_filepath in iter_vmp_files(
                ftp, download_folders, output_dir
            ):
                for row in iter_vmps(locally_downloaded_file):
                    writer.writerow([*row, remote_filepath])
                locally_downloaded_file.unlink()
        # Finally, gzip the csv file
        with open(output_path, "rb") as f_in:
            with gzip.open(output_path.with_suffix(".csv.gz"), "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        output_path.unlink()

        ftp.close()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-u", dest="username", help="ssh username", required=True)
    parser.add_argument("--host", dest="host", default="largeweb2.ebmdatalab.net")
    parser.add_argument(
        "-k", dest="keyfile", help="path/to/ed25519/key/file", required=True
    )
    parser.add_argument(
        "-p", dest="pwd", help="Password for ssk key file", required=True
    )
    parser.add_argument(
        "--remote-dir",
        dest="remote_dir",
        default="/home/hello/openprescribing-data/data/dmd",
    )
    parser.add_argument(
        "-o", dest="output_dir", help="path/to/local/output/dir", required=True
    )
    args = parser.parse_args()
    credentials = get_ssh_creds(args.host, args.username, args.keyfile, args.pwd)
    parse_vmp_xml_files(credentials, args.remote_dir, args.output_dir)
