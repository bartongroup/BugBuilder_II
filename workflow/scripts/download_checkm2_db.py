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

import requests

script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(script_dir))

from common.download import Handler, download_file_parallel

def main():
    """ Main process """

    parser = ArgumentParser(description="Download checkm2 database")
    parser.add_argument("-d", "--database_dir", help="directory to save database in", required=True)
    args = parser.parse_args()

    database_dir = Path(f"{args.database_dir}/checkm2_db/")

    try:
        database_dir.mkdir(exist_ok=True, parents=True)
    except FileExistsError as e:
        print(e)

    db_url = "https://zenodo.org/records/14897628/files/checkm2_database.tar.gz?download=1"

    local_db_file = database_dir / Path('checkm2_database.tar.gz ')

    download_file_parallel(db_url, local_db_file, number_of_threads=16)

    with tarfile.open(f"{local_db_file}", "r") as handle:
        handle.extractall(path=database_dir, filter="data") 

    os.remove(local_db_file)

if __name__ == "__main__":
    main()
