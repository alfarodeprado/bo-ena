#!/usr/bin/env bash

# Simple helper to run selected BO pipeline sections on FU‑Berlin HPC.
# Toggle RUN_* flags below.

set -euo pipefail

# ------------------------------
# Flags: set to true/false as needed
# ------------------------------
RUN_BIOSAMPLES=true   # biosamples/biosamples.py
RUN_ANALYSES=false     # analyses/analysis.py
RUN_RUNS=false         # runs/runs.py
# ------------------------------

module purge
module load Python/3.11.3-GCCcore-12.3.0

# 1) Set / refresh project environment WITHOUT spawning a sub‑shell
python set_env.py -s -H

# 2) Activate the environment created by set_env.py
source env/bin/activate

run_section() {
  local dir="$1"
  local script="$2"
  echo "--- Running ${dir}/${script} ---"
  ( cd "$dir" && python "$script" )
}

[ "$RUN_BIOSAMPLES" = true ] && run_section "biosamples" "biosamples.py"
[ "$RUN_ANALYSES"   = true ] && run_section "analysis"  "analysis.py"
[ "$RUN_RUNS"       = true ] && run_section "runs"      "runs.py"

module purge

echo "All selected sections completed."
