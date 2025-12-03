# ENflorA – ENA submission helper (biosamples, reads, assemblies)

Small collection of scripts to help submit to ENA:

- **Biosample metadata** (BioSamples)
- **Raw reads** (Experiments + Runs)
- **Assemblies / annotations** (Analyses)

using plain Python + Webin-CLI (for reads/assemblies) or `curl` (for biosamples). For a better understanding and documentation of the different ENA object types, please consult:  
`https://ena-docs.readthedocs.io/en/latest/submit/general-guide/metadata.html`

WARNING 1: Almost all data should be stored in either an Excel or tsv file. The column names and values are all defined inside the template excel, in the INFO sheet.

WARNING 2: Prior to running ENflorA, the user must have a study number, or create one themselves, as per ENA, all ENA object types except biosamples must be associated with a study. This can be done at:  
`https://www.ebi.ac.uk/ena/submit/webin/`

WARNING 3: The scripts were originally written for plastid plant data. At the moment, `biosamples.py` is tied to the ENA plant checklist ERC000037 and plant-specific attributes. In `analysis.py`, chromosome-level submissions default to a single plastid circular chromosome (CHR_NAME=1, CHR_TYPE=Circular-Chromosome, CHR_LOCATION=Plastid) if no chromosome columns are provided. To use nuclear or other chromosomes, simply add `CHR_NAME`, `CHR_TYPE`, and `CHR_LOCATION` columns to your analysis table; their values are written directly into chr_list.txt. Apart from that, the logic is generic and can be used for other organisms as long as your metadata tables follow the expected columns.


## Index

* [Folder layout](#folder-layout)
* [What each script does](#what-each-script-does)

  * [`hpc.sh`](#hpch)
  * [`biosamples/biosamples.py`](#biosamplesbiosamplespy)
  * [`runs/runs.py`](#runsrunspy)
  * [`analysis/analysis.py`](#analysisanalysispy)
  * [`lftp_sub.sh` (optional helper)](#lftp_subsh-optional-helper)
* [How to run](#how-to-run)

  * [1. Curta HPC via `hpc.sh` (FU Berlin)](#1-curta-hpc-via-hpcsh-fu-berlin)
  * [2. Local / other HPC using `set_env.py`](#2-local--other-hpc-using-set_envpy)
  * [3. Manual environment (no `set_env.py`)](#3-manual-environment-no-set_envpy)
* [Configuration (`config.yaml`)](#configuration-configyaml)
* [Requirements](#requirements)

  * [Common to all modes](#common-to-all-modes)
  * [If not running on the HPC](#if-not-running-on-the-hpc)
* [Optional `lftp_sub.sh`](#optional-lftp_subsh)
* [Logs and receipts](#logs-and-receipts)


## Folder layout

Expected layout in the main working directory:

```text
ENflorA/
├── biosamples/
│   ├── biosamples.py
│   └── BiosampleList.xlsx    // .tsv
│
├── runs/
│   ├── runs.py
│   └── ExperimentList.xlsx   // .tsv
│
├── analysis/
│   ├── analysis.py
│   └── AnalysisList.xlsx     // .tsv
│
├── config.yaml                 # shared config for all scripts
├── set_env.py                  # creates/updates env/ folder for Python dependencies
├── hpc.sh                      # Main script to use when using FUB's HPC
├── lftp_sub.sh                 # optional script to upload (only reads) via lftp if main scripts fail
├── credentials.txt             # Webin username (line 1) + password (line 2)
├── webin-cli-*.jar             # Webin-CLI JAR
└── README.md
```

The Webin CLI jar file can be downloaded from `https://github.com/enasequence/webin-cli/releases`.

## What each script does

### `hpc.sh`

- Only one parameter must be set inside, `ena_object`, which it calls.
- Can be called as a bash script or as a slurm job.
- Script to run any of the following ENA object uploaders from FUB's HPC.



### `biosamples/biosamples.py`

- Keys in `config.yaml`: `data_biosamples`, `credentials`, `submit`, `live`.
- Input: a metadata table (`BiosampleList.xlsx` or `.tsv`) with a header, and one row per biosample.
- Outputs:
  - `biosamples.xml`
  - `submission.xml`
  - optional submission to ENA’s BioSamples service (via `curl`).


### `runs/runs.py`

- Keys in `config.yaml`: `data_runs`, `sub_dir_runs`, `credentials`, `jar`, `submit`, `live`.
- Input: table of read libraries (`ExperimentList.xlsx` / `.tsv`) with paths to FASTQ/BAM/CRAM.
- Outputs:
  - Per-sample `submission/<SAMPLE_ACCESSION>/manifest.txt`
  - Staged and optionally compressed read files inside `submission/<SAMPLE>/`
  - optional submission of all manifests via Webin-CLI (`-context reads`).


### `analysis/analysis.py`

- Keys in `config.yaml`: `data_analysis`, `sub_dir_analysis`, `credentials`, `jar`, `submit`, `live`, `assembly_level`, `mingaplength`.
- Input: table of assemblies/annotations (`AnalysisList.xlsx` / `.tsv`) with paths to FASTA or EMBL/GenBank.
- Outputs:
  - Per-sample `submission/<SAMPLE_ACCESSION>/manifest.txt`
  - Staged and optionally compressed FASTA/EMBL in `submission/<SAMPLE>/`
  - optional submission of all manifests via Webin-CLI (`-context genome`).
- Handles:
  - GenBank → EMBL conversion via Biopython if needed.
  - `assembly_level` and `mingaplength` logic for contig/scaffold/chromosome assemblies.


### `lftp_sub.sh` (optional helper)

- Parameters must be set inside script.
- Independent helper that:
  - finds raw data files under given input paths,
  - compresses them (if needed),
  - makes `.md5` checksum files,
  - uploads everything via `lftp` to a Webin FTP folder,
  - writes a TSV (`remote_path <TAB> md5`) you can paste into ENA templates.
- It does **not** call the Python scripts or Webin-CLI, it's a standalone script.
- It requires the user to manually download the tsv template, and then upload to ENA, pasting in it the `remote_path` from the produced tsv. This can be done at their webpage, in the `Raw Reads (Experiments and Runs)` section:  
`https://www.ebi.ac.uk/ena/submit/webin/`


## How to run

There are three supported ways to run the scripts. Pick the one that matches your setup.

---

### 1. Curta HPC via `hpc.sh` (FU Berlin)

Use this if you are on FU Berlin’s Curta cluster and want everything handled automatically.

1. Inside `hpc.sh`, set which ENA object you want to run:

   ```bash
   # Possible values: biosamples, runs, analysis
   ena_object="analysis"
   ```

2. Then, from the project root run:

   ```bash
   mkdir -p logs          # Here go the slurm log files
   sbatch hpc.sh          # This sends the job to the queue
   ```

   It can be run on the login node for a quick non-Slurm test or light submissions, but recommended to go through slurm anyway:

   ```bash
   bash hpc.sh
   ```

What running through `hpc.sh` actually does:

- Loads Curta modules:

  ```bash
  module purge
  module load Python/3.11.3-GCCcore-12.3.0
  module load Java/21.0.5
  ```

- Calls `python set_env.py -s -H` to:
  - create or refresh `env/`,
  - install/upgrade Python libraries inside `env/`,
  - ensure Java is available via `module add Java/21.0.5`.
- Activates the virtualenv:

  ```bash
  source env/bin/activate
  ```

- Runs the chosen script inside the corresponding subfolder, e.g.:

  ```bash
  cd analysis
  python analysis.py
  ```

If you use `hpc.sh` you **do not** call `set_env.py` yourself; the job script does it for you.

---

### 2. Local / other HPC using `set_env.py`

Use this if you are **not** on Curta, but want `set_env.py` to manage the Python virtual environment for you.

From the project root:

```bash
# 1) Create or update env/ and install Python packages
python set_env.py -s

# 2) Spawn a new shell with the venv activated
python set_env.py -r
```

If you are on some other HPC with a `module` system and want `set_env.py` to load Java before opening the shell:

```bash
python set_env.py -s -r -H
```

(You may need to edit the `module add Java/21.0.5` line in `set_env.py` to match your cluster.)

Once inside the environment shell:

```bash
cd biosamples   # or runs / analysis
python biosamples.py
```

You can either rely on `config.yaml` or pass explicit CLI options (see each script’s `--help`).

---

### 3. Manual environment (no `set_env.py`)

If you prefer to manage everything yourself:

1. Create and activate your own virtualenv or conda env (can do without, in case you do have the dependencies installed already, but it's recommended to use an environment).
2. Install the required Python packages:

   ```bash
   pip install pandas openpyxl biopython pyyaml
   ```

3. Make sure the external tools you need are available (see **Requirements** below).
4. Run scripts directly, for example:

   ```bash
   cd runs
   python runs.py # Parameters are still read from the config file
   ```

In this mode `set_env.py` and `hpc.sh` are not used at all.


## Configuration (`config.yaml`)

All three Python scripts use a shared YAML configuration (`config.yaml`, typically in the project root). The provided example looks like:

```yaml
credentials: ../credentials.txt
jar: ../webin-cli-8.2.0.jar

data_biosamples: BiosampleList.xlsx
data_runs:       ExperimentList.xlsx
data_analysis:   AnalysisList.xlsx

submit: True
live:   False

sub_dir_runs:
sub_dir_analysis:

assembly_level: chromosome        # contig | scaffold | chromosome
mingaplength: 50                  # used only if scaffold & no AGP
```

**Parameters, precedence rules (important):**

For each script:

1. It first looks in the config file for a value (e.g. `data_runs`).
2. If the value in the config file is missing or empty, it falls back to the command‑line argument.
3. If both are unset, the script’s internal default is used.

So a non-empty config value **overrides** the corresponding CLI argument. In practical terms:

- If you want to control something via the command line, leave the relevant key empty or remove it from `config.yaml`.
- If you want to centralize settings, define them in `config.yaml` and call scripts with minimal flags.


## Requirements

### Common to all modes

Regardless of how you run things:

- A Unix‑like OS (Linux/macOS; the shell scripts assume Bash).
- An ENA **Webin account**.
- A Webin‑CLI JAR file (e.g. `webin-cli-8.2.0.jar`) placed somewhere reachable, and referenced in `config.yaml` (`jar:`).  


If running on FU Berlin's HPC, there are no software requirements, all necessary modules are already there or will be installed under `~/env/`. It's only necessary to check that python and java modules are available:
  ```bash
  module load Python/3.11.3-GCCcore-12.3.0
  module load Java/21.0.5
  ```

### If not running on the HPC

If running set_env.py you will need:

- **Python ≥ 3.8**  
  All scripts are written for Python 3; tested on 3.8–3.12.

- **Java ≥ 17**  
  Only for data files submission (runs and analysis objects), not necessary for biosample submission.

- **curl**  
  Only for biosample submission.

If running individual scripts, apart from the requirements above:

- **pandas ≥ 1.2**  
  Used for data handling, and processing data tables.

- **pyyaml**  
  Used to read the configuration file.

- **openpyxl ≥ 3.0**  
  Required by pandas to parse `.xlsx` workbooks (Excel).

- **biopython**  
  Only needed in `analysis.py`, only when Genbank to EMBL format conversion required (`.gb` -> `.embl`).

More often than not, just running `pip install "module_name"` works.

## Optional `lftp_sub.sh`

`lftp_sub.sh` is optional and completely independent from the Python / Webin‑CLI pipeline.

To use it you need:

- `bash`
- `lftp`
- `pigz` (for parallel gzip) **or** `gzip` (not both)
- `md5sum` (Linux) or `md5` (macOS)

Basic workflow:

1. Edit the **CONFIG** block inside `lftp_sub.sh`, at the top:
   - set `CREDENTIALS_FILE` or `WEBIN_USER` / `WEBIN_PASSWORD`,
   - set `REMOTE_BASE_DIR` and optional `BATCH_SUBDIR`,
   - set `OUT_TSV`,
   - fill the `INPUTS=(...)` array with the file paths or folder.
2. Run:

   ```bash
   ./lftp_sub.sh
   ```

3. Confirm when asked (unless you disable `ASK_CONFIRM_BEFORE_UPLOAD`).

The script will then compress, checksum, and upload files, and write a TSV mapping remote paths to MD5 sums.


## Logs and receipts

Each script writes basic receipts:

- `biosamples.py`
  - stores XML receipts from ENA under `logs/`,
  - appends accession mappings to a text file (e.g. `biosample_accessions.txt`).

- `runs.py` and `analysis.py`
  - create per‑sample log subfolders under `logs/` (e.g. `logs/SAMPLE_ID/reads/…` or `logs/SAMPLE_ID/genome/…`),
  - automatically delete stale `validate.json` files before each submission so Webin‑CLI recalculates MD5s.

It’s safe to delete `logs/` entirely if you want to start from a clean state; the scripts will recreate it.
