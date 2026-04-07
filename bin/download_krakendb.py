#!/usr/bin/env python

"""
Downloads Kraken2 GTDB database
"""

from pathlib import Path
from argparse import ArgumentParser
import tarfile
import os
import threading

import requests

def Handler(start, end, url, filename):
    """
    Handler function for each thread to download a part of the file
    
    Required params:
        start(int): starting byte of the part to download
        end(int): ending byte of the part to download
        url(str): URL of the file to download
        filename(str): name of the file to save the downloaded part
    
    Returns:
        None
    """
    headers = {'Range': f'bytes={start}-{end}'}
    r = requests.get(url, headers=headers, stream=True)
    print(f"Downloading bytes {start} to {end} from {url} to {filename}")
    with open(filename, "r+b") as fp:
        fp.seek(start)
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                fp.write(chunk)
    print(f"Finished downloading bytes {start} to {end} from {url} to {filename}")

def download_file(url_of_file, name, number_of_threads):
    """
    Downloads file using multiple threads
    
    Required params:
        url_of_file(str): URL of file to download
        name(str): name to save file as
        number_of_threads(int): number of threads to use for download
    
    Returns:
        None
    """

    r = requests.head(url_of_file)
    
    if name:
        file_name = name
    else:
        file_name = url_of_file.split('/')[-1]

    try:
        file_size = int(r.headers['Content-Length'])
    except:
        print("Invalid URL or missing Content-Length header.")
        return

    part = file_size // number_of_threads
    with open(file_name, "wb") as fp:
        fp.truncate(file_size)

    threads = []
    for i in range(number_of_threads):
        start = part * i
        # Make sure the last part downloads till the end of file
        end = file_size - 1 if i == number_of_threads - 1 else (start + part - 1)

        t = threading.Thread(target=Handler, kwargs={
            'start': start,
            'end': end,
            'url': url_of_file,
            'filename': file_name
        })
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


def main():
    """ Main process """

    parser = ArgumentParser(description="Download Kraken2 standard database")
    parser.add_argument("-d", "--database_dir", help="directory to save database in", required=True)
    parser.add_argument("-v", "--version", help="database version to download", required=True)
    args = parser.parse_args()

    database_dir = f"{args.database_dir}/kraken2"

    try:
        Path(database_dir).mkdir(exist_ok=True)
    except FileExistsError as e:
        print(e)

    url = f"https://genome-idx.s3.amazonaws.com/kraken/"
    db_url = f"{url}k2_standard_{args.version}.tar.gz"

    local_db_file = Path(f'{database_dir}/k2_standard_{args.version}.tar.gz')

    download_file(db_url, local_db_file, number_of_threads=16)

    with tarfile.open(f"{local_db_file}", "r") as handle:
        handle.extractall(path=f'{database_dir}/', filter="data") 

    os.remove(local_db_file)

if __name__ == "__main__":
    main()
