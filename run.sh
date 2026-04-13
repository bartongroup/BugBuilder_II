#!/bin/env bash

# Runs a Snakemake workflow to generate assemblies from raw data within data directory

# Some sanity checking...
# work out where we are running from, taking symlinks into account
run_dir=$(readlink -f "$0")
analysis_root=$(dirname ${run_dir}|sed 's/\/bin//')

# now work out where we are, taking symlinks into account
#'curr_dir=$(pwd|sed 's/\/analysis\/[A-Za-z0-9]*$//')
curr_dir=$(pwd)
real_base_dir=$(readlink -f $curr_dir)
if [[ ! -z "${real_base_dir}" ]]; then
	base_dir=${real_base_dir}
fi

# Are we in the right place?
if [[ "${base_dir}" != "${analysis_root}" ]]; then
	echo "This script should be run from the top-level directory of the project"
	exit 1
fi

# Set a permissive umask so that files created by Snakemake are group-writable,
# to help with sharing databases and apptainer caches
umask 002

# Firstly pull the apptainer images to make sure they download successfully
# allowing us to generate a sensible error message...
echo "Pulling required apptainer images..."

snakemake --use-apptainer --conda-create-envs-only --cores 1
if [[ $? -ne 0 ]]; then
	echo "Error pulling apptainer images. Please check your internet connection and try again."
	exit 1
fi

echo "\nRunning Snakemake workflow..."
snakemake --profile profile $@
