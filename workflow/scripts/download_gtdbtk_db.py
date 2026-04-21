#!/usr/bin/env python

"""
Downloads GTDB-TK database sections in parallel, combines and unpacks
"""

import argparse
import multiprocessing 
from pathlib import Path
import shutil
import subprocess
import tarfile

from bs4 import BeautifulSoup
import requests

from requests.adapters import HTTPAdapter, Retry

from common.download import download_file_parallel, make_request, update_db_version

BASE_URL = "https://data.gtdb.aau.ecogenomic.org/releases/"

def get_latest_release(release):

    result = make_request(BASE_URL)
    if result:
        soup = BeautifulSoup(result, 'html.parser')

        versions = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if str(href).startswith('release'):
                versions.append(str(href).replace('release', '').rstrip('/'))
        
        versions = sorted(versions)
        if len(versions) > 0:
            return versions[-1].rstrip('/')
    
    raise RuntimeError("Failed to retrieve GTDB-TK releases from GTDB website.")

def unpack(database_dir, download_dir, release):
    """ 
    Combines separate parts into single tar archive and unpacks 

    Required params:
        database_dir(str): directory to save database in
        download_dir(str): directory where downloaded files are located
        release (str): release version
    
    Returns:
        None
    """

    print(f"Unpacking archive: {download_dir}/gtdbtk_r{release}_data.tar.gz")
    with tarfile.open(f"{download_dir}/gtdbtk_r{release}_data.tar.gz", "r") as handle:
        handle.extractall(path=f"{download_dir}/")

    src_folder = download_dir / f"release{release}"
    for item in src_folder.iterdir():
        target = Path(database_dir) / item.name
        if target.exists():
            if target.is_dir(): shutil.rmtree(target)
            else: target.unlink()
        shutil.move(str(item), str(target))

    shutil.rmtree(download_dir)


def main():
    """ Main process """

    print("Starting GTDB-TK database download and unpacking process")
    parser = argparse.ArgumentParser(
        prog = "download_gtdbtk_db.py",
        description="Downloads split gtdbtk database, merges and unpacks"
    )
    parser.add_argument('-d', '--database_dir', action='store', dest="database_dir", required=True)
    parser.add_argument('-v', '--database_version', action='store', dest="database_version", required=True)

    args = parser.parse_args()
    database_dir = Path(f"{args.database_dir}/gtdbtk")
    download_dir = Path(f"{args.database_dir}/gtdbtk_download")

    if args.database_version != 'latest' and not args.database_version.isdigit():
        raise ValueError("Invalid database version. Must be 'latest' or a number corresponding to GTDB release.")
    
    if args.database_version == 'latest':
        release = get_latest_release(args.database_version)
    else:
        release = args.database_version

    print("GTDB-TK release to download: ", release)
    try:
        database_dir.mkdir(exist_ok=True, parents=True)
    except FileExistsError as e:
        print(e)

    try:
        download_dir.mkdir(exist_ok=True, parents=True)
    except FileExistsError as e:
        print(e)

    download_url = f"{BASE_URL}/release{release}/{release}.0/auxillary_files/gtdbtk_package/full_package/gtdbtk_r{release}_data.tar.gz"
    print(f"Downloading GTDB-TK database from {download_url} to {download_dir}")    

    download_file_parallel(download_url, download_dir / f"gtdbtk_r{release}_data.tar.gz", number_of_threads=16)

    if Path(database_dir).exists():
        print(f"Removing existing GTDB-TK database directory: {database_dir}")
        shutil.rmtree(database_dir)

    unpack(database_dir, download_dir, release)

    update_db_version(args.database_dir, 'gtdbtk', release, None)

if __name__ == "__main__":
    main()
