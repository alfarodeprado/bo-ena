# Raw reads ENA submission tool

Standalone script to create per-sample submission files from the model excel file, and submitting sequence reads to ENA making use of Webin-CLI.

## Folder Structure

```
runs/
├── runs.py
├── ExperimentList.xlsx
└── credentials.txt   # (optional) ENA username/password
```

- **ExperimentList.xlsx** – metadata spreadsheet. Must include a path to one of:
  - `BAM` 
  - `CRAM`
  - `FASTQ` (can input two for paired reads)
  
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

## Usage

Run **inside** the `runs/` folder. It will automatically create a folder (`submission/`) with all the submisson files already zipped and ready to submit (each in its own biosample-named folder), and a folder with the logs (`logs/`) so the submission's receipt can be checked.

A typical command will look like so:

`python runs.py -c "(path/to/)ExperimentList.xlsx" -s -j "(path/to/)webin-cli-8.2.0.jar" --cred_file "(path/to/)credentials.txt"`.

The script submits the reads objects to the **test** site by default, so must use the `--live` flag to submit to ENA.

The path to the reads must have been specified in the excel, so no need to further define it.


### Arguments


| Flag                       | Description                                                                                         | Required? |
|----------------------------|-----------------------------------------------------------------------------------------------------|-----------|
| `-c`, `--convert`          | Path to Excel file to convert                                                                       | Either/Both       |
| `-s`, `--submit`           | Submit all `submission/*` files via Webin-CLI                                                       | Either/Both        |
| `-j`, `--jar`              | Path to Webin-CLI JAR (auto‐detected if omitted)                                                    | Yes        |
| `--cred_file`              | File with username (line 1) and password (line 2) (default: `credentials.txt`)                      | Yes        |
| `--live`                   | Use real submissions (omit `-test` flag). By default, runs in test mode                             | No        |
| `--submission_dir`         | Top‐level folder for per‐sample subdirs (default: `submission`)                                     | No        |
| `--logs_dir`               | Directory where Webin-CLI writes its receipt logs (default: `logs`)                                 | No        |


## Output Structure

The code will create a folder structure like so, for submission:

```
submission/
├── SAMPLE1/
│   ├── manifest.txt
│   └── sample_name.fastq.gz
├── SAMPLE2/
│   ├── manifest.txt
│   └── sample_name.fastq.gz
└── …
```

It will also create the `logs/` folder when using `-s`.

---

*Under construction*: merging all scripts into a single entry point later, they must be run each in its own folder for now.