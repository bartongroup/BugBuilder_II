#!/usr/bin/env python
"""
Identifies data files from sample_sheet.xlsx for each sample and copy/download as required
"""

from pathlib import Path,PurePosixPath
import pandas as pd
from shutil import copy
import re
import requests

def download_file(sample_id, url):
    """
    Download a file from a URL and save it locally.

    Required parametsers:
    sample_id: The sample ID for which the file is being downloaded
    url: The URL of the file to download   
    """

    local_name = url.split('/')[-1]
    local_name = re.sub(r'^[0-9]+_', '', local_name)

    local_filename = Path(f"data/{sample_id}/short_reads/{local_name}")
    print("Downloading short read data to:", local_filename) 
    if not local_filename.exists():
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)

def get_data(sample_sheet):
    """
    Identifies data files from sample_sheet.xlsx for each sample and copy/download as required

    :param sample_sheet: Path to sample sheet
    """
    # Read the sample sheet
    df = pd.read_excel(sample_sheet, header=1, skiprows=0, comment = '#')

    # Iterate through each row in the sample sheet
    for index, row in df.iterrows():
        sample_id = str(row['sample_alias'])
        sample_id = sample_id.replace(' ', '')
        short_1 = str(row['Short read data location'])
        short_2 = str(row['Short read data location.1'])
        long_read = str(row['Long read data location'])

        print("Processing sample:", sample_id)
        Path(f'data/{sample_id}').mkdir(exist_ok=True)
        Path(f'data/{sample_id}/short_reads').mkdir(exist_ok=True)

        # cases where we have existing short read data on the cluster filesystem
        if 'estorage' in short_1:
            short_1 = Path(short_1.replace('\\\\estorage.dundee.ac.uk', "").replace('\\', '/'))
        long_read = Path(long_read.replace('\\\\estorage.dundee.ac.uk', "").replace('\\', '/'))

        if short_2 != "nan":
            download_file(sample_id, str(short_1))
            download_file(sample_id, str(short_2))
        else:
            if Path(short_1).exists():
                fastqs = list(short_1.glob(f"*{sample_id}*.fastq.gz"))

            for fastq in fastqs:
                local_name = fastq.name
                local_name = re.sub(r'^[0-9]+_', '', local_name)
                print("local name:", local_name)
                
                dest = Path(f'data/{sample_id}/short_reads/{local_name}')
                if not dest.exists():
                    print(f"Copying short read data: {fastq}")
                    copy(fastq, dest)
        
        if long_read.exists():
            Path(f'data/{sample_id}/long_reads').mkdir(exist_ok=True)

            fastq = list(long_read.glob(f"*{sample_id}*.fastq.gz"))[0]
            local_name = fastq.name
            local_name = re.sub(r'^[0-9L]+_', '', local_name)
            print("long read local name:", local_name)

            dest = Path(f'data/{sample_id}/long_reads/{local_name}')
            if not dest.exists():
                print("copying long read data...")
                copy(fastq, dest) 

if __name__ == "__main__":

    Path('data/').mkdir(exist_ok=True)
    get_data('sample_sheet.xlsx')