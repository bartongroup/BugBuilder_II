# BugBuilder II

This workflow is intended to carry out either a short read, or hybrid assembly
(combining long and short reads) of a number of microbial genomes, using a range
of well known software tools. Appropriate assembly tools will be selected
automatically based upon the read types available for each sample. It is
implemented using Snakemake, and aims to provide a 'hands-free' processes from
raw reads through to submission-ready annotated, classified genome assemblies,
optionally generating MANIFEST files required for ENA submission. 

The workflow is also created with reprodicibility in mind, using defined
versions of software provided via Docker, while clearly reporting all versions
of software used, which should be cited in any publications utilising it's
outputs.

The software requires a number of databases, which will be automatically downloaded as required. Note that these will require ~650 Gb disk space. 

TODO: Use centralised database and docker cache directories to ease reuse

## Quick start guide for those familiar with git and conda

Note that the configuration is currently configured to use a GridEngine based compute cluster with DRMAA. Changes will probably be required to support other environments, which will need to be made in the Snakemake `profile/config.yaml`.

1. Clone this repository and change into the resulting directory

2. Create a conda environment: `conda create -f etc/conda.yaml`

3. Activate the environment: `conda activate BugBuilder_II`

4. Setup your data. Create a `data` subdirectory, within which a directory for each sample (named with the sample name) should be created. Sequence reads should be placed in directories within these per-sample directories named 'short_reads' and (optionally) 'long_reads', as illustrated below.

```
data
├── NRS2102
│   └── short_reads
│       ├── NRS2102_1.fastq.gz
│       └── NRS2102_2.fastq.gz
├── NRS2103
│   ├── long_reads
│   │   └── NRS2103.fastq.gz
│   └── short_reads
│       ├── NRS2103_1.fastq.gz
│       └── NRS2103_2.fastq.gz
```

5. Tweak the configuration: See workflow configuration below

6. Run the workflow: `bin/run_workflow.sh`

## Installation - the long version

A separate copy of the workflow should be created for each analysis to be
conducted. A small conda environment is required containing the core workflow
management components, which is reusable across different copies of the
workflow.

The workflow has been implemented on Linux, and may work ok on MacOS, but is
untested. YMMV...

1. **Software Prerequisites**: Ensure you have conda and git available. If you don't have conda, head [here](https://docs.conda.io/en/latest/) to obtain the appropriate downoader for your platform, and follow it's installation instructions. You probably want the mambaforge installer rather than miniforge, which has commercial licensing implications

2. **Clone this repository**: Select a directory name to save this to, and clone the repository with `git clone https://github.com/bartongroup/BugBuilder_II.git my_workflow_dir`

3. **Change into the checkout directory**: `cd my_workflow_dir`

4. **Create the conda environment** This is a one-time operation which creates the environment containing the necessary workflow software: `conda env create -f etc/conda.yaml`

### Workflow Directory Structure and Configuration

The workflow follows old-fashion Unix conventions for directory naming. The only script needing running directly is the `bin/run_workflow.sh` script, which starts the process going, once setup and configured. 
```
.
├── bin
│   ├── download_busco_lineages.py
│   ├── download_gtdbtk_db.py
│   ├── download_krakendb.py
│   └── run_workflow.sh
├── etc
│   ├── conda.yaml
│   └── multiqc.conf
├── log
├── profile
│   └── config.yaml
├── README.md
├── rulegraph.svg
└── workflow
    ├── config
    │   └── config.template
    └── Snakefile
```

Minimal files are likely to require editing. The `profile/config.yaml` may need adjusting to match your compute environment. Each workflow run requires a `workflow/config/config.yaml` to be created based upon the provided `config.template` file. See below for details.

## Usage

1. **Activate the environment** This will make the software in the installed environment available: `conda activate BugBuilder_II

2. **Setup sequence read directory** Create a `data` subdirectory, within which a directory for each sample (named with the sample name) should be created. Sequence reads should be placed in directories within these per-sample directories named 'short_reads' and (optionally) 'long_reads', as illustrated below.

```
data
├── NRS2102
│   └── short_reads
│       ├── NRS2102_1.fastq.gz
│       └── NRS2102_2.fastq.gz
├── NRS2103
│   ├── long_reads
│   │   └── NRS2103.fastq.gz
│   └── short_reads
│       ├── NRS2103_1.fastq.gz
│       └── NRS2103_2.fastq.gz
```
3. **Register with ENA** To ensure the workflow outputs can be submitted to ENA with minimal additional work, pre-register your study and samples with the ENA, and upload your sequence reads. Ensuring you register a locus_tag for each sample - We normally use the isolate name as the locus tag, which is the approach taken by the workflow. So far we haven't had any problems with name conflicts with the locus tags. 

4. **Create a config.yaml file for the run**. Copy `workflows/config/config.template` to `workflows/config/config.template` and edit to set the required parameters:

    * project_id: The project identifier issued by ENA i.e. PRJNAXXXXX
    *   short_read_instrument: Type of instrument used for short-read sequencing i.e. Illumina MiSeq
    * long_read_instrument: Type of instrument used for long-read sequencing i.e. Oxford Nanopore GridION
    * genome_size: Estimated average size of genomes in bp. This is required by some assemblers
    * gram: '+' for gram positive organisms, or '-' for gram negative. This is used by the bakta annotation software to better target gene annotations to the type of bacteria.
    * gtdb_version: Version of GTDB database to use (default: 226)
    * kraken_db_version: Version of Kraken standard database to use (default: 20260226)

5. **Manifest files** (optional): If you would like to automatically generate manifest files for use in submitting assemblies to ENA, once you have your read data submitted (stage 3 above), navigate your browser to the Webin [runs report](https://www.ebi.ac.uk/ena/submit/webin/report/runs;defaultSearch=true) page and click the `Download all results` link. Repeat this for the [samples report](https://www.ebi.ac.uk/ena/submit/webin/report/samples;defaultSearch=true), and ensure the files are named `runs.csv` and `samples.csv`, and place them in the `workflow/config` directory. These will be used when populating data in the manifest files.

5. **Run the workflow**. Run `bin/run_workflow.sh` to start the workflow running. It will hopefully run to completion without any problems. Note that database downloads can take a considerable time.


## Workflow Outputs

The key outputs o
N.B. GTDB-TK v2.6.1 has a bug which causes it to fail if rerun when the output directory exists, so will need the output directory removing if a rerun is required. The bug is fixed in github, and awaiting a release