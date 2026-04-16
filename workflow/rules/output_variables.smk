# Variables defining output files for rules

NANO_TRIMMED = expand("results/long_read_stats/{sample}_trimmed_nanostat.txt", sample=LONG_SAMPLES)

SHORT_ASSEMBLIES = expand("results/assembly/short_assembly/{sample}.fasta",sample=SHORT_SAMPLES)
LONG_ASSEMBLIES = expand("results/assembly/long_assembly/{sample}.fasta",sample=LONG_SAMPLES)

KRAKEN_REPORTS = expand("results/kraken2/{sample}_kraken_report.txt", sample=SAMPLES)

ANNOT_EXTS = ['.tsv', '.gff3', '.gbff', '.embl', '.fna', 
              '.ffn', '.faa', '.hypotheticals.tsv', '.txt', '.json']
ANNOTS = expand(
    "results/annotated/{sample}/{sample}{ext}", 
    sample=SAMPLES, 
    ext=ANNOT_EXTS
)

BLAST_GENOMIC_SUFFIXES = ['','.ndb', '.nhr', '.nin', '.njs', '.not', '.nsq', '.ntf', '.nto']
BLAST_PROTEIN_SUFFIXES = ['','.pdb', '.phr', '.pin', '.pjs', '.pot', '.psq', '.ptf', '.pto']

BLAST_GENOMIC = expand("results/blast_db/genome/{sample}{suffix}", 
    sample=SAMPLES, suffix=BLAST_GENOMIC_SUFFIXES)
BLAST_PROTEIN = expand("results/blast_db/protein/{sample}{suffix}", 
    sample=SAMPLES, suffix=BLAST_PROTEIN_SUFFIXES)

BLAST_ALIAS_DBS = [
    "results/blast_db/assemblies.nal",
    "results/blast_db/assemblies.pal"
]

FASTQC_OUTPUTS = expand("results/fastqc/{sample}_{read}_fastqc.zip",
    sample=SAMPLES,
    read=[1,2]
)
BUSCOS  = expand("results/busco/short_summary_{sample}.txt", sample=SAMPLES)
CHECKMS = expand("results/checkm2/{sample}/quality_report.tsv", sample=SAMPLES)
GTDBTK  = ['results/gtdbtk/gtdbtk.bac120.summary.tsv']
QUASTS  = expand("results/quast/{sample}/report.tsv",sample=SAMPLES)
MULTIQC_REPORT = ['workflow/reports/multiqc_report.html']

MANIFESTS = expand("results/manifests/{sample}_manifest.tsv", sample=SAMPLES)
RNA_REPR = ['results/rna_representation_mqc.tsv']

OUTPUTS = ANNOTS + BLAST_ALIAS_DBS + BUSCOS + GTDBTK + QUASTS + \
    CHECKMS + FASTQC_OUTPUTS + MULTIQC_REPORT + RNA_REPR + MANIFESTS