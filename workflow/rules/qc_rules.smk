# Rules for quality control of raw sequencing data, including FastQC, fastp,
# chopper, NanoStat, and Kraken2 (for contamination identification)

rule fastqc:
    input:
        fq1 = 'data/{sample}/short_reads/{sample}_1.fastq.gz',
        fq2 = 'data/{sample}/short_reads/{sample}_2.fastq.gz'
    output:
        fq1 = 'results/fastqc/{sample}_1_fastqc.zip',
        fq2 = 'results/fastqc/{sample}_2_fastqc.zip'
    container: containers["fastqc"]
    log: 'workflow/logs/fastqc_{sample}.log'
    shell: """
        fastqc \
            -o results/fastqc/ \
            {input.fq1} \
            {input.fq2} \
        > {log} 2>&1
    """

rule fastp:
    input:
        fq1 = 'data/{sample}/short_reads/{sample}_1.fastq.gz',
        fq2 = 'data/{sample}/short_reads/{sample}_2.fastq.gz'
    output:
        fq1 = 'results/trimmed_short_reads/{sample}_1.fastq.gz',
        fq2 = 'results/trimmed_short_reads/{sample}_2.fastq.gz',
        json = 'results/trimmed_short_reads/{sample}_fastp.json'
    container: containers["fastp"]
    threads: 1 # overidden by profile config, but required...
    log: 'workflow/logs/fastp_{sample}.log'
    shell: """
        fastp \
            -i {input.fq1} \
            -I {input.fq2} \
            -o {output.fq1} \
            -O {output.fq2} \
            --json {output.json} \
            --html /dev/null \
            --thread {threads} \
            --disable_quality_filtering \
            --disable_length_filtering \
        > {log} 2>&1
    """

rule chopper:
    input:
        long_reads = 'data/{sample}/long_reads/{sample}.fastq.gz'
    output:
        filtered_reads = 'results/trimmed_long_reads/{sample}.fastq.gz'
    container: containers["chopper"]
    threads: 1 # overidden by profile config, but required...
    params:
        min_qual = 10,   # Minimum average Phred score
        min_len = 1000   # Minimum read length (bp)
    log: 'workflow/logs/chopper_{sample}.log'
    shell:
        """
        gunzip -c {input.long_reads} | \
        chopper -t {threads} -q {params.min_qual} -l {params.min_len} | \
        gzip > {output.filtered_reads} 2> {log}
        """

rule nanostat:
    input: 'data/{sample}/long_reads/{sample}.fastq.gz'
    output: 'results/long_read_stats/{sample}_nanostat.txt'
    container: containers["nanostat"]
    log: 'workflow/logs/nanostat_{sample}.log'
    threads: 1 # overidden by profile config, but required...
    shell: """
        NanoStat \
            --fastq {input} \
            --name {output} \
            --threads {threads} \
            --tsv \
        > {log} 2>&1
    """

rule nanostat_trimmed:
    input: 'results/trimmed_long_reads/{sample}.fastq.gz'
    output: 'results/long_read_stats/{sample}_trimmed_nanostat.txt'
    container: containers["nanostat"]
    log: 'workflow/logs/nanostat_{sample}.log'
    threads: 1 # overidden by profile config, but required...
    shell: """
        NanoStat \
            --fastq {input} \
            --name {output} \
            --threads {threads} \
            --tsv \
        > {log} 2>&1
    """

rule kraken:
    input: 
        r1 = 'results/trimmed_short_reads/{sample}_1.fastq.gz', 
        r2 = 'results/trimmed_short_reads/{sample}_2.fastq.gz',
        db = KRAKEN_DB
    output: 
        output = 'results/kraken2/{sample}_kraken_output.txt',
        report = 'results/kraken2/{sample}_kraken_report.txt'
    params:
        db_path = f"{config['database_path']}/kraken2"
    container: containers["kraken2"]
    log: 'workflow/logs/kraken2_{sample}.log'
    threads: 1 # overidden by profile config, but required...
    shell: """
    exec > {log} 2>&1
    echo "Running Kraken2 for sample {wildcards.sample} with database {params.db_path}"
    k2 classify \
        --db {params.db_path} \
        --threads {threads} \
        --memory-mapping \
        --use-names \
        --output {output.output} \
        --report {output.report} \
        --paired \
        {input.r1} {input.r2}
    """

