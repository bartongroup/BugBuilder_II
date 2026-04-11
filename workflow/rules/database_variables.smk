# Variables for database file paths, used to both define outputs of download
# rules, and in rules that require database files as input

BAKTA_DB_PATH = f"{config['database_path']}/bakta_db"

# Bakta database consists of multiple files with different extensions depending on the type of data
BAKTA_DB_MAP = {
    "hmmer": (["antifam", "pfam"], [".h3f", ".h3i", ".h3m", ".h3p"]),
    "infernal": (["ncRNA-genes", "ncRNA-regions", "rRNA"], [".i1i", ".i1f", ".i1m", ".i1p"]),
    "singletons": [
        "bakta.db", "expert-protein-sequences.dmnd", "sorf.dmnd", 
        "oric.fna", "orit.fna", "rfam-go.tsv", "version.json"
    ]
}

BAKTA_DB = (
    [f"{BAKTA_DB_PATH}/{p}{ext}" for p, exts in [BAKTA_DB_MAP["hmmer"], BAKTA_DB_MAP["infernal"]] for p in p for ext in exts] +
    [f"{BAKTA_DB_PATH}/{f}" for f in BAKTA_DB_MAP["singletons"]]
)

AMRFINDER_DB_MAP = {
    "hmmer": (["AMR.LIB"], [".h3f", ".h3i", ".h3m", ".h3p"]),
    "blast": (["AMRProt.fa"], [".pdb", ".phr", ".pin", ".pjs", ".pot", ".psq", ".ptf", ".pto"]),
    "singletons": [
        "AMRProt-mutation.tsv","AMRProt-suppress.tsv","AMRProt-susceptible.tsv",
        "database_format_version.txt", "fam.tsv", "taxgroup.tsv"
    ]
}

AMRFINDER_DB = (
    [f"{BAKTA_DB_PATH}/amrfinderplus-db/latest/{p}{ext}" 
        for p, exts in [AMRFINDER_DB_MAP["hmmer"], AMRFINDER_DB_MAP["blast"]] for p in p for ext in exts] +
    [f"{BAKTA_DB_PATH}/amrfinderplus-db/latest/{f}" for f in AMRFINDER_DB_MAP["singletons"]]
)

# Kraken2 database files...
KRAKEN_DB_MAP=  { "kmers": [50,75,100,150,200,250,300],
                  "k2d": ["hash", "opts", "taxo" ],
                  "dmp": ["names", "nodes"],
                  "txt": ["inspect", "unmapped_accessions"],
                  "tsv": ["ktaxonomy", "library_report"] } 

KRAKEN_DB_PATH = f"{config['database_path']}/kraken2"
KRAKEN_DB = ( [f"{KRAKEN_DB_PATH}/database{kmers}mers.kmer_distrib" for kmers in KRAKEN_DB_MAP["kmers"]] +
              [f"{KRAKEN_DB_PATH}/{k2d}.k2d" for k2d in ["hash", "opts", "taxo"]] +
              [f"{KRAKEN_DB_PATH}/{dmp}.dmp" for dmp in KRAKEN_DB_MAP["dmp"]] +
              [f"{KRAKEN_DB_PATH}/{txt}.txt" for txt in KRAKEN_DB_MAP["txt"]] +
              [f"{KRAKEN_DB_PATH}/{tsv}.tsv" for tsv in KRAKEN_DB_MAP["tsv"]] +
              [f"{KRAKEN_DB_PATH}/seqid2taxid.map"] )

BUSCO_DB   = f"{config['database_path']}/busco/download.complete"
CHECKM2_DB = f"{config['database_path']}/checkm2_db/uniref100.KO.1.dmnd"

# Way too many files in GTDB to list them all, so just one as a target
GTDB = [f"{config['database_path']}/gtdbtk/taxonomy/gtdb_taxonomy.tsv"]