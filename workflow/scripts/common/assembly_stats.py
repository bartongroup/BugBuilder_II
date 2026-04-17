"""
Functions for extracting assembly statistics from various outputs
"""
import json
import pandas as pd
import re
from pathlib import Path

from Bio import SeqIO

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
        for key,value in quast_df.items():
            log_file.write(f"{key}: {value.values[0]}\n")

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

def get_all_quast_stats(quast_reports, log):
    """
    Extracts all statistics from QUAST reports for multiple samples.

    Required parameters:
        quast_reports: List of paths to QUAST report.tsv files for each sample
        log: Path to log file

    Returns:
        A dataframe containgong one row per sample and columns for each QUAST statistic
    """
    all_stats = {}
    for report in quast_reports:
        sample_name = Path(report).parent.name
        stats = get_quast_stats(report, log)
        all_stats[sample_name] = stats

    all_stats_df = pd.DataFrame.from_dict(all_stats, orient='index')
    return all_stats_df

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
        print(nanostat_df)
        log_file.write("NanoStat report loaded successfully.\n")

        nanostat_df.set_index('Metrics',inplace=True)
        nanostat_df = nanostat_df.transpose()

        stats = {
            "total_bases": int(float(nanostat_df['number_of_bases'].values[0])),
            "total_reads": int(float(nanostat_df['number_of_reads'].values[0])),
            "mean_length": int(float(nanostat_df['mean_read_length'].values[0])),
            "n50": int(float(nanostat_df['n50'].values[0])),
        }

        log_file.write("NanoStat stats extracted:\n")
        for key, value in stats.items():
            log_file.write(f"{key}: {value}\n")

    return stats

def get_checkm2_stats(checkm2_reports, log):
    """
    Extracts key statistics from CheckM2 quality report.

    Required parameters:
        checkm2_dir: List of paths to CheckM2 quality report TSV files
        log: Path to log file

    Returns:
        A dataframe containing one row per sample and columns for each CheckM2 statistic
    """

    with open(log[0], 'a') as log_file:
        all_stats = {}
        for report in checkm2_reports:
            sample_name = Path(report).parent.name
            log_file.write(f"Processing CheckM2 report for sample: {sample_name}\n")
            try:
                df = pd.read_csv(report, sep='\t')
                log_file.write(f"CheckM2 report for {sample_name} loaded successfully.\n")
            except Exception as e:
                log_file.write(f"Error loading CheckM2 report for {sample_name}: {e}\n")
                continue

            stats = {
                "completeness": float(df['Completeness'].values[0]),
                "contamination": float(df['Contamination'].values[0]),
            }
            all_stats[sample_name] = stats

            log_file.write(f"CheckM2 stats extracted for {sample_name}:\n")
            for key, value in stats.items():
                log_file.write(f"{key}: {value}\n")

        all_stats_df = pd.DataFrame.from_dict(all_stats, orient='index')
        print(all_stats_df)

        return all_stats_df

def extract_trna_amino_acid(tRNA_string):
    """
    Extracts the amino acid from a tRNA description string.

    Required parameters:
    tRNA_string: A string describing the tRNA, e.g. "tRNA-Met"

    Returns: 
        The amino acid associated with the tRNA, e.g. "Met"
    """
    # Regex searches for text between 'tRNA-' and either a digit or '('
    match = re.search(r'tRNA-([a-zA-Z]+)', tRNA_string)
    if match:
        aa = match.group(1)
        return aa
    return None

def extract_RNA_seqs(bakta_dir, log):
    """
    Extracts statistics on RNA sequences from the assembly FASTA file, while
    also extracting the 16S sequences.  tRNAs are classified accoring to the
    unique amino acid they code for, and the number of unique amino acids is
    also counted.

    Note that fMet tRNAs are classfied separately from Met, and Ile2 tRNA are
    classified separately from Ile, as these are functionally distinct.

    Required parameters:
        bakta_dir: Path to the directory containing Bakta annotation results
        log: Path to log file
    Returns:
        dictionary with keys '16S_rRNA', '23S_rRNA', '5S_rRNA' and values counts of sequences
    """

    with open(log[0], 'a') as log_file:
        rna_stats = {}

        assembly_files = list(Path(bakta_dir).rglob('*.ffn'))

        for assembly in assembly_files:

            sample = assembly.parent.name
            log_file.write(f"Processing assembly for sample: {sample}")

            RNA_counts = {
                '16S_rRNA': 0,
                '23S_rRNA': 0,
                '5S_rRNA': 0
            }

            rRNA_sequences = {
                '16S_rRNA': [],
                '23S_rRNA': [],
                '5S_rRNA': []
            }

            tRNAs = []
            for record in SeqIO.parse(assembly, "fasta"):
                description = record.description
                if '16S ribosomal RNA' in description: 
                    RNA_counts['16S_rRNA'] += 1
                    rRNA_sequences['16S_rRNA'].append(record)
                elif '23S ribosomal RNA' in description:
                    RNA_counts['23S_rRNA'] += 1
                    rRNA_sequences['23S_rRNA'].append(record)
                elif '5S ribosomal RNA' in description:
                    RNA_counts['5S_rRNA'] += 1
                    rRNA_sequences['5S_rRNA'].append(record)

                # tRNA regex looks for 'tRNA-' followed by an optional lowercase
                # letter (for fMet), then an uppercase letter, then three
                # lowercase letters (for the amino acid), with an optional '2' for Ile2 
                elif re.search(r'tRNA-[f]?[A-Z][a-z]{2}[2]?', description):
                    tRNAs.append(description)

            RNA_counts['tRNAs (total)'] = len(tRNAs)
            tRNAs = list(set(tRNAs))  # Get unique tRNA types
            RNA_counts['tRNAs (unique)'] = len(tRNAs)
            print(tRNAs)
            AAs = [extract_trna_amino_acid(tRNA) for tRNA in tRNAs]
            RNA_counts['tRNA amino acids'] = len(sorted(set(AAs))) 

            rna_stats[sample] = RNA_counts

            rna_stats_df = pd.DataFrame.from_dict(rna_stats, orient='index')

            # Write out fasta files for rRNA sequeunces
            for rRNA_type, sequences in rRNA_sequences.items():
                rRNA_fasta = assembly.parent / f"{sample}_{rRNA_type}.fasta"
                for sequence in sequences:
                    sequence.id = f"{sample}_{rRNA_type}"
                    sequence.description = ""   
                SeqIO.write(sequences, rRNA_fasta, "fasta")
        
        return rna_stats_df