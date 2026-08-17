#!/usr/bin/env bash
set -euo pipefail
INPUT=examples
OUTPUT=results
CORES=${SNAKEMAKE_CORES:-2}
OPEN=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --input) INPUT="$2"; shift 2;;
    --output) OUTPUT="$2"; shift 2;;
    --cores) CORES="$2"; shift 2;;
    --no-open) OPEN=0; shift;;
    *) echo "Unknown option: $1" >&2; exit 2;;
  esac
done
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --config input_dir="$INPUT" output_dir="$OUTPUT" --cores "$CORES"
echo "Report: $OUTPUT/report/index.html"
if [[ "$OPEN" == 1 ]] && command -v open >/dev/null; then open "$OUTPUT/report/index.html"; fi
