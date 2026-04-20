# Rules for summarising results, including software versions and MultiQC report generation import pandas as pd
rule software_versions:
    input: f"{config['database_path']}/db_versions.json"
    output: 'results/software_mqc_versions.yaml'
    params: 
        database_path = config['database_path']
    log: 'workflow/logs/software_versions.log'
    container: containers['bugbuilder_ii']
    shell: """
    workflow/scripts/write_sw_versions.py \
        --input {input} \
        --output {output}
    """

rule summary_tables:
    input:
        quast = expand("results/quast/{sample}/report.tsv",sample=SAMPLES),
        busco = expand('results/busco/short_summary_{sample}.txt', sample=SAMPLES),
        checkm2 = expand("results/checkm2/{sample}/quality_report.tsv", sample=SAMPLES),
        bakta = expand('results/annotated/{sample}/{sample}.ffn', sample=SAMPLES)
    output: 
        rna_representation = 'results/rna_representation_mqc.tsv',
        assembly_stats = 'results/assembly_stats.tsv'
    log: 'workflow/logs/summary_tables.log'
    container: containers['bugbuilder_ii']
    shell: """
    export PYTHONPATH=workflow/scripts
    workflow/scripts/write_summary_tables.py \
        2>&1 > {log}
    """


rule multiqc:
    input:
        files = expand('results/trimmed_short_reads/{sample}_fastp.json', sample=SAMPLES) +
                expand('results/long_read_stats/{sample}_nanostat.txt', sample=LONG_SAMPLES) +
                FASTQC_OUTPUTS + KRAKEN_REPORTS + ANNOTS + GTDBTK + CHECKMS + BUSCOS + QUASTS + 
                ['results/software_mqc_versions.yaml', 'results/rna_representation_mqc.tsv'],
        config = 'etc/multiqc.conf'
    output:
        'workflow/reports/multiqc_report.html'
    container: containers["multiqc"]
    log: 'workflow/logs/multiqc.log'
    shell:
        """
        multiqc results \
                --config etc/multiqc.conf \
                --outdir workflow/reports/ \
                --filename multiqc_report.html \
                --force > {log} 2>&1
        """

rule manifest:
    input: 
        fastp = 'results/trimmed_short_reads/{sample}_fastp.json',
        quast = "results/quast/{sample}/report.tsv"
    output: "results/manifests/{sample}_manifest.tsv"
    params: 
        nanostat = "results/long_read_stats/{sample}_trimmed_nanostat.txt"
    log: 'workflow/logs/manifest_{sample}.log'
    container: containers["bugbuilder_ii"]
    shell: """
    export PYTHONPATH=workflow/scripts
    workflow/scripts/write_manifest.py \
        --sample {wildcards.sample} \
        2>&1 > {log}
    """