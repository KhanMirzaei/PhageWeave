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
if [[ "${PHAGEWEAVE_ENABLE_VHULK:-0}" == "1" ]] && ! conda env list | awk '{print $1}' | grep -qx phageweave-vhulk; then
  log 'Installing vHULK host-prediction environment (legacy Python/TensorFlow stack)'
  # TensorFlow 2.8.2 is absent from some macOS Conda channels. Create the
  # scientific-tool environment with Conda, then install the matching Intel
  # macOS wheel with pip as a fallback.
  if ! conda create -y -n phageweave-vhulk -c conda-forge -c bioconda python=3.10 prokka hmmer 'numpy<2' pandas scipy biopython pip tensorflow=2.8.2; then
    log 'Conda TensorFlow package unavailable; retrying with the pip wheel.'
    conda env remove -y -n phageweave-vhulk >/dev/null 2>&1 || true
    conda create -y -n phageweave-vhulk -c conda-forge -c bioconda python=3.10 prokka hmmer 'numpy<2' pandas scipy biopython pip || log 'vHULK base environment failed.'
    conda run -n phageweave-vhulk python -m pip install 'tensorflow==2.8.2' || log 'TensorFlow 2.8.2 could not be installed; use Linux/Docker.'
  fi
fi
if [[ "${PHAGEWEAVE_ENABLE_VHULK:-0}" != "1" ]]; then
  log 'vHULK disabled by default; WIsH is the host-prediction method.'
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
if ! conda env list | awk '{print $1}' | grep -qx phageweave-padloc; then
  log 'Installing PADLOC environment'
  conda create -y -n phageweave-padloc -c conda-forge -c bioconda padloc || log 'PADLOC installation failed; retry later.'
fi
if ! conda env list | awk '{print $1}' | grep -qx phageweave-depp; then
  log 'Installing DePP depolymerase predictor environment'
  conda create -y -n phageweave-depp -c conda-forge python=3.10 'biopython<1.80' 'numpy<2' pandas scikit-learn || log 'DePP installation failed; retry later.'
fi
if [[ ! -d "$TOOLS/DePP" ]]; then
  log 'Fetching DePP source and model files'
  git clone --depth 1 https://github.com/DamianJM/Depolymerase-Predictor.git "$TOOLS/DePP" || log 'DePP download failed.'
fi
log 'Installation attempt complete. Check workflow reports/module_status.json for available modules.'
