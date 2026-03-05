#!/usr/bin/env python

"""
Downloads BUSCO bacterial lineages 
"""

from io import StringIO
from multiprocessing import Pool
from pathlib import Path
import tarfile
import os

from bs4 import BeautifulSoup
import pandas as pd
import requests
from requests.adapters import HTTPAdapter, Retry

DB_DIR = "databases/busco_lineages/"

def make_request(uri):

    """
    Makes HTTP request and returns result body

    Required params:
        uri(str): URI for request

    Returns:
        text of response
    """

    s = requests.Session()

    retries = Retry(total=10,
              backoff_factor=2,
              status_forcelist=[ 500, 502, 504 ],
              raise_on_status=True)

    s.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        r = s.get(uri, timeout=30)
    except requests.exceptions.RequestException as errex:
        print(f"Exception: {uri} - {errex}")

    return r.text

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
    soup = BeautifulSoup(text, 'html.parser')
    links = soup.find_all('a')

    files = [link.get('href') for link in links if link.get('href')]
    files = [file for file in files if any(lineage in file for lineage in lineages)]
    
    return(files)

def download_file(file):

    """ 
    Downloads tar section using requests and expands
    
    Required parameters:
        file(str): url of file to download
    
    Returns:
        None
    """

    url = f"https://busco-data.ezlab.org/v5/data/lineages/{file}"
    local_filename = Path(f'{DB_DIR}/{file}')
    lineage = file.split(".")[0]

    if not Path(f'{DB_DIR}/{lineage}').exists():
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.exceptions.RequestException as errex:
                print(f"Exception: {url} - {errex}")
                return
    
    with tarfile.open(f"{DB_DIR}/{file}", "r") as handle:
        handle.extractall(path=f'{DB_DIR}/', filter="data") 
    
    os.remove(local_filename)

def main():
    """ Main process """

    try:
        Path('databases/busco_lineages').mkdir(exist_ok=True)
    except FileExistsError as e:
        print(e)


    lineages = get_available_lineages()
    files = get_available_files(lineages)

    pool = Pool(4)
    try:
        results = pool.map(download_file, files)
    except requests.exceptions.RequestException as e:
        print(f'Download failed: {e}')

    pool.close()
    pool.join()


if __name__ == "__main__":
    main()
