# Rules for post-assembly analyses, including annotation with bakta, blast
# database formatting, GTDB-Tk classification, CheckM2 quality assessment, and
# QUAST assembly quality assessment
print("short samples:", SHORT_SAMPLES)
rule bakta:
    input: 
        contigs = lambda wildcards: get_assembly_path(wildcards, SHORT_SAMPLES),
        db=AMRFINDER_DB # Ensure AMRFinder (and therefore bakta) database is available before running annotation...
    output:
        multiext("results/annotated/{sample}/{sample}",'.tsv','.gff3',
            '.gbff','.embl','.fna','.ffn','.faa','.hypotheticals.tsv','.txt','.json')
    container: containers["bakta"]
    log: 'workflow/logs/bakta_{sample}.log'
    params:
        database_path = config['database_path'],
        gram=config['gram']
    threads: 1 # overidden by profile config, but required...
    shell:"""
        bakta \
        --db {params.database_path}/bakta_db/ \
        --prefix {wildcards.sample} \
        --output results/annotated/{wildcards.sample} \
        --threads {threads} \
        --complete \
        --compliant \
        --locus-tag {wildcards.sample} \
        --gram {params.gram} \
        --force \
        {input.contigs} > {log} 2>&1
"""

rule blast_format:
    input: 
        genome="results/annotated/{sample}/{sample}.fna",
        protein="results/annotated/{sample}/{sample}.faa"
    output: 
        genome=multiext("results/blast_db/genome/{sample}",'','.ndb', '.nhr', '.nin', '.njs', '.not', '.nsq', '.ntf', '.nto'),
        protein=multiext("results/blast_db/protein/{sample}",'','.pdb', '.phr', '.pin', '.pjs', '.pot', '.psq', '.ptf', '.pto')
    container: containers["blast"]
    log: 'workflow/logs/blast_format_{sample}.log'
    shell: """
        cat {input.genome} |  sed -E 's/(contig_[0-9]*).*/{wildcards.sample}|\\1/' > \
            results/blast_db/genome/{wildcards.sample}
        cp {input.protein} results/blast_db/protein/{wildcards.sample}

        makeblastdb \
            -in results/blast_db/genome/{wildcards.sample} \
            -dbtype nucl \
            -out results/blast_db/genome/{wildcards.sample} \
            > {log} 2>&1

        makeblastdb \
            -in results/blast_db/protein/{wildcards.sample} \
            -dbtype prot \
            -out results/blast_db/protein/{wildcards.sample} \
            > {log} 2>&1
    """

rule combined_blast_db:
    input: BLAST_GENOMIC + BLAST_PROTEIN
    output:
        genome = "results/blast_db/assemblies.nal",
        protein = "results/blast_db/assemblies.pal"
    container: containers["blast"]
    log: 'workflow/logs/combined_blast_db.log'
    shell: """
    ls results/blast_db/genome|grep -v \\\\. | \
        sed 's|^|results/blast_db/genome/|' > $TMPDIR/genome_samples.txt

    ls  results/blast_db/protein|grep -v \\\\. | \
        sed 's|^|results/blast_db/protein/|' > $TMPDIR/protein_samples.txt

    blastdb_aliastool -dblist_file $TMPDIR/genome_samples.txt \
        -dbtype nucl \
        -title "Combined Genomic Assemblies" \
        -out results/blast_db/assemblies
        >> {log} 2>&1

    blastdb_aliastool -dblist_file $TMPDIR/protein_samples.txt \
        -dbtype prot \
        -title "Combined Protein Predictions" \
        -out results/blast_db/assemblies
        >> {log} 2>&1
    """


rule gtdbtk:
    input:
        assemblies = LONG_ASSEMBLIES + SHORT_ASSEMBLIES,
        database = GTDB
    output:
        "results/gtdbtk/gtdbtk.bac120.summary.tsv"
    params:
        database_path = config['database_path']
    container: containers["gtdbtk"]
    threads: 1 # overidden by profile config, but required...
    log: 'workflow/logs/gtdbtk.log'
    shell: """
export GTDBTK_DATA_PATH="{params.database_path}/gtdbtk"
echo "Running GTDB-Tk classification workflow with GTDBTK_DATA_PATH=$GTDBTK_DATA_PATH"
gtdbtk classify_wf \
        --genome_dir results/assembly \
        --out_dir results/gtdbtk/ \
        -x fasta \
        --cpus {threads} \
        --pplacer_cpus {threads} \
        --tmpdir $TMPDIR \
        --force \
        > {log} 2>&1
"""

rule busco:
    input: 
        assembly = lambda wildcards: get_assembly_path(wildcards, SHORT_SAMPLES),
        database = BUSCO_DB
    output: "results/busco/short_summary_{sample}.txt"
    params:
        database_path = config['database_path'] 
    container: containers["busco"]
    threads: 1 # overidden by profile config, but required...
    log: 'workflow/logs/busco_{sample}.log'
    shell: """
    cp -v {input.assembly} $TMPDIR/assembly.fasta 
    current_dir=$(pwd) 
    cd $TMPDIR
    busco -m genome \
        -c {threads} \
        --auto-lineage-prok \
        --download_path {params.database_path}/busco \
        --out_path $TMPDIR \
        -o {wildcards.sample} \
        -i assembly.fasta \
        -f >> $current_dir/{log} 2>&1
        result=$(ls -rt $TMPDIR/{wildcards.sample}/*.txt|tail -1)
        cp -v $result $current_dir/{output} >> $current_dir/{log} 2>&1
"""

rule checkm2: 
    input: 
        assembly = lambda wildcards: get_assembly_path(wildcards, SHORT_SAMPLES),
        database = CHECKM2_DB
    output: "results/checkm2/{sample}/quality_report.tsv"
    container: containers["checkm2"]
    threads: 1 # overidden by profile config, but required...
    log: 'workflow/logs/checkm2_{sample}.log'
    shell: """
    checkm2 predict \
        --input {input.assembly} \
        --output_dir results/checkm2/{wildcards.sample} \
        --database {input.database} \
        --threads {threads} \
        --force \
        --tmpdir $TMPDIR \
        > {log} 2>&1
"""

rule quast:
    input: 
        short_fq1 = 'results/trimmed_short_reads/{sample}_1.fastq.gz',
        short_fq2 = 'results/trimmed_short_reads/{sample}_2.fastq.gz',
        assembly = lambda wildcards: get_assembly_path(wildcards, SHORT_SAMPLES)
    output: "results/quast/{sample}/report.tsv"
    params:
        long_fq = 'results/trimmed_long_reads/{sample}.fastq.gz',
        genome_size = config['genome_size'] 
    container: containers["quast"]
    threads: 1 # overidden by profile config, but required...
    log: 'workflow/logs/quast_{sample}.log'
    shell: """
        mkdir $TMPDIR/reads
        cp {input.short_fq1} $TMPDIR/reads/{wildcards.sample}_1.fastq.gz
        cp {input.short_fq2} $TMPDIR/reads/{wildcards.sample}_2.fastq.gz

        job_args=""
        if [ -f {params.long_fq} ]; then
            cp -v {params.long_fq} $TMPDIR/reads/{wildcards.sample}.fastq.gz
            job_args="--nanopore $TMPDIR/reads/{wildcards.sample}.fastq.gz"
        fi

        quast \
        --pe1 $TMPDIR/reads/{wildcards.sample}_1.fastq.gz \
        --pe2 $TMPDIR/reads/{wildcards.sample}_2.fastq.gz \
        --features results/annotated/{wildcards.sample}/{wildcards.sample}.gff3 \
        $job_args \
        --est-ref-size {params.genome_size} \
        -l {wildcards.sample} \
        -o results/quast/{wildcards.sample} \
        --threads {threads} \
        --no-html \
        {input.assembly} > {log} 2>&1
"""