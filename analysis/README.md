# Genome Submission Manifests Generator

Standalone script to prepare per-sample submission folders and manifests for ENA/Webin-CLI or FASTA-only workflows.

## Folder Structure

```
analysis/
├── analysis.py
├── analysis.xlsx
└── assembly_file.<fasta|gb|embl>
```

- **analysis.xlsx** – metadata spreadsheet. Must include columns like `SAMPLE_NAME`, `STRAIN`, plus one of:
  - `FLATFILE` (path to `.embl` or `.gb`)  
  - `FASTA` (path to un-annotated FASTA)
- **assembly_file.<fasta|gb|embl>** – your sequence file. Name must match the reference in `analysis.xlsx`.

## Requirements

- Python ≥ 3.8  
- pandas ≥ 1.2 
- openpyxl ≥ 3.0
- Java ≥ 17 (to run Webin-CLI JAR for manifest submission)
- Biopython ≥ 1.78 (optional, only if you supply `.gb` files needing conversion)

## Usage

Run **inside** the `analysis/` folder.

### Arguments


| Flag                       | Description                                                                                         | Required? |
|----------------------------|-----------------------------------------------------------------------------------------------------|-----------|
| `-c`, `--convert`          | Path to Excel file to convert (e.g. `analysis.xlsx`)                                                 | Either/Both       |
| `-s`, `--submit`           | Submit all `submission/*` files via Webin-CLI                                           | Either/Both        |
| `--submission_dir`         | Top‐level folder for per‐sample subdirs (default: `submission`)                                       | No        |
| `-j`, `--jar`              | Path to Webin-CLI JAR (auto‐detected if omitted)                                                     | No        |
| `--cred_file`              | File with username (line 1) and password (line 2) (default: `credentials.txt`)                       | No        |
| `--live`                   | Use real submissions (omit `-test` flag). By default, runs in test mode                               | No        |
| `--logs_dir`               | Directory where Webin-CLI writes its receipt logs (default: `logs`)                                  | No        |


## Output Structure

```
submission/
├── SAMPLE1/
│   ├── SAMPLE1.manifest.json
│   ├── SAMPLE1.CHROMOSOME_LIST
│   └── assembly_file.fasta.gz  (or .embl/.gb.gz + conversion)
├── SAMPLE2/
└── …
```

- **Annotated**: put `.embl` or `.gb` under `FLATFILE`; `.gb` will be auto-converted.  
- **FASTA-only**: put `.fasta` under `FASTA`; header accession is auto-extracted.

You can then run Webin-CLI against `submission/` to send everything.

---

*Under construction*: merging both scripts into a single entry point later, they'll be kept separate for now.