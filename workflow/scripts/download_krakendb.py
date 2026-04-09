#!/usr/bin/env python

"""
Downloads Kraken2 GTDB database
"""

from pathlib import Path
from argparse import ArgumentParser
import tarfile
import os
import sys

import threading
import requests

script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(script_dir))

from common.download import download_file_parallel

def main():
    """ Main process """

    parser = ArgumentParser(description="Download Kraken2 standard database")
    parser.add_argument("-d", "--database_dir", help="directory to save database in", required=True)
    parser.add_argument("-v", "--version", help="database version to download", required=True)
    args = parser.parse_args()

    database_dir = Path(f"{args.database_dir}/kraken2")

    try:
        database_dir.mkdir(exist_ok=True, parents=True)
    except FileExistsError as e:
        print(e)

    url = f"https://genome-idx.s3.amazonaws.com/kraken/"
    db_url = f"{url}k2_standard_{args.version}.tar.gz"

    local_db_file = database_dir / Path(f'k2_standard_{args.version}.tar.gz')

    download_file_parallel(db_url, local_db_file, number_of_threads=16)

    with tarfile.open(f"{local_db_file}", "r") as handle:
        handle.extractall(path=f'{database_dir}/', filter="data") 

    os.remove(local_db_file)

if __name__ == "__main__":
    main()
