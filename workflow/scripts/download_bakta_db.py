#!/usr/bin/env python

"""
Downloads Baktta database
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

    parser = ArgumentParser(description="Download bakta full database")
    parser.add_argument("-d", "--database_dir", help="directory to save database in", required=True)
    parser.add_argument("-v", "--database_version", help="database version to download", default='latest')
    parser.add_argument("-t", "--database_type", help="database type to download (full or light)", default='light')
    args = parser.parse_args()

    database_dir = Path(f"{args.database_dir}/bakta_db")

    try:
        database_dir.mkdir(exist_ok=True, parents=True)
    except FileExistsError as e:
        print(e)

    record_id, version = get_zenodo_db_version('10.5281/zenodo.4247252', args.database_version)
    bakta_url = get_zenodo_download_url(record_id, args.database_type)

    local_db_file = Path(f'{database_dir}/bakta.tar.xz')

    if type == 'full':
        download_file_parallel(bakta_url, local_db_file, number_of_threads=16)
    else:
        download_file(bakta_url, local_db_file)

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

    update_db_version(args.database_dir, 'bakta', version, args.database_type)

    os.remove(local_db_file)

if __name__ == "__main__":
    main()
