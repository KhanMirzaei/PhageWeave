# PhageWeave

Pairwise genomic screening of candidate phage synergy, additivity, and interference.

The pipeline accepts two or more phage FASTA files, builds a pairwise feature matrix, adds Replidec replication-cycle evidence (virulent/temperate/chronic), and writes an auditable HTML report. WIsH is the default host predictor when a directory of bacterial genomes is supplied; vHULK is retained as an opt-in legacy module. Pharokka-derived trait scanning covers depolymerases/capsule enzymes, receptor-binding/tail proteins, anti-defense keywords, lysis, and superinfection-exclusion/repressor signals. DefenseFinder and PADLOC screen supplied bacterial genomes for host anti-phage defense systems. DePP and AcrFinder are supported when installed. A missing module is reported as unavailable and is never silently treated as a biological negative. Scores are a transparent screening baseline—not a validated experimental interaction model.

```bash
bash install.sh
conda activate phageweave
./run_phageweave.sh --input examples --output results/demo
```

To enable replication-cycle evidence, install the dedicated environment once:

```bash
bash install_optional_tools.sh
```

Replidec downloads its reference database on first use. For a quick run while troubleshooting Pharokka, set `PHAGEWEAVE_SKIP_PHAROKKA=1`; otherwise Pharokka is attempted automatically when its database is configured.

To include bacterial defense systems, set `PHAGEWEAVE_BACTERIA_DIR` to a directory of bacterial FASTA/protein files before running. DefenseFinder and PADLOC results are written under `modules/bacterial_defense/` and linked in the report. Host defense systems are properties of bacterial genomes; they cannot be inferred reliably from phage FASTA alone.

vHULK uses a legacy TensorFlow build. On older Intel Macs whose CPUs lack AVX instructions, TensorFlow aborts during import even when installation succeeds; PhageWeave records vHULK as unavailable and uses WIsH when a bacterial reference directory is provided. Use a newer Linux host or Docker/remote compute for vHULK.

To enable WIsH, provide bacterial reference FASTA files (one genome per file). WIsH builds a Markov model for each supplied bacterial genome and reports log-likelihoods; it does not produce a calibrated probability unless null parameters are supplied.

```bash
export PHAGEWEAVE_WISH_HOST_DB=/path/to/bacterial_genomes
```

vHULK requires its legacy Python/TensorFlow stack and is attempted when the `phageweave-vhulk` environment is available. On macOS, Linux or Docker may be needed because the pinned TensorFlow release is not available for every platform. WIsH remains the lightweight fallback when bacterial references are provided.
