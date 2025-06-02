# Annotation / Sequence ENA submission tool

Standalone script to create per-sample annotation or assembly submission files from the model excel file, and submitting to ENA making use of Webin-CLI.

It is specifically designed to make use of a standardized excel file format, and for submission of plastid annotation / sequences (chromosome list is hardcoded).

## Folder Structure

```
analysis/
├── analysis.py
├── AssemblyList.xlsx
├── assembly_file.<fasta|gb|embl>
└── credentials.txt
```

- **AssemblyList.xlsx** – metadata spreadsheet. Must include one of:
  - `FLATFILE` (path to `.embl` or `.gb`)  
  - `FASTA` (path to un-annotated FASTA)

- **assembly_file.<fasta|gb|embl>** – your sequence file. Name must match the reference in `AssemblyList.xlsx`.
- **credentials.txt** – plain text file with two lines:
  ```
  your_ena_username
  your_ena_password
  ```

## Requirements (only if not running `set_env.py`)

- Python ≥ 3.8  
- pandas ≥ 1.2 
- openpyxl ≥ 3.0 (only if you use `--convert`)
- Java ≥ 17 (to run Webin-CLI JAR for manifest submission)
- Biopython ≥ 1.78 (optional, only if you don't already supply the annotation in `.embl` format)

## Usage

Run **inside** the `analysis/` folder. It will automatically create a folder (`submission/`) with all the submisson files already zipped and ready to submit (each in its own biosample-named folder), and a folder with the logs (`logs/`) so the submission's receipt can be checked.

A typical command will look like so:

`python analysis.py -c "(path/to/)AssemblyList.xlsx" -s -j "(path/to/)webin-cli-8.2.0.jar" --cred_file "(path/to/)credentials.txt"`.

The path to the assembly file or FASTA is specified in the excel, so no need to further define it.

The script submits the analysis objects to the test site by default, so must use the `--live` flag to submit to ENA.

### Arguments


| Flag                       | Description                                                                                         | Required? |
|----------------------------|-----------------------------------------------------------------------------------------------------|-----------|
| `-c`, `--convert`          | Path to Excel file to convert (e.g. `AssemblyList.xlsx`)                                                 | Either/Both       |
| `-s`, `--submit`           | Submit all `submission/*` files via Webin-CLI                                           | Either/Both        |
| `-j`, `--jar`              | Path to Webin-CLI JAR (auto‐detected if omitted)                                                     | Yes        |
| `--cred_file`              | File with username (line 1) and password (line 2) (default: `credentials.txt`)                       | Yes        |
| `--live`                   | Use real submissions (omit `-test` flag). By default, runs in test mode                               | No        |
| `--submission_dir`         | Top‐level folder for per‐sample subdirs (default: `submission`)                                       | No        |
| `--logs_dir`               | Directory where Webin-CLI writes its receipt logs (default: `logs`)                                  | No        |


## Output Structure

The code will create a folder structure like so, for submission:

```
submission/
├── SAMPLE1/
│   ├── manifest.txt
│   ├── chr_list.txt.gz
│   └── assembly_file.fasta.gz  (or .embl/.gb.gz + conversion)
├── SAMPLE2/
│   ├── manifest.txt
│   ├── chr_list.txt.gz
│   └── assembly_file.fasta.gz  (or .embl/.gb.gz + conversion)
└── …
```

It will also create the `logs/` folder when using `-s`.

---

*Under construction*: merging all scripts into a single entry point later, they must be run each in its own folder for now.