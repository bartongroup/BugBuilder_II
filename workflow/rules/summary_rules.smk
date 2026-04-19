# Rules for summarising results, including software versions and MultiQC report generation import pandas as pd
rule software_versions:
    input: f"{config['database_path']}/db_versions.json"
    output: 'results/software_mqc_versions.yaml'
    params: 
        database_path = config['database_path']
    log: 'workflow/logs/software_versions.log'
    run:
        with open(log[0], 'w') as log_file:
            json_file = f'{params.database_path}/db_versions.json'
            print(f"Collecting software versions from file: {json_file}", file=log_file)

            with open(f'{params.database_path}/db_versions.json') as f:
                db_versions = json.load(f)

            print("\nLoaded database versions:", file=log_file)
            for name, version in db_versions.items():
                print(f"  {name}: {version}", file=log_file)

            with open(output[0], 'w') as f:
                for name, container in containers.items():
                    version = container.split(':')[-1].split('--')[0]

                    db_version = None
                    db_type = None

                    if name in db_versions:
                        db_version = db_versions[name].get('version')
                        db_type = db_versions[name].get('type')

                    if db_type is not None and db_version is not None:
                        version += f" (database: {db_version} [{db_type}])"
                    elif db_version is not None:
                         version += f" (database: {db_version})"

                    f.write(f"{name}: '{version}'\n")

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
    run: 
        rna_stats    = extract_RNA_seqs('results/annotated', log)
        quast_stats  = get_all_quast_stats(input.quast, log) 
        checkm_stats = get_checkm2_stats(input.checkm2, log)

        rna_stats.to_csv(output.rna_representation, sep='\t', index_label='SAMPLE')
        all_stats = quast_stats.join([checkm_stats, rna_stats], how='outer')
        all_stats['Status'] = all_stats.apply(lambda row: assign_status(row), axis=1)

        all_stats.to_csv('results/assembly_stats.tsv', sep='\t', index_label='SAMPLE')


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
    run:
        short_bases = 0
        long_bases = 0
        program = 'SPAdes' 

        # Load quast report
        assembly_stats = get_quast_stats(input.quast, log)
        assembly_size = assembly_stats['assembly_size']
        
        fastp_stats = get_fastp_stats(input.fastp, log)
        short_bases = fastp_stats['total_bases']

        if wildcards.sample in LONG_SAMPLES:
            nanostat_stats = get_nanostat_stats(params.nanostat, log)
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
            sample_info = ena_df[ena_df['alias_samples'] == wildcards.sample]

            sample_id = sample_info['id_samples'].values[0] if not sample_info.empty else None
            run_id = ','.join(sample_info['id_runs'].values) if not sample_info.empty else None
        
        # Combine into manifest
        manifest_df = pd.DataFrame({
            'STUDY': [config['project_id']],
            'SAMPLE': sample_id,
            'ASSEMBLYNAME': [wildcards.sample],
            'ASSEMBLY_TYPE': 'isolate',
            'COVERAGE': coverage,
            'PROGRAM': program,
            'PLATFORM': config['short_read_instrument'] + (f", {config['long_read_instrument']}" \
                if long_bases > 0 else ""),
            'MOLECULE_TYPE': 'genomic DNA',
            'RUN_REF': run_id,
            'FLATFILE': f"{wildcards.sample}.embl.gz"
        })

        manifest_df = manifest_df.transpose()
        manifest_df.to_csv(output[0], sep='\t', index=True, header=False)