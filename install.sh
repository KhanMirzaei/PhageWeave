#!/usr/bin/env bash
set -euo pipefail
ENV_NAME="${PHAGEWEAVE_ENV:-phageweave}"
command -v conda >/dev/null || { echo 'Install Miniforge/Conda first.'; exit 1; }
if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda create -y -n "$ENV_NAME" -c conda-forge snakemake python=3.11
fi
echo "Installed $ENV_NAME. Activate with: conda activate $ENV_NAME"
