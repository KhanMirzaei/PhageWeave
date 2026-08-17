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
if ! conda env list | awk '{print $1}' | grep -qx phageweave-vhulk; then
  log 'Installing vHULK host-prediction environment (legacy Python/TensorFlow stack)'
  conda create -y -n phageweave-vhulk -c conda-forge -c bioconda python=3.7 prokka hmmer numpy pandas scipy biopython tensorflow=2.8.2 || log 'vHULK environment installation failed; use Linux/Docker if TensorFlow is unavailable on macOS.'
fi
if [[ ! -d "$TOOLS/vHULK" ]]; then
  log 'Fetching vHULK models and script'
  git clone --depth 1 https://github.com/LaboratorioBioinformatica/vHULK.git "$TOOLS/vHULK" || log 'vHULK download failed.'
fi
if [[ ! -d "$TOOLS/WIsH" ]]; then
  log 'Fetching WIsH source'
  git clone --depth 1 https://github.com/soedinglab/WIsH.git "$TOOLS/WIsH" || log 'WIsH download failed.'
fi
if [[ -d "$TOOLS/WIsH" && ! -x "$TOOLS/WIsH/WIsH" ]]; then
  (cd "$TOOLS/WIsH" && cmake . && make -j2) || log 'WIsH compilation failed; install a C++11/OpenMP compiler and retry.'
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
if [[ ! -d "$TOOLS/DePP" ]]; then
  log 'Fetching DePP source and model files'
  git clone --depth 1 https://github.com/DamianJM/Depolymerase-Predictor.git "$TOOLS/DePP" || log 'DePP download failed.'
fi
log 'Installation attempt complete. Check workflow reports/module_status.json for available modules.'
