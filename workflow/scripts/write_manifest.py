#!/usr/bin/env python

"""
Writes manifest file for ENA submission based on assembly stats and config
Required arguments:
    sample: sample name 
"""
import argparse
from pathlib import Path
import os
import pandas as pd
import yaml

from common.assembly_stats import get_all_quast_stats, get_fastp_stats, \
    get_quast_stats, get_nanostat_stats

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", required=True)
    args = parser.parse_args()

    SAMPLES = Path('data').glob('*')
    SAMPLES = [os.path.basename(x) for x in SAMPLES]
    LONG_SAMPLES = []

    for sample in SAMPLES:
        if os.path.exists(f"data/{sample}/long_reads"):
            LONG_SAMPLES.append(sample)

    with open("workflow/config/config.yaml") as f:
        config = yaml.safe_load(f)

    short_bases = 0
    long_bases = 0
    program = 'SPAdes' 

    sample = args.sample

    # Load quast report
    assembly_stats = get_quast_stats(f"results/quast/{sample}/report.tsv")
    assembly_size = assembly_stats['assembly_size']
    
    fastp_stats = get_fastp_stats(f"results/trimmed_short_reads/{sample}_fastp.json")
    short_bases = fastp_stats['total_bases']

    if sample in LONG_SAMPLES:
        nanostat_stats = get_nanostat_stats(f"results/long_read_stats/{sample}_trimmed_nanostat.txt")
        long_bases = nanostat_stats['total_bases']
        program = 'flye, unicycler'

    coverage = int((short_bases + long_bases) / assembly_size) if assembly_size > 0 else 0

    samples_file = Path('workflow/config/samples.csv')
    runs_file = Path('workflow/config/runs.csv')

    sample_id = 'Unknown'
    run_id = 'Unknown'

    if samples_file.exists() and runs_file.exists():
        samples_df = pd.read_csv(samples_file)
        runs_df = pd.read_csv(runs_file)
        ena_df = samples_df.merge(runs_df, left_on='id', right_on='sampleId', how='outer', suffixes=('_samples', '_runs'))
        sample_info = ena_df[ena_df['alias_samples'] == sample]

        sample_id = sample_info['id_samples'].values[0] if not sample_info.empty else None
        run_id = ','.join(sample_info['id_runs'].values) if not sample_info.empty else None
    
    # Combine into manifest
    manifest_df = pd.DataFrame({
        'STUDY': [config['project_id']],
        'SAMPLE': sample_id,
        'ASSEMBLYNAME': [sample],
        'ASSEMBLY_TYPE': 'isolate',
        'COVERAGE': coverage,
        'PROGRAM': program,
        'PLATFORM': config['short_read_instrument'] + (f", {config['long_read_instrument']}" \
            if long_bases > 0 else ""),
        'MOLECULE_TYPE': 'genomic DNA',
        'RUN_REF': run_id,
        'FLATFILE': f"{sample}.embl.gz"
    })

    manifest_df = manifest_df.transpose()
    manifest_df.to_csv(f"results/manifests/{sample}_manifest.tsv", sep='\t', index=True, header=False)