# Helper functions used directly dwithin workflow
import os

def get_spades_mode(wildcards, config, input):
    """
    Determine SPAdes mode based on estimated coverage from input FASTQ files.

    Required parameters:
        wildcards: Snakemake wildcards object containing the sample name
        config: Snakemake config object containing genome size information
        input: Snakemake input object containing paths to FASTQ files
    
    Returns:
        String indicating SPAdes mode: "--isolate" for high coverage, or "--careful"
    """
    # Estimate total bases: Gzipped FASTQ is roughly 1 byte per base 
    # (conservative estimate including quality scores and headers)
    file_size_bytes = os.path.getsize(input.fq1) + os.path.getsize(input.fq2)
    estimated_coverage = file_size_bytes / config['genome_size']
    
    if estimated_coverage > 100:
        return "--isolate"
    else:
        return "--careful"

def get_assembly_path(wildcards, short_samples):
    """
    Resolve the assembly path based on the sample type (long or short).

    Required parameters:
        wildcards: Snakemake wildcards object containing the sample name
        short_samples: List of sample names that are short read samples
    """
    if wildcards.sample in short_samples:
        return f"results/assembly/short_assembly/{wildcards.sample}.fasta"
    else:
        return f"results/assembly/long_assembly/{wildcards.sample}.fasta"

def get_assembly_type(wildcards):
    """
    Return the assembly type (short or long) based on the sample.
    """
    if wildcards.sample in LONG_SAMPLES:
        return "long"
    else:
        return "short"

