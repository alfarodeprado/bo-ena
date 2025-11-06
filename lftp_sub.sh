#!/usr/bin/env bash

set -euo pipefail

###############################################################################
# CONFIG — EDIT THIS BLOCK ONLY
###############################################################################

# A) Credentials
# Option 1 (recommended): file with 1st line=user, 2nd line=password.
CREDENTIALS_FILE="path/to/credentials"

# A) Option 2: set here. Leave WEBIN_PASSWORD empty to input it when calling the script ($lftp_sub.sh 1234).
WEBIN_USER="Webin-XXXXX"
WEBIN_PASSWORD=""

# B) Remote target (default live). For test portal, use "webin-cli-test/lftp".
REMOTE_BASE_DIR="webin-cli/lftp"

# Optional subfolder inside REMOTE_BASE_DIR (e.g., "2025-11-06_batch1"); "" = none
BATCH_SUBDIR=""

# C) Helper TSV (remote_path \t md5). If empty, auto-place next to first input.
OUT_TSV="logs/md5s_NAME_HERE.tsv"

# D) Files/dirs to include (dirs scanned recursively for known read extensions).
INPUTS=(
  # "/path/to/R1.fastq"
  # "/path/to/R2.fastq"
  # "/path/to/library.bam"
  # "/path/to/dir/with/files"
)

# Ask for a Y/N confirmation before uploading
ASK_CONFIRM_BEFORE_UPLOAD=true

# pigz threads; gzip fallback is single-threaded
GZIP_THREADS=2

# Directory scan extensions (case-insensitive)
INCLUDE_EXTS=("fastq" "fq" "fasta" "fa" "gz" "bam" "cram" "sff" "fast5")

###############################################################################
# END CONFIG
###############################################################################

have() { command -v "$1" >/dev/null 2>&1; }
lower() { tr 'A-Z' 'a-z'; }

# Compress only when needed; PRINT ONLY the final path; logs → STDERR
compress_if_needed() {
  local f="$1"
  case "${f,,}" in
    *.fastq|*.fq|*.fasta|*.fa)
      if [[ -f "${f}.gz" ]]; then
        echo "[info] Already have ${f}.gz; will upload the .gz" >&2
        printf '%s\n' "${f}.gz"
      else
        echo "[info] Compressing (keep original) $f -> ${f}.gz" >&2
        if have pigz; then pigz -k -n -p "${GZIP_THREADS}" "$f"
        else gzip -k -n "$f"
        fi
        printf '%s\n' "${f}.gz"
      fi
      ;;
    *.fastq.gz|*.fq.gz|*.fasta.gz|*.fa.gz|*.bam|*.cram|*.sff|*.fast5|*.fast5.gz)
      printf '%s\n' "$f"
      ;;
    *)
      echo "[warn] Unrecognized extension for $f; uploading as-is." >&2
      printf '%s\n' "$f"
      ;;
  esac
}

# Create X.md5 with ONLY the 32 hex chars (lowercase). PRINT the .md5 path.
write_md5_file() {
  local f="$1"
  local md5file="${f}.md5"
  local sum=""
  if have md5sum; then
    sum="$(md5sum "$f" | awk '{print $1}' | lower)"
  elif have md5; then
    sum="$(md5 -q "$f" | lower)"
  else
    echo "ERROR: need md5sum (Linux) or md5 (macOS) in PATH" >&2; exit 3
  fi
  printf '%s\n' "$sum" > "$md5file"
  printf '%s\n' "$md5file"
}

scan_inputs() {
  declare -a found=()
  if (( ${#INPUTS[@]} == 0 )); then
    echo "ERROR: No INPUTS set in CONFIG." >&2; exit 2
  fi
  for inpath in "${INPUTS[@]}"; do
    if [[ -d "$inpath" ]]; then
      local expr=()
      for ext in "${INCLUDE_EXTS[@]}"; do expr+=( -iname "*.${ext}" -o ); done
      unset 'expr[${#expr[@]}-1]'
      while IFS= read -r -d '' f; do found+=("$f"); done \
        < <(find "$inpath" -type f \( "${expr[@]}" \) -print0)
    else
      [[ -f "$inpath" ]] && found+=("$inpath") || echo "[warn] Missing: $inpath" >&2
    fi
  done
  (( ${#found[@]} )) || { echo "ERROR: No files found." >&2; exit 2; }
  printf '%s\n' "${found[@]}"
}

load_credentials() {
  if [[ -n "$CREDENTIALS_FILE" ]]; then
    [[ -f "$CREDENTIALS_FILE" ]] || { echo "ERROR: CREDENTIALS_FILE not found: $CREDENTIALS_FILE" >&2; exit 2; }
    WEBIN_USER="$(sed -n '1p' "$CREDENTIALS_FILE" | tr -d '\r\n')"
    WEBIN_PASSWORD="$(sed -n '2p' "$CREDENTIALS_FILE" | tr -d '\r\n')"
  fi
  [[ -n "${WEBIN_USER:-}" ]] || { echo "ERROR: WEBIN_USER is empty." >&2; exit 2; }
}

main() {
  load_credentials

  local remote_dir="$REMOTE_BASE_DIR"
  [[ -n "$BATCH_SUBDIR" ]] && remote_dir="${remote_dir%/}/$BATCH_SUBDIR"

  mapfile -t to_process < <(scan_inputs)

  # Default helper TSV next to first input if not set
  if [[ -z "$OUT_TSV" ]]; then
    OUT_TSV="$(dirname "${to_process[0]}")/ena_uploaded_md5s.tsv"
  fi

  declare -a final_files=()
  declare -a summary_rows=()
  for f in "${to_process[@]}"; do
    data="$(compress_if_needed "$f")"     # -> prints ONLY final path
    md5p="$(write_md5_file "$data")"      # -> .md5 path
    final_files+=("$data" "$md5p")
    md5=$(tr -d ' \t\r\n' < "$md5p" | lower)
    remotepath="${remote_dir%/}/$(basename "$data")"
    summary_rows+=("$remotepath"$'\t'"$md5")
  done

  echo
  echo "================ UPLOAD SUMMARY ================"
  echo "Webin user:     $WEBIN_USER"
  echo "Remote target:  $remote_dir  (on webin2.ebi.ac.uk)"
  echo "Files to send:  ${#final_files[@]} (data + .md5)"
  echo "Helper TSV ->   $OUT_TSV"
  echo "================================================"
  echo

  if [[ "$ASK_CONFIRM_BEFORE_UPLOAD" == "true" ]]; then
    read -rp "Proceed with upload? [y/N] " ans
    [[ "${ans,,}" == "y" || "${ans,,}" == "yes" ]] || { echo "Aborted."; exit 0; }
  fi

  # Write helper TSV
  : > "$OUT_TSV"
  for row in "${summary_rows[@]}"; do printf "%s\n" "$row" >> "$OUT_TSV"; done

  # Build lftp script (include the OPEN here; we call lftp -f only)
  local LFTP_SCRIPT; LFTP_SCRIPT="$(mktemp)"; trap 'rm -f "$LFTP_SCRIPT"' EXIT
  {
    echo "set ftp:ssl-force true"
    echo "set ftp:ssl-protect-data true"
    echo "set net:max-retries 2"
    echo "set net:reconnect-interval-base 5"
    echo "set net:reconnect-interval-max 60"
    echo "set cmd:fail-exit yes"
    if [[ -n "${WEBIN_PASSWORD:-}" ]]; then
      printf 'open -u %q,%q %s\n' "$WEBIN_USER" "$WEBIN_PASSWORD" "webin2.ebi.ac.uk"
    else
      printf 'open -u %q %s\n' "$WEBIN_USER" "webin2.ebi.ac.uk"
    fi
    printf 'mkdir -p %q\n' "$remote_dir"
    printf 'cd %q\n' "$remote_dir"
    echo "pwd"
    echo -n "mput -c -O ."
    for f in "${final_files[@]}"; do printf ' %q' "$f"; done
    echo
    echo "bye"
  } > "$LFTP_SCRIPT"

  # IMPORTANT: use -f alone (host is handled by the 'open' inside the script)
  lftp -f "$LFTP_SCRIPT"

  echo
  echo "[ok] Upload complete to: $remote_dir"
  echo "[ok] Helper TSV written: $OUT_TSV"
  echo
  echo "Manual step: Webin Portal → Submit Reads → download template →"
  echo "fill file names EXACTLY as uploaded (e.g. ${remote_dir}/your.fastq.gz) + md5 → submit TSV."
}

main "$@"
