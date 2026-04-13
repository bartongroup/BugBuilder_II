# Rules for carrying out database downloads requried for various tools

rule kraken_db_download:
    input: 'workflow/scripts/download_krakendb.py'
    output: KRAKEN_DB
    params:
        database_path = config['database_path'],
        kraken_db_version = config['kraken_db_version'],
        kraken_db_type = config['kraken_db_type']
    log: 'workflow/logs/kraken_db_download.log'
    shell:"""
export PYTHONPATH=workflow/scripts
workflow/scripts/download_krakendb.py \
    --database_dir {params.database_path} \
    --database_version {params.kraken_db_version} \
    --database_type {params.kraken_db_type} > {log} 2>&1
"""

rule bakta_download:
    input: 'workflow/scripts/download_bakta_db.py'
    output: BAKTA_DB
    params:
        database_path    = config['database_path'],
        database_version = config['bakta_db_version'],
        database_type    = config['bakta_db_type']
    log: 'workflow/logs/bakta_db_download.log'
    shell:"""
export PYTHONPATH=workflow/scripts
workflow/scripts/download_bakta_db.py \
    --database_dir     {params.database_path} \
    --database_version {params.database_version} \
    --database_type    {params.database_type} > {log} 2>&1
"""

rule amrfinder_download:
    input: BAKTA_DB
    output: AMRFINDER_DB
    params:
        database_path = config['database_path']
    log: 'workflow/logs/amrfinder_db_download.log'
    container: containers["bakta"]
    shell:"""
    exec > {log} 2>&1
    amrfinder_update --database {params.database_path}/bakta_db/amrfinderplus-db/ 
    echo "exit status: $?" 
"""

rule gtdb_download:
    input: 'workflow/scripts/download_gtdbtk_db.py'
    output: GTDB
    params:
        database_path = config['database_path'],
        gtdb_version = config['gtdb_version']
    log: 'workflow/logs/gtdb_download.log'
    shell: """
    export PYTHONPATH=workflow/scripts
    workflow/scripts/download_gtdbtk_db.py \
        --database_dir {params.database_path} \
        --database_version {params.gtdb_version} \
    > {log} 2>&1
"""

rule busco_download:
    input: 'workflow/scripts/download_busco_lineages.py'
    output: BUSCO_DB
    params:
        database_path = config['database_path'],
        database_version = config['busco_dataset']
    log: 'workflow/logs/busco_download.log'
    shell: """
    export PYTHONPATH=workflow/scripts
    workflow/scripts/download_busco_lineages.py \
        --database_dir {params.database_path} \
        --database_version {params.database_version} \
  > {log} 2>&1
touch {output}
"""

rule checkm2_download:
    input: 'workflow/scripts/download_checkm2_db.py'
    output: CHECKM2_DB
    params:
        database_path = config['database_path'],
        database_version = config['checkm2_db_version']
    log: 'workflow/logs/checkm2_download.log'
    shell: """
    export PYTHONPATH=workflow/scripts
    workflow/scripts/download_checkm2_db.py \
        --database_dir {params.database_path} \
        --database_version {params.database_version} \
    > {log} 2>&1
"""