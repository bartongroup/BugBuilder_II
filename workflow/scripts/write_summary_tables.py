#!/usr/bin/env python
"""
Write summary tables of RNA representation and assembly stats for multiqc report

Required arguments: None

"""
from pathlib import Path

from common.assembly_stats import get_all_quast_stats, \
    get_checkm2_stats, extract_RNA_seqs, assign_status

if __name__ == "__main__":

    quast_results = list(Path("results/quast").rglob("*/report.tsv"))
    checkm2_results = list(Path("results/checkm2").rglob("*/quality_report.tsv"))

    rna_stats    = extract_RNA_seqs('results/annotated')
    quast_stats  = get_all_quast_stats(quast_results) 
    checkm_stats = get_checkm2_stats(checkm2_results)

    rna_stats.to_csv("results/rna_representation_mqc.tsv", sep='\t', index_label='SAMPLE')
    all_stats = quast_stats.join([checkm_stats, rna_stats], how='outer')
    all_stats['Status'] = all_stats.apply(lambda row: assign_status(row), axis=1)

    all_stats.to_csv('results/assembly_stats.tsv', sep='\t', index_label='SAMPLE')