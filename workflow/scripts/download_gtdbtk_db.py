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

from common.download import init_worker, download_file, make_request, update_db_version

def get_latest_release(release):

    url = "https://data.gtdb.aau.ecogenomic.org/releases/"

    result = make_request(url)
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

def get_gtdbtk_part_list(release):

    """
    Retrieves data on separate tar sections for gtdbtk database

    Required arguments:
        release(str): GTDB database release number

    Returns:
        uris(list): URIs of tar sections
    """

    base_url = "https://data.gtdb.ecogenomic.org/releases"
    release_path = f"release{release}/{release}.0"
    package_path = "auxillary_files/gtdbtk_package/split_package/"

    uri = f"{base_url}/{release_path}/{package_path}"

    html = make_request(uri)
    if html is not None:
        soup = BeautifulSoup(html, features='lxml')

    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']

        if isinstance(href, str) and href.startswith('gtdb'):
            print(f"Found link: {link.get('href')}")
            part_uri = uri + href
            links.append(part_uri)

    return links

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
    print(f"Looking for split files in {download_dir} with pattern gtdbtk_r{release}_data.tar.gz.part*")
    print(f"Files found: {list(download_dir.glob(f'gtdbtk_r{release}_data.tar.gz.part*'))}")

    parts = [str(p) for p in sorted(download_dir.glob(f"gtdbtk_r{release}_data.tar.gz.part*"))]
    if not parts:
        raise RuntimeError("No split files found.")
    cmd = ['cat'] + parts

    print(f"Combining parts into single archive: {' '.join(cmd)}")
    with open(f"{download_dir}/gtdbtk_r{release}_data.tar.gz", 'wb') as fh:
       subprocess.run(cmd, check=True, stdout = fh)

    print(f"Unpacking combined archive: {download_dir}/gtdbtk_r{release}_data.tar.gz")
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

    links = get_gtdbtk_part_list(release)
    print(f"Found {len(links)} parts to download")

    session = None

    with multiprocessing.Pool(initializer=init_worker, processes=18) as pool:
        results = pool.starmap(download_file, [(url,  f"{download_dir}/{url.split('/')[-1]}") for url in links])

    pool.close()
    pool.join()

    unpack(database_dir, download_dir, release)

    update_db_version(args.database_dir, 'gtdbtk', release, None)

if __name__ == "__main__":
    main()
