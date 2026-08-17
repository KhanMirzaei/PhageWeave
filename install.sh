#!/usr/bin/env bash
set -euo pipefail
ENV_NAME="${PHAGEWEAVE_ENV:-phageweave}"
command -v conda >/dev/null || { echo 'Install Miniforge/Conda first.'; exit 1; }
if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda create -y -n "$ENV_NAME" -c conda-forge -c bioconda \
    snakemake python=3.11 pandas biopython scikit-learn matplotlib networkx hmmer blast mmseqs2
fi
echo "Installed $ENV_NAME. Activate with: conda activate $ENV_NAME"
if [[ "${PHAGEWEAVE_SKIP_OPTIONAL:-0}" != "1" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  bash "$SCRIPT_DIR/install_optional_tools.sh" || echo "Optional modules were not all installable on this platform; see the log above."
fi
