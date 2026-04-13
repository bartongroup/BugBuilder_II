"""
Functions for extracting assembly statistics from various outputs
"""
import json
import pandas as pd

def get_quast_stats(quast_report,log):
    """
    Extracts key statistics from QUAST report. 

    Required parameters:
        quast_report: Path to the QUAST report.tsv file
        log: Path to log file

    Returns:
        A dictionary with keys: 'assembly_size', 'num_contigs', 'gc_content', 'n50'
    """
    with open(log[0], 'a') as log_file:
        log_file.write(f"Extracting QUAST stats from {quast_report}\n")

        quast_df = pd.read_csv(quast_report, sep='\t', header=None)
        log_file.write("QUAST report loaded successfully.\n")

        quast_df.set_index(0,inplace=True)
        quast_df = quast_df.transpose()

        stats = {
            "assembly_size": int(quast_df['Total length'].values[0]),
            "num_contigs": int(quast_df['# contigs'].values[0]),
            "gc_content": float(quast_df['GC (%)'].values[0]),
            "n50": int(quast_df['N50'].values[0])
        }

        log_file.write("QUAST stats extracted:\n")
        for key, value in stats.items():
            log_file.write(f"{key}: {value}\n")

    return stats

def get_fastp_stats(fastp_json, log):
    """
    Extracts key statistics from fastp JSON report.

    Required parameters:
        fastp_json: Path to the fastp JSON report file
        log: Path to log file

    Returns:
        A dictionary with keys: 'total_bases', 'total_reads', 'q20_bases', 'q30_bases'
    """
    with open(log[0], 'a') as log_file:
        log_file.write(f"Extracting fastp stats from {fastp_json}\n")

        try:
            with open(fastp_json) as f:
                data = json.load(f)
                log_file.write("fastp JSON report loaded successfully.\n")
        except Exception as e:
            log_file.write(f"Error loading fastp JSON report: {e}\n")
            return {}

        stats = {
            "total_bases": int(data['summary']['after_filtering']['total_bases']),
            "total_reads": int(data['summary']['after_filtering']['total_reads']),
        }

        log_file.write("fastp stats extracted:\n")
        for key, value in stats.items():
            log_file.write(f"{key}: {value}\n")

    return stats

def get_nanostat_stats(nanostat_report, log):
    """
    Extracts key statistics from NanoStat report.

    Required parameters:
        nanostat_report: Path to the NanoStat report file
        log: Path to log file

    Returns:
        A dictionary with keys: 'total_bases', 'total_reads', 'mean_length', 'n50'
    """
    with open(log[0], 'a') as log_file:
        log_file.write(f"Extracting NanoStat stats from {nanostat_report}\n")

        nanostat_df = pd.read_csv(nanostat_report, sep='\t')
        log_file.write("NanoStat report loaded successfully.\n")

        nanostat_df.set_index('Metrics',inplace=True)
        nanostat_df = nanostat_df.transpose()

        stats = {
            "total_bases": int(float(nanostat_df['number_of_bases'].values[0])),
            "total_reads": int(float(nanostat_df['number_of_bases'].values[0])),
            "mean_length": int(float(nanostat_df['mean_read_length'].values[0])),
            "n50": int(float(nanostat_df['n50'].values[0])),
        }

        log_file.write("NanoStat stats extracted:\n")
        for key, value in stats.items():
            log_file.write(f"{key}: {value}\n")

    return stats
