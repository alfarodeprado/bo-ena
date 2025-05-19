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


def compress_file(path, remove_original=True):
    """Compress `path` → `path.gz`.  
       If remove_original, delete the uncompressed file."""
    gz_path = path + ".gz"
    with open(path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
        f_out.writelines(f_in)
    if remove_original:
        os.remove(path)
    return os.path.basename(gz_path)

def extract_first_accession(analysis_path):
    """Return first AC accession from an EMBL flatfile or sequence name from a FASTA file."""
    # open gzipped or plain text
    if analysis_path.lower().endswith(".gz"):
        open_f, mode = gzip.open, "rt"
    else:
        open_f, mode = open, "r"
    with open_f(analysis_path, mode) as f:
        for line in f:
            if line.startswith("AC"):
                return line[2:].strip().split()[0].rstrip(";")
            if line.startswith(">"):
                return line[1:].strip().split()[0]
    sys.exit(f"Error: no accession line ('AC' or '>') found in {analysis_path}")


def convert_manifests(excel_file, submission_dir="submission"):
    # Load Excel
    df = pd.read_excel(excel_file, sheet_name=0)
    df.columns = df.columns.str.strip()
    required = [
        "STUDY","SAMPLE","RUN_REF","ASSEMBLYNAME","ASSEMBLY_TYPE",
        "COVERAGE","PROGRAM","PLATFORM","MOLECULETYPE",
        "DESCRIPTION","FLATFILE","FASTA"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        sys.exit(f"Missing columns in Excel: {', '.join(missing)}")

    os.makedirs(submission_dir, exist_ok=True)
    manifest_paths = []

    for idx, row in df.iterrows():
        n = idx + 1
        sample_id = str(row["SAMPLE"]).strip()
        samp_dir = os.path.join(submission_dir, sample_id)
        os.makedirs(samp_dir, exist_ok=True)

        flat = str(row["FLATFILE"]).strip()
        fasta = str(row["FASTA"]).strip()
        has_flat = flat and flat.lower() != "nan"
        has_fasta = fasta and fasta.lower() != "nan"
        if has_flat == has_fasta:
            sys.exit(f"Row {n}: exactly one of FLATFILE or FASTA must be set")

        # Prepare FLATFILE handling
        if has_flat:
            rel = flat
            path_in = os.path.abspath(rel)
            ext = os.path.splitext(path_in)[1].lower()

            if ext == ".gb":
                # Lazy‐import Biopython only if needed
                try:
                    from Bio import SeqIO
                except ImportError:
                    sys.exit(
                        "Error: converting .gb → .embl requires Biopython;\n"
                        " please install biopython or supply an .embl flatfile."
                    )
                stem = os.path.splitext(os.path.basename(rel))[0]
                embl_path = os.path.join(samp_dir, stem + ".embl")
                recs = SeqIO.parse(path_in, "genbank")
                count = SeqIO.write(recs, embl_path, "embl")
                if count == 0:
                    sys.exit(f"Row {n}: no records written converting {path_in}")
                print(f"[Row {n}] Converted {path_in} → {embl_path} ({count} recs)")
                acc = extract_first_accession(embl_path)
                embl_gz = compress_file(embl_path, remove_original=False)
                data_field = ("FLATFILE", embl_gz)

            elif ext == ".embl":
                # Copy-in the existing EMBL
                embl_src = path_in
                embl_dst = os.path.join(samp_dir, os.path.basename(rel))
                if embl_src != embl_dst:
                    shutil.copy(embl_src, embl_dst)
                acc = extract_first_accession(embl_dst)
                embl_gz = compress_file(embl_dst, remove_original=False)
                data_field = ("FLATFILE", embl_gz)

            else:
                sys.exit(f"Row {n}: FLATFILE must end in .gb or .embl, not '{ext}'")
        
        else:
            # FASTA-only: extract accession from the first '>' header line
            rel = fasta
            path_in = os.path.abspath(rel)
            fasta_src = path_in
            fasta_dst = os.path.join(samp_dir, os.path.basename(rel))
            if fasta_src != fasta_dst:
                shutil.copy(fasta_src, fasta_dst)
            acc = extract_first_accession(fasta_dst)
            fasta_gz = compress_file(fasta_dst, remove_original=False)
            data_field = ("FASTA", fasta_gz)


        # Create chr_list.txt(.gz)
        chr_txt = os.path.join(samp_dir, "chr_list.txt")
        with open(chr_txt, "w") as f:
            f.write(f"{acc} 1 Circular-Chromosome Plastid")
        chr_gz = compress_file(chr_txt, remove_original=False)

        # Write manifest.txt
        mf = os.path.join(samp_dir, "manifest.txt")
        with open(mf, "w") as fh:
            fh.write(f"STUDY\t{row['STUDY']}\n")
            fh.write(f"SAMPLE\t{row['SAMPLE']}\n")
            fh.write(f"RUN_REF\t{row['RUN_REF']}\n")
            fh.write(f"ASSEMBLYNAME\t{row['ASSEMBLYNAME']}\n")
            fh.write(f"ASSEMBLY_TYPE\t{row['ASSEMBLY_TYPE']}\n")
            fh.write(f"COVERAGE\t{row['COVERAGE']}\n")
            fh.write(f"PROGRAM\t{row['PROGRAM']}\n")
            fh.write(f"PLATFORM\t{row['PLATFORM']}\n")
            fh.write(f"MOLECULETYPE\t{row['MOLECULETYPE']}\n")
            if pd.notnull(row["DESCRIPTION"]) and str(row["DESCRIPTION"]).strip().lower() != "nan":
                fh.write(f"DESCRIPTION\t{row['DESCRIPTION']}\n")
            fh.write(f"{data_field[0]}\t{data_field[1]}\n")
            fh.write(f"CHROMOSOME_LIST\t{chr_gz}\n")
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
        cmd = [
            "java", "-jar", jar,
            "-context", "genome",
            "-manifest", mf,
            "-inputDir", inp,
            "-outputDir", logs_dir,
            "-submit",
            "-username", user,
            "-password", pwd
        ]
        if not live:
            cmd.insert(cmd.index("-submit"), "-test")
        print(f"→ Running: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True)
        print(f"  Return code: {res.returncode}")
        if res.stdout:
            print(res.stdout)
        if res.stderr:
            print(res.stderr, file=sys.stderr)

def main():
    p = argparse.ArgumentParser(
        description="analysis.py → per‐sample submission folders + Webin-CLI"
    )
    p.add_argument(
        "-c", "--convert", metavar="EXCEL",
        help="Convert EXCEL to per‐sample submission/<SAMPLE>/…"
    )
    p.add_argument(
        "-s", "--submit", action="store_true",
        help="Submit all submission/*/manifest.txt via Webin-CLI"
    )
    p.add_argument(
        "--submission_dir", default="submission",
        help="Top‐level folder for per‐sample subdirs (default=submission/)"
    )
    p.add_argument(
        "-j", "--jar", help="Path to webin-cli JAR (auto‐detect if omitted)"
    )
    p.add_argument(
        "--cred_file", default="credentials.txt",
        help="File with username (line1) and password (line2)"
    )
    p.add_argument(
        "--live", action="store_true",
        help="Use real submission (omit -test). Default=test"
    )
    p.add_argument(
        "--logs_dir", default="logs",
        help="Where Webin-CLI writes its receipts"
    )
    args = p.parse_args()

    manifests = []
    if args.convert:
        manifests = convert_manifests(args.convert, args.submission_dir)

    if args.submit:
        user, pwd = load_credentials(args.cred_file)
        jar = find_jar(args.jar)
        logs = prepare_logs_dir(args.logs_dir)
        if not manifests:
            # discover all manifests under submission_dir
            manifests = sorted(
                glob.glob(os.path.join(args.submission_dir, "*", "manifest.txt"))
            )
            if not manifests:
                sys.exit("No manifests found; run with -c your.xlsx first.")
        submit_manifests(manifests, jar, user, pwd, args.live, logs)

    if not args.convert and not args.submit:
        p.print_help()

if __name__ == "__main__":
    main()
