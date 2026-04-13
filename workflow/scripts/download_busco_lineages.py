#!/usr/bin/env python

"""
Downloads BUSCO bacterial lineages 

Container somehow makes buscos inbuilt download function a bit broken, so do it ourselves....
"""

import argparse
from io import StringIO
import multiprocessing
from pathlib import Path
import tarfile
import os

from bs4 import BeautifulSoup
import pandas as pd
import requests
from requests.adapters import HTTPAdapter, Retry

from common.download import init_worker, download_file, make_request, update_db_version

def get_available_lineages(url, dataset):

    """
    Retrieves summary and selects bacterial lineages for download
    
    Selects Prokaroyic lineages from odb12 dataset

    Required arguments:
        url(str): URL for retrieving summary of available lineages
        dataset(str): BUSCO dataset to retrieve lineages from

    Returns:
        files(pd.Serieis): Filenames of bacterial lineages to download
    """

    uri = f"{url}/file_versions.tsv"
    text = make_request(uri)
    df = pd.read_csv(StringIO(text), header = None, sep='\t')
    df.dropna(inplace=True)
    df = df[df[3].str.contains("Prokaryota")]
    df = df[df[0].str.contains(dataset)]

    return list(df[0])

def get_files(url, filter):

    """
    Retrieves directory index and selects files for download based
    upon lineages of interest

    Required arguments:
        url(str): URL for retrieving directory index of lineage files
        filter(list): whitelist of files to download

    Returns:
        files(list): Filenames of bacterial lineages to download
    """

    text = make_request(url)
    if text:
        soup = BeautifulSoup(text, 'html.parser')
        links = soup.find_all('a')

        files = [link.get('href') for link in links if link.get('href')]
        files = [file for file in files if file != '../'] # exclude parent directory link
        if filter:
            files = [file for file in files if any(f in file for f in filter)]
        
        return(files)
    else:
        print(f"Failed to retrieve directory index from {url}")
        return []

def download_lineages(database_dir, database_version, url):

    """
    Downloads BUSCO bacterial lineage files in parallel

    Required arguments:
        database_dir(str): Directory to save lineage files in
        database_version(str): Version of BUSCO dataset to download lineages for
        url(str): Base URL for downloading lineage files

    Returns:  None
    """

    lineage_dir = Path(f'{database_dir}/busco/lineages/')

    try:
        lineage_dir.mkdir(exist_ok=True, parents=True)
    except FileExistsError as e:
        print(e)

    lineages = get_available_lineages(url, database_version)
    files = get_files(f"{url}/lineages", lineages)

    urls = [f"{url}/lineages/{file}" for file in files]

    session = None

    with multiprocessing.Pool(initializer=init_worker, processes=8) as pool:
        results = pool.starmap(download_file, [(url, f"{lineage_dir}/{url.split('/')[-1]}") for url in urls])

    pool.close()
    pool.join()

def unpack_tarfile(tar_file, output_dir):
    
    """
    Unpacks tar file to output directory

    Required arguments:
        tar_file(str): Path to tar file to unpack
        output_dir(str): Directory to unpack tar file to

    Returns:  None
    """

    try:
        with tarfile.open(tar_file, "r") as handle:
            handle.extractall(path=output_dir, filter="data") 
        
        os.remove(tar_file)
    except tarfile.TarError as e:
        print(f"Error unpacking {tar_file}: {e}")

def unpack_lineages(database_dir):
    """
    Unpacks downloaded lineage files

    Required arguments:
        database_dir(str): Directory to save lineage files in

    Returns:  None
    """

    lineage_dir = Path(f'{database_dir}/busco/lineages')
    lineages = list(lineage_dir.glob("*.tar.gz"))

    with multiprocessing.Pool(processes=8) as pool:
        pool.starmap(unpack_tarfile, [(file, lineage_dir) for file in lineages])


def download_information(database_dir, url):

    """
    Downloads BUSCO information files

    Required arguments:
        database_dir(str): Directory to save information file in
        url(str): Base URL for downloading information file

    Returns:  None
    """

    info_url = f"{url}/information"
    information_dir = Path(f'{database_dir}/busco/information')

    information_dir.mkdir(exist_ok=True, parents=True)
    information_files = get_files(info_url, None)

    if not information_files:
        print(f"No information files found at {info_url}")
        raise ValueError(f"No information files found at {info_url}")

    for file in information_files:
        local_info_file = information_dir / Path(str(file)).name
        download_file(info_url, local_info_file)

def download_placement_files(database_dir, database_version, url):
    """
    Downloads BUSCO placement files

    Required arguments:
        database_dir(str): Directory to save placement files in
        database_version(str): Version of BUSCO dataset to download placement files for
        url(str): Base URL for downloading placement files

    Returns:  None
    """

    placement_url = f"{url}/placement_files"
    placement_dir = Path(f'{database_dir}/busco/information')

    placement_dir.mkdir(exist_ok=True, parents=True)
    placement_files = get_files(placement_url, [database_version])

    if not placement_files:
        print(f"No placement files found at {placement_url} for version {database_version}")
        raise ValueError(f"No placement files found at {placement_url} for version {database_version}")

    for file in placement_files:
        local_placement_file = placement_dir / Path(str(file)).name
        download_file(placement_url, local_placement_file)


def main():
    """ Main process """

    parser = argparse.ArgumentParser(
        prog = "download_busco_lineages.py",
        description="Downloads busco lineages, and unpacks"
    )
    parser.add_argument('-d', '--database_dir', action='store', dest="database_dir", required=True)
    parser.add_argument('-v', '--database_version', action='store', dest="database_version", default='latest')
    args = parser.parse_args()

    database_dir = Path(f'{args.database_dir}/busco')
    url = "https://busco-data.ezlab.org/v5/data/"

    database_dir.mkdir(exist_ok=True, parents=True)

    download_lineages(args.database_dir, args.database_version, url)
    unpack_lineages(args.database_dir)
    download_information(args.database_dir, url)
    download_placement_files(args.database_dir, args.database_version, url)

    update_db_version(args.database_dir, 'busco', args.database_version, None)

    # database contents are not readily deterministic, so we can't reliably
    # check for completeness based on file presence. Instead, we will just
    # create a flag to indicate that the download process has completed.
    Path(f'{database_dir}/download.complete').touch()

    

if __name__ == "__main__":
    main()
