################################################################################
#
# Sample and database configuration
#
################################################################################

# Each sample should be in a subdirectory of 'data/' named with the sample id,
# and containing 'short_reads/' and/or 'long_reads/' subdirectories with the
# appropriate FASTQ files.

# Filenaming should start with the sample id, and end with '_1.fastq.gz' and
# '_2.fastq.gz' for short reads, and '{sample}.fastq.gz' for long reads.

print("Loading sample variables...")
global SHORT_SAMPLES, LONG_SAMPLES, SAMPLES

SAMPLES = glob('data/*')
SAMPLES = [os.path.basename(x) for x in SAMPLES]
LONG_SAMPLES = []
SHORT_SAMPLES = []

for sample in SAMPLES:
    if os.path.exists(f"data/{sample}/long_reads"):
        LONG_SAMPLES.append(sample)
    else:
        SHORT_SAMPLES.append(sample)
