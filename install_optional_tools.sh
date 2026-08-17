#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
TOOLS="$ROOT/tools"
mkdir -p "$TOOLS"
log(){ echo "[PhageWeave] $*"; }
command -v conda >/dev/null || { echo 'Conda/Miniforge is required.' >&2; exit 1; }
if ! conda env list | awk '{print $1}' | grep -qx phageweave-replidec; then
  log 'Installing Replidec replication-cycle predictor'
  conda create -y -n phageweave-replidec -c conda-forge -c bioconda replidec mmseqs2 hmmer blast || log 'Replidec installation failed; retry later.'
fi
if ! conda env list | awk '{print $1}' | grep -qx phageweave-defense; then
  log 'Installing DefenseFinder environment'
  conda create -y -n phageweave-defense -c conda-forge -c bioconda python=3.12 hmmer mdmparis-defense-finder || log 'DefenseFinder installation failed; retry later.'
fi
if conda env list | awk '{print $1}' | grep -qx phageweave-defense; then
  conda run -n phageweave-defense defense-finder update || log 'DefenseFinder models were not downloaded.'
fi
if ! conda env list | awk '{print $1}' | grep -qx phageweave-padloc; then
  log 'Installing PADLOC environment'
  conda create -y -n phageweave-padloc -c conda-forge -c bioconda padloc || log 'PADLOC installation failed; retry later.'
fi
if [[ ! -d "$TOOLS/RaFAH" ]]; then
  log 'Fetching RaFAH scripts and model files'
  git clone --depth 1 https://github.com/felipehcoutinho/RaFAH.git "$TOOLS/RaFAH" || log 'RaFAH download failed.'
fi
if [[ -f "$TOOLS/RaFAH/RaFAH.pl" ]]; then
  (cd "$TOOLS/RaFAH" && perl RaFAH.pl --fetch) || log 'RaFAH model fetch failed; install R/ranger and retry.'
fi
if [[ ! -d "$TOOLS/DePP" ]]; then
  log 'Fetching DePP source and model files'
  git clone --depth 1 https://github.com/DamianJM/Depolymerase-Predictor.git "$TOOLS/DePP" || log 'DePP download failed.'
fi
log 'Installation attempt complete. Check workflow reports/module_status.json for available modules.'
