Pulling required apptainer images...
Loading sample variables...
\nRunning Snakemake workflow...
Loading sample variables...
---
title: DAG
---
flowchart TB
	id0[all]
	id1[bakta]
	id2[spades]
	id3[fastp]
	id4[amrfinder_download]
	id5[bakta_download]
	id6[unicycler]
	id7[chopper]
	id8[flye]
	id9[nanostat_trimmed]
	id10[combined_blast_db]
	id11[blast_format]
	id12[busco]
	id13[busco_download]
	id14[gtdbtk]
	id15[gtdb_download]
	id16[quast]
	id17[checkm2]
	id18[checkm2_download]
	id19[fastqc]
	id20[multiqc]
	id21[nanostat]
	id22[kraken]
	id23[kraken_db_download]
	id24[software_versions]
	id25[manifest]
	style id0 fill:#D95757,stroke-width:2px,color:#333333
	style id1 fill:#D97F57,stroke-width:2px,color:#333333
	style id2 fill:#577FD9,stroke-width:2px,color:#333333
	style id3 fill:#7FD957,stroke-width:2px,color:#333333
	style id4 fill:#D96B57,stroke-width:2px,color:#333333
	style id5 fill:#D99357,stroke-width:2px,color:#333333
	style id6 fill:#576BD9,stroke-width:2px,color:#333333
	style id7 fill:#A7D957,stroke-width:2px,color:#333333
	style id8 fill:#57D957,stroke-width:2px,color:#333333
	style id9 fill:#57BBD9,stroke-width:2px,color:#333333
	style id10 fill:#93D957,stroke-width:2px,color:#333333
	style id11 fill:#D9A757,stroke-width:2px,color:#333333
	style id12 fill:#D9BB57,stroke-width:2px,color:#333333
	style id13 fill:#D9CF57,stroke-width:2px,color:#333333
	style id14 fill:#57D97F,stroke-width:2px,color:#333333
	style id15 fill:#57D96B,stroke-width:2px,color:#333333
	style id16 fill:#57A7D9,stroke-width:2px,color:#333333
	style id17 fill:#CFD957,stroke-width:2px,color:#333333
	style id18 fill:#BBD957,stroke-width:2px,color:#333333
	style id19 fill:#6BD957,stroke-width:2px,color:#333333
	style id20 fill:#57D9CF,stroke-width:2px,color:#333333
	style id21 fill:#57CFD9,stroke-width:2px,color:#333333
	style id22 fill:#57D993,stroke-width:2px,color:#333333
	style id23 fill:#57D9A7,stroke-width:2px,color:#333333
	style id24 fill:#5793D9,stroke-width:2px,color:#333333
	style id25 fill:#57D9BB,stroke-width:2px,color:#333333
	id25 --> id0
	id14 --> id0
	id16 --> id0
	id17 --> id0
	id10 --> id0
	id1 --> id0
	id19 --> id0
	id20 --> id0
	id12 --> id0
	id6 --> id1
	id4 --> id1
	id2 --> id1
	id3 --> id2
	id5 --> id4
	id8 --> id6
	id7 --> id6
	id3 --> id6
	id9 --> id8
	id7 --> id8
	id7 --> id9
	id11 --> id10
	id1 --> id11
	id6 --> id12
	id13 --> id12
	id2 --> id12
	id6 --> id14
	id2 --> id14
	id15 --> id14
	id2 --> id16
	id3 --> id16
	id1 --> id16
	id6 --> id16
	id12 --> id16
	id6 --> id17
	id2 --> id17
	id18 --> id17
	id14 --> id20
	id22 --> id20
	id3 --> id20
	id17 --> id20
	id16 --> id20
	id1 --> id20
	id19 --> id20
	id24 --> id20
	id12 --> id20
	id21 --> id20
	id23 --> id22
	id3 --> id22
	id16 --> id25
	id3 --> id25
