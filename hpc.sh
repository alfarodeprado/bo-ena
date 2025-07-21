#!/usr/bin/env bash

# Helper to run a selected BO pipeline on FU‑Berlin HPC.
# Usage: ./hpc.sh {biosamples|analysis|runs}

set -euo pipefail

# ------------------------------
# Script to run: biosamples, analysis, or runs
# ------------------------------
SCRIPT="${1:-}"  # pass one of: biosamples, analysis, runs

if [[ -z "$SCRIPT" ]]; then
  echo "Error: No script specified."
  echo "Usage: $0 {biosamples|analysis|runs}"
  exit 1
fi

# Load environment
module purge
module load Python/3.11.3-GCCcore-12.3.0

# 1) Set / refresh project environment WITHOUT spawning a sub‑shell
python set_env.py -s -H

# 2) Activate the environment created by set_env.py
source env/bin/activate

# Helper to run a given script
run_script() {
  local dir="$1"
  local script="$2"
  echo "--- Running ${dir}/${script} ---"
  ( cd "$dir" && python "$script" )
}

# Dispatch based on SCRIPT
case "$SCRIPT" in
  biosamples)
    run_script "biosamples" "biosamples.py"
    ;;
  analysis)
    run_script "analyses" "analysis.py"
    ;;
  runs)
    run_script "runs" "runs.py"
    ;;
  *)
    echo "Error: Unknown script '$SCRIPT'."
    echo "Usage: $0 {biosamples|analysis|runs}"
    exit 1
    ;;
esac

# Clean up
module purge

echo "'$SCRIPT' script  completed."
