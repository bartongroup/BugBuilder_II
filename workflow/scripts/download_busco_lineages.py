#!/usr/bin/env python

"""
Downloads BUSCO bacterial lineages 
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

def get_available_lineages(dataset):

    """
    Retrieves summary and selects bacterial lineages for download
    
    Selects Prokaroyic lineages from odb12 dataset

    Required arguments:
        dataset(str): BUSCO dataset to retrieve lineages from

    Returns:
        files(pd.Serieis): Filenames of bacterial lineages to download
    """

    uri = f"https://busco-data.ezlab.org/v5/data/file_versions.tsv"
    text = make_request(uri)
    df = pd.read_csv(StringIO(text), header = None, sep='\t')
    df.dropna(inplace=True)
    df = df[df[3].str.contains("Prokaryota")]
    df = df[df[0].str.contains(dataset)]

    return df[0]

def get_available_files(lineages):

    """
    Retrieves directory index and selects files for download based
    upon lineages of interest

    Required arguments:
        lineages(pd.Series): Lineages of interest

    Returns:
        files(list): Filenames of bacterial lineages to download
    """
    uri="https://busco-data.ezlab.org/v5/data/lineages/"
    text = make_request(uri)
    if text:
        soup = BeautifulSoup(text, 'html.parser')
        links = soup.find_all('a')

        files = [link.get('href') for link in links if link.get('href')]
        files = [file for file in files if any(lineage in file for lineage in lineages)]
    
        return(files)
    else:
        print(f"Failed to retrieve directory index from {uri}")
        return []

def main():
    """ Main process """

    parser = argparse.ArgumentParser(
        prog = "download_busco_lineages.py",
        description="Downloads busco lineages, and unpacks"
    )
    parser.add_argument('-d', '--database_dir', action='store', dest="database_dir", required=True)
    parser.add_argument('-v', '--database_version', action='store', dest="database_version", default='latest')
    args = parser.parse_args()

    database_dir = Path(f'{args.database_dir}/busco_lineages')

    try:
        database_dir.mkdir(exist_ok=True, parents=True)
    except FileExistsError as e:
        print(e)

    lineages = get_available_lineages(args.database_version)
    files = get_available_files(lineages)

    urls = [f"https://busco-data.ezlab.org/v5/data/lineages/{file}" for file in files]

    session = None

    with multiprocessing.Pool(initializer=init_worker, processes=8) as pool:
        results = pool.starmap(download_file, [(url, f"{database_dir}/{url.split('/')[-1]}") for url in urls])

    pool.close()
    pool.join()

    update_db_version(args.database_dir, 'busco', args.database_version, None)

    

if __name__ == "__main__":
    main()
