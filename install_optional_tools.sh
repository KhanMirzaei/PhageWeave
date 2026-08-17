#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
TOOLS="$ROOT/tools"
mkdir -p "$TOOLS"
log(){ echo "[PhageWeave] $*"; }
command -v conda >/dev/null || { echo 'Conda/Miniforge is required.' >&2; exit 1; }
if ! conda env list | awk '{print $1}' | grep -qx phageweave-replidec; then
  log 'Installing Replidec replication-cycle predictor'
  conda create --solver libmamba -y -n phageweave-replidec -c conda-forge -c bioconda replidec mmseqs2 hmmer blast || log 'Replidec installation failed; retry later.'
fi
PHAROKKA_ENV="${PHAGEWEAVE_PHAROKKA_ENV:-phageweave-pharokka}"
PHAROKKA_DB="${PHAGEWEAVE_PHAROKKA_DB:-$ROOT/databases/pharokka}"
if ! conda env list | awk '{print $1}' | grep -qx "$PHAROKKA_ENV"; then
  log "Installing Pharokka in $PHAROKKA_ENV"
  conda create --solver libmamba -y -n "$PHAROKKA_ENV" -c conda-forge -c bioconda pharokka || log 'Pharokka installation failed; retry later.'
fi
if conda env list | awk '{print $1}' | grep -qx "$PHAROKKA_ENV"; then
  # Pharokka's dependency checker expects a `phanotate` executable, while
  # recent Conda packages expose `phanotate.py`.  Add a project-local shim so
  # fresh installs work without modifying the Conda environment.
  mkdir -p "$ROOT/tools/phageweave_bin"
  PHAROKKA_PREFIX="$(conda info --base)/envs/$PHAROKKA_ENV"
  cat > "$ROOT/tools/phageweave_bin/dnaapler" <<EOF
#!/bin/sh
exec "$ROOT/tools/phageweave_bin/dnaapler.real" "\$@" 2>/dev/null
EOF
  cat > "$ROOT/tools/phageweave_bin/dnaapler.real" <<EOF
#!/bin/sh
exec "$PHAROKKA_PREFIX/bin/dnaapler" "\$@"
EOF
  cat > "$ROOT/tools/phageweave_bin/phanotate" <<EOF
#!/bin/sh
exec "$PHAROKKA_PREFIX/bin/phanotate.py" "\$@"
EOF
  chmod +x "$ROOT/tools/phageweave_bin/phanotate"
  mkdir -p "$PHAROKKA_DB"
  if [[ ! -f "$PHAROKKA_DB/.phageweave_ready" ]]; then
    log "Downloading Pharokka databases into $PHAROKKA_DB"
    if conda run --no-capture-output -n "$PHAROKKA_ENV" pharokka install -o "$PHAROKKA_DB"; then
      touch "$PHAROKKA_DB/.phageweave_ready"
    elif conda run --no-capture-output -n "$PHAROKKA_ENV" install_databases.py -o "$PHAROKKA_DB"; then
      touch "$PHAROKKA_DB/.phageweave_ready"
    else
      log 'Pharokka database download failed; rerun install_optional_tools.sh later.'
    fi
  fi
fi
if [[ "${PHAGEWEAVE_ENABLE_VHULK:-0}" == "1" ]] && ! conda env list | awk '{print $1}' | grep -qx phageweave-vhulk; then
  log 'Installing vHULK host-prediction environment (legacy Python/TensorFlow stack)'
  # TensorFlow 2.8.2 is absent from some macOS Conda channels. Create the
  # scientific-tool environment with Conda, then install the matching Intel
  # macOS wheel with pip as a fallback.
  if ! conda create --solver libmamba -y -n phageweave-vhulk -c conda-forge -c bioconda python=3.10 prokka hmmer 'numpy<2' pandas scipy biopython pip tensorflow=2.8.2; then
    log 'Conda TensorFlow package unavailable; retrying with the pip wheel.'
    conda env remove -y -n phageweave-vhulk >/dev/null 2>&1 || true
    conda create --solver libmamba -y -n phageweave-vhulk -c conda-forge -c bioconda python=3.10 prokka hmmer 'numpy<2' pandas scipy biopython pip || log 'vHULK base environment failed.'
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
  CORE_ENV="${PHAGEWEAVE_ENV:-phageweave}"
  (cd "$TOOLS/WIsH" && conda run --no-capture-output -n "$CORE_ENV" cmake . && make -j2) || log 'WIsH compilation failed; install a C++11/OpenMP compiler and retry.'
fi
if ! conda env list | awk '{print $1}' | grep -qx phageweave-padloc; then
  log 'Installing PADLOC environment'
  conda create --solver libmamba -y -n phageweave-padloc -c conda-forge -c bioconda padloc || log 'PADLOC installation failed; retry later.'
fi
if ! conda env list | awk '{print $1}' | grep -qx phageweave-depp; then
  log 'Installing DePP depolymerase predictor environment'
  conda create --solver libmamba -y -n phageweave-depp -c conda-forge python=3.10 'biopython<1.80' 'numpy<2' pandas scikit-learn || log 'DePP installation failed; retry later.'
fi
if [[ ! -d "$TOOLS/DePP" ]]; then
  log 'Fetching DePP source and model files'
  git clone --depth 1 https://github.com/DamianJM/Depolymerase-Predictor.git "$TOOLS/DePP" || log 'DePP download failed.'
fi
log 'Installation attempt complete.'
log "Core: ${PHAGEWEAVE_ENV:-phageweave}"
log "Pharokka: $PHAROKKA_ENV (database: $PHAROKKA_DB)"
log 'WIsH requires PHAGEWEAVE_WISH_HOST_DB pointing to bacterial FASTA files.'
