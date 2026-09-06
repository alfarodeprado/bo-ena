# BioSamples ENA submission tool

Standalone scripts for generating and submitting ENA BioSamples XML from a
metadata table.

Which columns are expected, and which of them are mandatory, are read from an
**ENA sample checklist XML** that you point the config at. Nothing about the
checklist is written into the code, so any ENA sample checklist works. The repo
ships with the plant checklist `ERC000037.xml` configured, since that is what
ENflorA was first built for.

See [Using a different checklist](../README.md#using-a-different-checklist) in
the main README for the full walkthrough.

## Files

- **`biosamples.py`** – validates a metadata table against a checklist, builds
  the XML, and submits it.
- **`make_table.py`** – one-off helper that turns a checklist XML into a blank
  table for you to fill in. Never contacts ENA.
- **`ERC000037.xml`** – the ENA plant sample checklist, the configured default.
- **`BiosampleList.xlsx`** – hand-made plant template, `DATA` sheet to fill in
  and `INFO` sheet describing each column.
- **`credentials.txt`** – two lines, username then password. Or pass `-u`/`-p`
  on the command line.

Tables can be Excel (`.xlsx`, `.xls`), CSV (`.csv`) or tab-separated (`.tsv`,
`.tab`, `.txt`).

## Usage

Run **inside** the `biosamples/` folder.

```bash
# Build a blank table for a checklist you have none for (one-off)
python make_table.py --checklist ERC000019.xml -o MySampleList.xlsx

# Convert and submit
python biosamples.py -c "(path/to/)MyList.xlsx" -s --cred_file "(path/to/)credentials.txt"
```

Most settings normally come from `../config.yaml`, including the checklist
path; the flags below override it where the config leaves a value blank.

Paths in `config.yaml` are relative to the folder you run from, which is why
`checklist: ERC000037.xml` and `data_biosamples: BiosampleList.xlsx` resolve to
files in `biosamples/`.

**On FU Berlin's HPC,** `python` is not on the path until the modules are loaded
and the environment is active, so use `hpc.sh` rather than calling the scripts
directly: set `ena_object="make_table"` or `ena_object="biosamples"` at the top
and run it. To work interactively instead, load the modules, run
`python set_env.py -s -H` once, then `source env/bin/activate`, after which the
commands above work as written.

Submissions go to the **test** site by default; use `--live` for the real one.
The `<HOLD/>` action is always included, so samples are submitted private with
a release date two years out, and you release them yourself from the web portal.

### Arguments

| Flag | Description | Required? |
|---|---|---|
| `-c`, `--convert` | Path to the table to convert | Either/Both |
| `-s`, `--submit` | Submit the generated XML via `curl` | Either/Both |
| `--checklist` | Checklist XML to validate against (overrides `config.yaml`) | No |
| `--cred_file` | Credentials file; default `credentials.txt` | No |
| `-u`, `--username` | ENA username (overrides `--cred_file`) | No |
| `-p`, `--password` | ENA password (overrides `--cred_file`) | No |
| `--live` | Submit to the live endpoint instead of the test one | No |
| `--logs_dir` | Where to write submission logs; default `logs/` | No |
| `-v`, `--verbose` | Print what the script is doing at each step | No |
| `--demo` | Use the bundled demo data and the test server | No |

### `make_table.py` arguments

| Flag | Description |
|---|---|
| `--checklist` | Checklist XML to build from (default: `checklist` in the config) |
| `-o`, `--output` | Table to write (default: `data_biosamples` in the config) |
| `--all-fields` | Include optional checklist fields, not just mandatory and recommended |
| `--force` | Overwrite an existing file |

## What gets checked

Mandatory fields must be present and filled for every sample, or the run stops.
Missing recommended fields produce a note. Empty recommended and optional cells
are not submitted. Columns matching no checklist field are submitted as free
sample attributes. Value formats and controlled vocabularies are left to ENA's
own validator.

`isolate`, `organism` and `taxon_id` are required whatever the checklist: they
become the sample alias, the title, and the taxon. They are part of ENA's
sample record rather than the checklist, so you will not find them in any
checklist XML.

## Output

- `biosamples.xml` — all samples, tagged with the checklist accession
- `submission.xml` — the actions (submit and hold)
- `biosample_accessions.txt` — assigned accessions, with a `server` column
  marking test vs live. Test accessions do not exist on the live server.
- With `--submit`, receipt files in `logs/`