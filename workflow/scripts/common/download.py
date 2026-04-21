"""
Common functions for downloading files for databases, including GTDB-Tk, Bakta,
and BUSCO lineages
 """

from pathlib import Path
import pprint
import json
import re
import sys
import inspect

import tarfile
import os

import threading
import requests
from requests.adapters import HTTPAdapter, Retry
import portalocker

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

def download_file(url, name):

    """ 
    Downloads tar section using requests 
    
    Required parameters:
        url(str): url of file to download
        name(str): name to save file as
    
    Returns:
        None
    """

    print(f"Downloading {url} to {name}")
    try:
        with create_http_session() as s:
            r = s.get(url, stream=True, timeout=60) 
            r.raise_for_status()
            with open(name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.exceptions.RequestException as errex:
        print(f"Exception: {url} - {errex}")
        raise

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
    print(r.headers)
    
    if name:
        file_name = name
    else:
        file_name = url_of_file.split('/')[-1]

    try:
        file_size = int(r.headers['Content-Length'])
    except:
        print("Invalid URL or missing Content-Length header.")
        return

    print("File size: ", file_size, " bytes")
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

def update_db_version(database_dir, database, version, db_type):

    """
    Updates JSON file with database version information using locking to cope
    with concurrent access

    Required params:
        database_dir(Path): directory where JSON file is located
        database(str): name of database to update version for
        version(str): version number to update in JSON file
        db_type(str): type of database to update

    Returns:
        None
    """
    json_file = Path(f'{database_dir}/db_versions.json')

    if json_file.exists():
        with portalocker.Lock(f'{database_dir}/db_versions.json', 'r+', timeout=10) as version_file:
            try:
                versions = json.load(version_file)
            except json.JSONDecodeError:
                versions = {}

            if db_type is not None:
                version_info = {'version': version, 'type': db_type}
            else:
                version_info = {'version': version}
            versions[database] = version_info

            version_file.seek(0)
            json.dump(versions, version_file, indent=4)
            version_file.truncate()
    else:
        with portalocker.Lock(f'{database_dir}/db_versions.json', 'w', timeout=10) as version_file:
            if db_type is not None:
                versions = {database: {'version': version, 'type': db_type}}
            else:
                versions = {database: {'version': version}}
            json.dump(versions, version_file, indent=4)


def get_zenodo_db_version(doi, version):
    """
    Resolves Zenodo DOI to get record id for database version

    Required params:
        doi(str): 'Concept' (master) DOI of Zenodo record
        version(str): version number of database to resolve (e.g. 'latest', '1.0', '2.0', etc.)

    Returns:
        db_url(str): URL of database file for specified version
        version(str): version number of database selected
    """

    if (version != 'latest' and not re.match(r'^\d+(\.\d+)*$', version)):
        raise ValueError(f"Version ({version}) must be 'latest' or in the format '1.0', '2.0', etc.")

    record_id = doi.split('.')[-1]
    base_url = "https://zenodo.org/api/records/"
    uri = f"{base_url}{record_id}"

    json_response = make_request(uri)
    if json_response is not None:
        response_data = json.loads(json_response)

        # Get the Concept ID (this links all versions together)
        concept_id = response_data.get('conceptrecid')
    
        # Query Zenodo for all records sharing this Concept ID
        versions_url = f"https://zenodo.org/api/records/?q=conceptrecid:{concept_id}&all_versions=True"
        v_response = requests.get(versions_url)
        v_response.raise_for_status()
        all_versions_data = v_response.json()
        
        versions = {}
        for entry in all_versions_data['hits']['hits']:
            versions[entry['metadata'].get('version')] =  {
                "date": entry['metadata'].get('publication_date'),
                "doi": entry['doi'],
                "record_id": entry['id']
            }
        
        # Sort by date or version number if needed
        if version == 'latest':
            latest_version = max(versions.items())
            db_record_id = latest_version[1]['record_id']
            version = latest_version[0]
        else:
            if version in versions:
                db_record_id = versions[version]['record_id']
                version = versions[version]['version']
            else:
                raise ValueError(f"Version ({version}) not found.")
                sys.exit(1)

        return(db_record_id, version)

def get_zenodo_download_url(record_id, type):

    """
    Gets download URL for Zenodo record id

    Required params:
        record_id(str): Zenodo record id for database version
        type(str): type of file to download (e.g. 'full' or 'light')
        
    Returns:
        db_url(str): URL of database file for specified version
    """

    # Identify database name based on calling script
    caller_frame = inspect.stack()[1]
    caller_filename = caller_frame.filename

    if 'bakta' in caller_filename:
        if type == 'full':
            file_name = 'db.tar.xz'
        else:
            file_name = 'db-light.tar.xz'
    elif 'checkm2' in caller_filename:
        file_name = 'checkm2_database.tar.gz'
    else:
        raise ValueError("Unknown database type based on calling script.")
    print(f"Looking for file {file_name} in Zenodo record {record_id}")
    base_url = "https://zenodo.org/api/records/"
    uri = f"{base_url}{record_id}"

    json_response = make_request(uri)
    if json_response is not None:
        response_data = json.loads(json_response)
        files = response_data.get('files', [])
        if files:
            for file in files:
                if file.get('key') == file_name:
                    return file.get('links', {}).get('self')
        else:
            raise ValueError(f"No files found for record ID {record_id}.")
    else:
        raise ValueError(f"Could not retrieve data for record ID {record_id}.")