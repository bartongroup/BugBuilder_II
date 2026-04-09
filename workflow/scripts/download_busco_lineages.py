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

from common.download import init_worker, download_file, make_request

def get_available_lineages():

    """
    Retrieves summary and selects bacterial lineages for download
    
    Selects Prokaroyic lineages from odb12 dataset

    Required arguments:
        None

    Returns:
        files(pd.Serieis): Filenames of bacterial lineages to download
    """

    uri = f"https://busco-data.ezlab.org/v5/data/file_versions.tsv"
    text = make_request(uri)
    df = pd.read_csv(StringIO(text), header = None, sep='\t')
    df.dropna(inplace=True)
    df = df[df[3].str.contains("Prokaryota")]
    df = df[df[0].str.contains("odb12")]

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
    args = parser.parse_args()

    database_dir = Path(f'{args.database_dir}/busco_lineages')

    try:
        database_dir.mkdir(exist_ok=True, parents=True)
    except FileExistsError as e:
        print(e)

    lineages = get_available_lineages()
    files = get_available_files(lineages)

    session = None

    with multiprocessing.Pool(initializer=init_worker, processes=16) as pool:
        results = pool.starmap(download_file, [(database_dir, file) for file in files])

    pool.close()
    pool.join()

if __name__ == "__main__":
    main()
