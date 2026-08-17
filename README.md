# PhageWeave

Pairwise genomic screening of candidate phage synergy, additivity, and interference.

The current baseline accepts two or more phage FASTA files, builds a pairwise feature matrix, scores mechanistic hypotheses, and writes an HTML report. Pharokka, DefenseFinder, PADLOC, DePP, RaFAH, Foldseek, MMseqs2, XGBoost, and SHAP will be added as optional evidence modules; baseline outputs must not be interpreted as experimental interaction evidence.

```bash
bash install.sh
conda activate phageweave
./run_phageweave.sh --input examples --output results/demo
```
