# Downloadable libraries
import pandas as pd

# Standard libraries
import os
import sys
import argparse
import gzip
import subprocess
import shutil
import glob
from collections import defaultdict
import yaml

def load_config(cfg_path: str = "config.yaml") -> dict:
    """
    Return a dict with the YAML content or an empty dict if the file is absent.
    """
    if os.path.exists(cfg_path):
        with open(cfg_path, "r") as fh:
            return yaml.safe_load(fh) or {}
    return {}

def convert_manifests(excel_file, submission_dir="submission"):
    # Load Excel
    df = pd.read_excel(excel_file, sheet_name=0)
    df.columns = df.columns.str.strip()
    sample_counts = defaultdict(int) # 

    # Required columns for raw reads submission
    required = [
        "STUDY", "SAMPLE", "NAME", "INSTRUMENT", "INSERT_SIZE",
        "LIBRARY_NAME", "LIBRARY_SOURCE", "LIBRARY_SELECTION", "LIBRARY_STRATEGY",
        "DESCRIPTION"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        sys.exit(f"Missing columns in Excel: {', '.join(missing)}")

    # Identify file columns (BAM, CRAM, FASTQ, including duplicates like FASTQ1)
    file_cols = [c for c in df.columns if c.upper() in ("BAM", "CRAM") or c.upper().startswith("FASTQ")]
    if not file_cols:
        sys.exit("No file columns (BAM, CRAM, FASTQ) found in Excel header")

    os.makedirs(submission_dir, exist_ok=True)
    manifest_paths = []

    for idx, row in df.iterrows():
        n = idx + 1
        #sample_id = str(row["SAMPLE"]).strip()
        # In case there are more than one objects associated with the same sample.
        raw_id = str(row["SAMPLE"]).strip()
        sample_counts[raw_id] += 1
        # first occurrence → use raw_id; subsequent → raw_id_2, raw_id_3, ...
        if sample_counts[raw_id] == 1:
            sample_id = raw_id
        else:
            sample_id = f"{raw_id}_{sample_counts[raw_id]}"
        samp_dir = os.path.join(submission_dir, sample_id)
        os.makedirs(samp_dir, exist_ok=True)

        # Collect file entries
        entries = []
        for col in file_cols:
            val = row.get(col)
            if pd.notnull(val) and str(val).strip().lower() != "nan":
                entries.append((col, str(val).strip()))
        if not entries:
            sys.exit(f"Row {n}: no files specified in any of {', '.join(file_cols)}")


        # Determine file type in case of paired reads, or more than one type, based on paths' extensions
        types = set()
        for _, rel in entries:
            low = rel.lower()
            if low.endswith(".bam") or low.endswith(".bam.gz"):
                types.add("BAM")
            elif low.endswith(".cram") or low.endswith(".cram.gz"):
                types.add("CRAM")
            elif low.endswith(".fastq") or low.endswith(".fq") \
                or low.endswith(".fastq.gz") or low.endswith(".fq.gz"):
                types.add("FASTQ")
            else:
                sys.exit(f"Row {n}: unrecognized file extension in '{rel}'")
        if len(types) != 1:
            sys.exit(f"Row {n}: mixed file types in one row: {types}")
        filetype = types.pop()



        # Validate counts
        if filetype in ("BAM", "CRAM") and len(entries) != 1:
            sys.exit(f"Row {n}: {filetype} requires exactly one file entry, got {len(entries)}")
        if filetype == "FASTQ" and len(entries) < 1:
            sys.exit(f"Row {n}: at least one FASTQ entry required")
        
        # Handling of files, check for compression too
        compressed_files = []
        # Handle each file: copy into samp_dir, compress if needed
        for _, rel in entries:
            src = os.path.abspath(rel)
            if not os.path.exists(src):
                sys.exit(f"Row {n}: file not found: {src}")
            # if file is already in samp_dir, just add to manifest
            if os.path.dirname(src) == os.path.abspath(samp_dir):
                compressed_files.append(os.path.basename(src))
                continue
            # if already .gz then hard-link into samp_dir
            if src.endswith(".gz"):
                link_path = os.path.join(samp_dir, os.path.basename(src))
                try:
                    os.link(src, link_path)        # hard-link
                except OSError:
                        raise
                compressed_files.append(os.path.basename(link_path))
                continue

            # if not .gz then stream-compress right into samp_dir
            gz_name = os.path.basename(src) + ".gz"
            dst = os.path.join(samp_dir, gz_name)

            with open(src, "rb") as f_in, gzip.open(dst, "wb", compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out, length=1024 * 1024)  # 1 MiB chunks

            compressed_files.append(gz_name)


        # Write manifest.txt
        mf = os.path.join(samp_dir, "manifest.txt")
        with open(mf, "w") as fh:
            fh.write(f"STUDY\t{row['STUDY']}\n")
            fh.write(f"SAMPLE\t{row['SAMPLE']}\n")
            fh.write(f"NAME\t{row['NAME']}\n")
            fh.write(f"INSTRUMENT\t{row['INSTRUMENT']}\n")
            fh.write(f"INSERT_SIZE\t{row['INSERT_SIZE']}\n")
            fh.write(f"LIBRARY_NAME\t{row['LIBRARY_NAME']}\n")
            fh.write(f"LIBRARY_SOURCE\t{row['LIBRARY_SOURCE']}\n")
            fh.write(f"LIBRARY_SELECTION\t{row['LIBRARY_SELECTION']}\n")
            fh.write(f"LIBRARY_STRATEGY\t{row['LIBRARY_STRATEGY']}\n")
            fh.write(f"DESCRIPTION\t{row['DESCRIPTION']}\n")
            for fn in compressed_files:
                fh.write(f"{filetype}\t{fn}\n")
        print(f"[Row {n}] Wrote manifest → {mf}")
        manifest_paths.append(mf)

    return manifest_paths


def prepare_logs_dir(logs_dir="logs"):
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def load_credentials(path):
    if not os.path.isfile(path):
        sys.exit(f"Credentials file not found: {path}")
    lines = [l.strip() for l in open(path) if l.strip()]
    if len(lines) < 2:
        sys.exit(f"{path} must have username on line 1 and password on line 2")
    return lines[0], lines[1]


def find_jar(jar_arg):
    if jar_arg:
        if os.path.isfile(jar_arg):
            return jar_arg
        sys.exit(f"JAR not found at {jar_arg}")
    webin = [m for m in glob.glob("*.jar") if "webin-cli" in m]
    if len(webin) == 1:
        return webin[0]
    sys.exit("Auto-detect failed; pass --jar /path/to/webin-cli.jar")


def submit_manifests(manifests, jar, user, pwd, live, logs_dir):
    for mf in manifests:
        inp = os.path.dirname(mf)
        sample_id = os.path.basename(inp)
        log_subdir = os.path.join(logs_dir, sample_id)
        os.makedirs(log_subdir, exist_ok=True)
        cmd = [
            "java", "-jar", jar,
            "-context", "reads",
            "-manifest", mf,
            "-inputDir", inp,
            "-outputDir", log_subdir,
            "-submit",
            "-username", user,
            "-password", pwd
        ]
        if not live:
            cmd.insert(cmd.index("-submit"), "-test")
        #print(f"→ Running: {' '.join(cmd)}")

        # redact user and password in the printed command
        safe_cmd = [
            ("******" if c in (user, pwd) else c)       # replace secrets
            for c in cmd
        ]
        print(f"→ Running: {' '.join(safe_cmd)}")

        res = subprocess.run(cmd, capture_output=True, text=True)
        print(f"  Return code: {res.returncode}")
        if res.stdout:
            print(res.stdout)
        if res.stderr:
            print(res.stderr, file=sys.stderr)
    
    # remove compressed files?


def main():
    p = argparse.ArgumentParser(
        description="reads.py → per‐sample raw‐reads submission folders + Webin-CLI")
    
    p.add_argument(
        "--config", default="config.yaml",
        help="Path to YAML config file (default: config.yaml)")
    
    p.add_argument(
        "-c", "--convert", metavar="EXCEL",
        help="Convert EXCEL to per‐sample submission/<SAMPLE>/…")
    
    p.add_argument(
        "-s", "--submit", action="store_true",
        help="Submit all submission/*/manifest.txt via Webin-CLI")
    
    p.add_argument(
        "--submission_dir", default="submission",
        help="Top‐level folder for per‐sample subdirs (default=submission/)")
    
    p.add_argument(
        "-j", "--jar", help="Path to webin-cli JAR (auto‐detect if omitted)")
    
    p.add_argument(
        "--cred_file", default="credentials.txt",
        help="File with username (line1) and password (line2)")
    
    p.add_argument(
        "--live", action="store_true",
        help="Use real submission (omit -test). Default=test")
    
    p.add_argument(
        "--logs_dir", default="logs",
        help="Where Webin-CLI writes its receipts")
    
    args = p.parse_args()

    # pull YAML config
    cfg = load_config(args.config)

    # 1. Excel file to convert
    excel_path = args.convert or cfg.get("excel_runs")
    # 2. credentials file
    cred_path  = args.cred_file or cfg.get("credentials", "credentials.txt")
    # 3. JAR path
    jar_path   = args.jar or cfg.get("jar")
    # 4. live flag
    live = args.live or cfg.get("live", False)

    manifests = []
    if excel_path:
        manifests = convert_manifests(excel_path, args.submission_dir)

    if args.submit:
        user, pwd = load_credentials(cred_path)
        jar = find_jar(jar_path)
        logs = prepare_logs_dir(args.logs_dir)
        if not manifests: #discover
            manifests = sorted(
                glob.glob(os.path.join(args.submission_dir, "*", "manifest.txt"))
            )
            if not manifests:
                sys.exit("No manifests found; run with -c your.xlsx first.")
        submit_manifests(manifests, jar, user, pwd, live, logs)

    if not args.convert and not args.submit:
        p.print_help()


if __name__ == "__main__":
    main()
