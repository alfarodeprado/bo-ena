# ENA BioSamples Submission Script

This is a standalone script for generating and submitting ENA BioSamples XML from a metadata spreadsheet.

## Folder Structure

```
biosamples/
├── biosamples.py
├── biosamples.xlsx
└── credentials.txt   # (optional) ENA username/password, or pass via CLI
```

- **biosamples.xlsx** – your metadata table. Column headers must match the `expected_fields` list in `biosamples.py`.  
- **credentials.txt** – plain text file with two lines:
  ```
  username: your_ena_username
  password: your_ena_password
  ```
  Or supply `-u`/`--user` and `-p`/`--password` on the command line instead.

## Requirements

- Python ≥ 3.8  
- pandas ≥ 1.2  
- openpyxl ≥ 3.0  
- curl ≥ 7.0 (only if you use `--submit`)

## Usage

Run **inside** the `biosamples/` folder.

### Arguments

| Flag                     | Description                                                                                   | Required? |
|--------------------------|-----------------------------------------------------------------------------------------------|-----------|
| `-c`, `--convert`        | Path to Excel file to convert (e.g. `MetadataList.xlsx`)                                       | Either/Both       |
| `-s`, `--submit`         | Submit the generated XML files via `curl`                                                      | Either/Both        |
| `-u`, `--username`       | ENA username (overrides `--cred_file` if provided)                                             | No        |
| `-p`, `--password`       | ENA password (overrides `--cred_file` if provided)                                             | No        |
| `--cred_file`            | Path to credentials file (username on line 1, password on line 2); default: `credentials.txt`  | No        |
| `--live`                 | Submit to the live ENA endpoint instead of the DEV/test endpoint                               | No        |
| `--logs_dir`             | Directory to write submission logs; default: `logs`                                            | No        |

## Output

- XML files in `out-dir/xml/`  
- `biosample_accessions.txt` log  
- (With `--submit`) receipt files in `out-dir/receipt/`

---

*Under construction*: merging both scripts into a single entry point later, they'll be kept separate for now.