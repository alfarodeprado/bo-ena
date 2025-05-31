# BioSamples ENA submission tool

This is a standalone script for generating and submitting ENA BioSamples XML from a metadata spreadsheet.

## Folder Structure

```
biosamples/
├── biosamples.py
├── MetadataList.xlsx
└── credentials.txt   # (optional) ENA username/password, or pass via CLI
```

- **MetadataList.xlsx** – your metadata table. Column headers must match the `expected_fields` list in `biosamples.py`.  
- **credentials.txt** – plain text file with two lines:
  ```
  username: your_ena_username
  password: your_ena_password
  ```
  Or supply `-u`/`--user` and `-p`/`--password` on the command line instead.

## Requirements

- Python ≥ 3.8  
- pandas ≥ 1.2  
- openpyxl ≥ 3.0  (only if you use `--convert`)
- curl ≥ 7.0 (only if you use `--submit`)

## Usage

Run **inside** the `biosamples/` folder. A typical command will look like so: 

`python biosamples.py -c "(path/to/)MetadataList.xlsx" -s --cred_file "(path/to/)credentials.txt"`.

The script submits samples to the test site by default, so must use the `--live` flag to submit to ENA.
It also has the `<HOLD/>` action by default, which submits the biosamples on private, with a release date of two years from now, so that the user can easily manually release them from the webportal.

### Arguments

| Flag                     | Description                                                                                   | Required? |
|--------------------------|-----------------------------------------------------------------------------------------------|-----------|
| `-c`, `--convert`        | Path to Excel file to convert (e.g. `MetadataList.xlsx`)                                       | Either/Both       |
| `-s`, `--submit`         | Submit the generated XML files via `curl`                                                      | Either/Both        |
| `--cred_file`            | Path to credentials file (username on line 1, password on line 2); default: `credentials.txt`  | No        |
| `-u`, `--username`       | ENA username (overrides `--cred_file` if provided)                                             | No        |
| `-p`, `--password`       | ENA password (overrides `--cred_file` if provided)                                             | No        |
| `--live`                 | Submit to the live ENA endpoint instead of the test endpoint                               | No        |
| `--logs_dir`             | Directory to write submission logs; by default a `logs` will be created                                            | No        |

## Output

The code will create:

- A `biosamples.xml` file with all biosamples' information to be submitted
- A `submission.xml` file with the actions (submit and hold)
- A `biosample_accessions.txt` file with all the accession codes from the submitted samples
- (With `--submit`) receipt files in `logs/`

---

*Under construction*: merging all scripts into a single entry point later, they must be run each in its own folder for now.