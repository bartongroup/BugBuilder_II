# Rules for assembly of short and long read data, using SPAdes, Flye, and Unicycler

rule spades:
    input:
        fq1 = 'results/trimmed_short_reads/{sample}_1.fastq.gz',
        fq2 = 'results/trimmed_short_reads/{sample}_2.fastq.gz'
    output: 
        contigs = "results/assembly/short_assembly/{sample}.fasta",
        gfa = "results/assembly/short_assembly/{sample}.gfa"
    container: containers["spades"]
    log: 'workflow/logs/spades_{sample}.log'
    threads: 1 # overidden by profile config, but required...
    resources:
        mem_mb = 1 # overidden by profile config, but required...
    params:
        mode = lambda wildcards, input: get_spades_mode(wildcards, config, input)
    shell: """
        exec > {log} 2>&1
        cp -v {input.fq1} $TMPDIR/{wildcards.sample}_1.fastq.gz
        cp -v {input.fq2} $TMPDIR/{wildcards.sample}_2.fastq.gz
        spades.py \
            -1 $TMPDIR/{wildcards.sample}_1.fastq.gz \
            -2 $TMPDIR/{wildcards.sample}_2.fastq.gz \
            {params.mode} \
            -t {threads} \
            -m {resources.mem_mb} \
            -o $TMPDIR/spades_output
        cp -v $TMPDIR/spades_output/contigs.fasta {output.contigs}
        cp -v $TMPDIR/spades_output/assembly_graph_with_scaffolds.gfa {output.gfa}
        ln -sfv short_assembly/{wildcards.sample}.fasta results/assembly/{wildcards.sample}.fasta 
    """

rule flye:
    input: 
        fastq="results/trimmed_long_reads/{sample}.fastq.gz",
        stats="results/long_read_stats/{sample}_trimmed_nanostat.txt" 
    output: 
        assembly = "results/flye/{sample}.fasta",
        gfa = "results/flye/{sample}.gfa",
        info = "results/flye/{sample}_assembly_info.txt"
    container: containers["flye"]
    log: 'workflow/logs/flye_{sample}.log'
    threads: 1 # overidden by profile config, but required...
    resources:
        mem_mb = 1 # overidden by profile config, but required...
    params:
        genome_size = config['genome_size']
    shell: """
        exec > {log} 2>&1
        cp -v {input.fastq} $TMPDIR 
        flye \
            --nano-hq $TMPDIR/{wildcards.sample}.fastq.gz \
            --out-dir $TMPDIR/flye \
            --genome-size {params.genome_size} \
            --asm-coverage 50 \
            --threads {threads}
        cp -v $TMPDIR/flye/assembly.fasta {output.assembly}
        cp -v $TMPDIR/flye/assembly_graph.gfa {output.gfa}
        cp -v $TMPDIR/flye/assembly_info.txt {output.info}
    """

rule unicycler:
    input: 
        short_fq1 = 'results/trimmed_short_reads/{sample}_1.fastq.gz',
        short_fq2 = 'results/trimmed_short_reads/{sample}_2.fastq.gz',
        long_fq = 'results/trimmed_long_reads/{sample}.fastq.gz',
        flye_contigs = 'results/flye/{sample}.fasta'
    output: 
        contigs = "results/assembly/long_assembly/{sample}.fasta",
            gfa = "results/assembly/long_assembly/{sample}.gfa" 
    container: containers["unicycler"]
    log: 'workflow/logs/unicycler_{sample}.log'
    threads: 1 # overidden by profile config, but required...
    resources:
        mem_mb = 1 # overidden by profile config, but required... 
    shell:"""
        exec > {log} 2>&1
        echo "Running Unicycler for sample {wildcards.sample}"
        echo "Short reads: {input.short_fq1} and {input.short_fq2}"
        echo "Long reads: {input.long_fq}" 
        echo "Flye assembly: {input.flye_contigs}"
        mkdir $TMPDIR/reads 
        cp -v {input.short_fq1} $TMPDIR/reads/{wildcards.sample}_1.fastq.gz 
        cp -v {input.short_fq2} $TMPDIR/reads/{wildcards.sample}_2.fastq.gz 
        cp -v {input.long_fq} $TMPDIR/reads/{wildcards.sample}.fastq.gz 
        cp -v {input.flye_contigs} $TMPDIR/reads/flye.fasta 
        unicycler \
            -1 $TMPDIR/reads/{wildcards.sample}_1.fastq.gz \
            -2 $TMPDIR/reads/{wildcards.sample}_2.fastq.gz \
            -l $TMPDIR/reads/{wildcards.sample}.fastq.gz \
            --existing_long_read_assembly $TMPDIR/reads/flye.fasta \
            -t {threads} \
            --mode bold \
            -o $TMPDIR/output 
        cp -v $TMPDIR/output/assembly.fasta {output.contigs} 
        cp -v $TMPDIR/output/assembly.gfa {output.gfa}
        ln -sfv long_assembly/{wildcards.sample}.fasta results/assembly/{wildcards.sample}.fasta
    """
