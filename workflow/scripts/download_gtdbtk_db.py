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

def create_http_session():
    """
    Creates HTTP session with retry strategy for requests
    
    Required params:
        None

    Returns:
        session(requests.Session): HTTP session with retry strategy
    """

    s = requests.Session()
    retries = Retry(
        total=5, 
        backoff_factor=1, 
        status_forcelist=[502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("https://", adapter)
    s.mount("http://", adapter)

    return s

def init_worker():

    """
    Initializes worker for multiprocessing pool using factory function 
    
    Required params:
        None

    Returns:
        None
    """

    global session
    session = create_http_session()


def make_request(uri):

    """
    Makes HTTP request and returns result body

    Required params:
        uri(str): URI for request

    Returns:
        text of response
    """

    try:
        with create_http_session() as s:
            r = s.get(uri, timeout=30)
            r.raise_for_status()

            return r.text
    except requests.exceptions.RequestException as errex:
        print(f"Exception: {uri} - {errex}")


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

def download_file(download_dir, url):

    """ 
    Downloads tar section using requests 
    
    Required parameters:
        download_dir(str): directory to save downloaded file in
        url(str): url of file to download
    
    Returns:
        None
    """

    local_filename = url.split('/')[-1]
    local_filename = Path(f'{download_dir}/{local_filename}')

    if not local_filename.exists():
        try:
            with session.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.exceptions.RequestException as errex:
            print(f"Exception: {url} - {errex}")

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

    parser = argparse.ArgumentParser(
        prog = "download_gtdbtk_db.py",
        description="Downloads split gtdbtk database, merges and unpacks"
    )
    parser.add_argument('-d', '--database_dir', action='store', dest="database_dir", required=True)
    parser.add_argument('-r', '--release', action='store', dest="release", required=True)

    args = parser.parse_args()
    database_dir = Path(f"{args.database_dir}/gtdbtk")
    download_dir = Path(f"{args.database_dir}/gtdbtk_download")

    try:
        database_dir.mkdir(exist_ok=True)
    except FileExistsError as e:
        print(e)

    try:
        download_dir.mkdir(exist_ok=True)
    except FileExistsError as e:
        print(e)

    links = get_gtdbtk_part_list(args.release)
    print(f"Found {len(links)} parts to download")

    session = None

    #with multiprocessing.Pool(initializer=init_worker, processes=18) as pool:
    #    results = pool.starmap(download_file, [(download_dir, url) for url in links])

    #pool.close()
    #pool.join()

    unpack(database_dir, download_dir, args.release)

if __name__ == "__main__":
    main()
