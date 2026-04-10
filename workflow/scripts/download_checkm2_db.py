#!/usr/bin/env python

"""
Downloads checkm2 database
"""

from pathlib import Path
from argparse import ArgumentParser
import tarfile
import os
import sys
import threading
import json

import requests

script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(script_dir))

from common.download import download_file, download_file_parallel, update_db_version, get_zenodo_download_url, get_zenodo_db_version

def main():
    """ Main process """

    parser = ArgumentParser(description="Download checkm2 database")
    parser.add_argument("-d", "--database_dir", help="directory to save database in", required=True)
    parser.add_argument("-v", "--database_version", help="database version to download", default='latest')
    args = parser.parse_args()

    database_dir = Path(f"{args.database_dir}/checkm2_db/")

    try:
        database_dir.mkdir(exist_ok=True, parents=True)
    except FileExistsError as e:
        print(e)

    record_id, version = get_zenodo_db_version('10.5281/zenodo.4626518', args.database_version)
    print(record_id, version)
    db_url = get_zenodo_download_url(record_id, None)
    print(f"Downloading {db_url}")

    local_db_file = database_dir / Path('checkm2_database.tar.gz ')

    download_file_parallel(db_url, local_db_file, number_of_threads=16)

    with tarfile.open(f"{local_db_file}", "r") as handle:
        # Strip the leading directory from the member names
        members = []
        for member in handle.getmembers():
            parts = member.name.split(os.sep)
            
            if len(parts) > 1:
                member.name = os.path.join(*parts[1:])
                members.append(member)
        
        # Extract only the modified members
        handle.extractall(path=database_dir, members=members, filter="data")

    os.remove(local_db_file)

    update_db_version(args.database_dir, 'checkm2', version, None)

if __name__ == "__main__":
    main()
