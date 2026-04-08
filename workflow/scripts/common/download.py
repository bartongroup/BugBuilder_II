"""
Common functions for downloading files for databases, including GTDB-Tk, Bakta,
and BUSCO lineages
 """

from pathlib import Path
import tarfile
import os

import threading
import requests
from requests.adapters import HTTPAdapter, Retry

def create_http_session():
    """
    Factory function which creates requests session 
    
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

def Handler(start, end, url, filename):
    """
    Handler function for multithreaded download for each part of a file
    
    Required params:
        start(int): starting byte of the part to download
        end(int): ending byte of the part to download
        url(str): URL of the file to download
        filename(str): name of the file to save the downloaded part
    
    Returns:
        None
    """
    headers = {'Range': f'bytes={start}-{end}'}
    try:
        with create_http_session() as s:
            print(f"Downloading bytes {start} to {end} from {url} to {filename}")
            r = s.get(url, headers=headers, stream=True)

            with open(filename, "r+b") as fp:
                fp.seek(start)
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        fp.write(chunk)
            print(f"Finished downloading bytes {start} to {end} from {url} to {filename}")
    except requests.exceptions.RequestException as errex:
        print(f"Exception while downloading bytes {start} to {end} from {url} to {filename} - {errex}")

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

def download_file(download_dir, url):

    """ 
    Downloads tar section using requests 
    
    Required parameters:
        download_dir(Path): directory to save downloaded file in
        url(str): url of file to download
    
    Returns:
        None
    """

    local_filename = Path(url.split('/')[-1])
    local_filename = download_dir / local_filename

    try:
        with create_http_session() as s:
            r = s.get(url, stream=True, timeout=60) 
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.exceptions.RequestException as errex:
        print(f"Exception: {url} - {errex}")

def download_file_parallel(url_of_file, name, number_of_threads):
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
