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

from common.download import download_file_parallel, update_db_version

def main():
    """ Main process """

    parser = ArgumentParser(description="Download Kraken2 standard database")
    parser.add_argument("-d", "--database_dir", help="directory to save database in", required=True)
    parser.add_argument("-v", "--database_version", help="database version to download", required=True)
    parser.add_argument("-t", "--database_type", 
                        help="database type to download (standard or standard-16)", 
                        default='standard-16') 
    args = parser.parse_args()

    database_dir = Path(f"{args.database_dir}/kraken2")
    if args.database_type != 'standard' and args.database_type != 'standard-16' and args.database_type != 'standard-8':
        raise ValueError("Invalid database type. Must be 'standard', 'standard-16' or 'standard-8'.")

    try:
        database_dir.mkdir(exist_ok=True, parents=True)
    except FileExistsError as e:
        print(e)

    url = f"https://genome-idx.s3.amazonaws.com/kraken/"

    if args.database_type == 'standard':
        url += f"k2_standard_{args.database_version}.tar.gz"
    elif args.database_type == 'standard-16':
        url += f"k2_standard_16_GB_{args.database_version}.tar.gz"
    elif args.database_type == 'standard-8':
        url += f"k2_standard_08_GB_{args.database_version}.tar.gz"
        
    local_db_file = database_dir / Path(f'k2_{args.database_version}.tar.gz')

    download_file_parallel(url, local_db_file, number_of_threads=16)

    with tarfile.open(f"{local_db_file}", "r") as handle:
        handle.extractall(path=f'{database_dir}/', filter="data") 
    
    update_db_version(args.database_dir, 'kraken', args.database_version, args.database_type)

    os.remove(local_db_file)

if __name__ == "__main__":
    main()
