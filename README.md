# PhageWeave

Pairwise genomic screening of candidate phage synergy, additivity, and interference.

The pipeline accepts two or more phage FASTA files, builds a pairwise feature matrix, adds Replidec replication-cycle evidence (virulent/temperate/chronic), and writes an auditable HTML report. Pharokka, DefenseFinder, PADLOC, DePP, and RaFAH are optional modules because their model/database assets are platform-dependent. A missing module is reported as unavailable and is never silently treated as a biological negative. Scores are a transparent screening baseline—not a validated experimental interaction model.

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
