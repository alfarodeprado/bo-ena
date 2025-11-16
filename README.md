# bo-ena – ENA submission helper (biosamples, reads, assemblies)

Small collection of scripts to help submit to ENA:

- **Biosample metadata** (BioSamples)
- **Raw reads** (Experiments + Runs)
- **Assemblies / annotations** (Analyses)

using plain Python + Webin-CLI (for reads/assemblies) or `curl` (for biosamples).

The scripts were originally written for plastid plant data. At the moment, biosamples.py is tied to the ENA plant checklist ERC000037 and plant-specific attributes, and chromosome-level assemblies default to a plastid chromosome unless you override CHR_NAME / CHR_TYPE / CHR_LOCATION. Apart from that, the logic is generic and can be used for other organisms as long as your metadata tables follow the expected columns.


## Folder layout

Expected layout in the main working directory:

```text
bo-ena/
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
├── lftp_sub.sh                 # script to upload via lftp if main scripts fail (only reads)
├── credentials.txt             # Webin username (line 1) + password (line 2)
├── webin-cli-*.jar             # Webin-CLI JAR
└── README.md
```

The Webin CLI jar file can be downloaded from `https://github.com/enasequence/webin-cli/releases`.

## What each script does

### `biosamples/biosamples.py`

- Input: a metadata table (`BiosampleList.xlsx` or `.tsv`) with a header, and one row per biosample.
- Outputs:
  - `biosamples.xml`
  - `submission.xml`
  - optional submission to ENA’s BioSamples service (via `curl`).
- Keys in `config.yaml`: `data_biosamples`, `credentials`, `submit`, `live`.

### `runs/runs.py`

- Input: table of read libraries (`ExperimentList.xlsx` / `.tsv`) with paths to FASTQ/BAM/CRAM.
- Outputs:
  - Per-sample `submission/<SAMPLE_ACCESSION>/manifest.txt`
  - Staged and optionally compressed read files inside `submission/<SAMPLE>/`
  - optional submission of all manifests via Webin-CLI (`-context reads`).
- Keys in `config.yaml`: `data_runs`, `sub_dir_runs`, `credentials`, `jar`, `submit`, `live`.

### `analysis/analysis.py`

- Input: table of assemblies/annotations (`AnalysisList.xlsx` / `.tsv`) with paths to FASTA or EMBL/GenBank.
- Outputs:
  - Per-sample `submission/<SAMPLE_ACCESSION>/manifest.txt`
  - Staged and optionally compressed FASTA/EMBL in `submission/<SAMPLE>/`
  - optional submission of all manifests via Webin-CLI (`-context genome`).
- Handles:
  - GenBank → EMBL conversion via Biopython if needed.
  - `assembly_level` and `mingaplength` logic for contig/scaffold/chromosome assemblies.
- Keys in `config.yaml`: `data_analysis`, `sub_dir_analysis`, `credentials`, `jar`, `submit`, `live`, `assembly_level`, `mingaplength`.

### `lftp_sub.sh` (optional helper)

- Independent helper that:
  - finds raw data files under given input paths,
  - compresses them (if needed),
  - makes `.md5` checksum files,
  - uploads everything via `lftp` to a Webin FTP folder,
  - writes a TSV (`remote_path<TAB>md5`) you can paste into ENA templates.
- It does **not** call the Python scripts or Webin-CLI and can be used standalone.


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

2. From the project root:

   ```bash
   mkdir -p logs # Here go the slurm log files
   sbatch hpc.sh # This sends the job to the queue
   ```

   It can be run on the login node for a quick non-Slurm test or light submissions, but recommended to go through slurm anyway:

   ```bash
   bash hpc.sh
   ```

What running through `hpc.sh` does:

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

assembly_level: chromosome   # contig | scaffold | chromosome
mingaplength: 50             # used only if scaffold & no AGP
```

**Precedence rules (important):**

For each script:

1. It first looks in the config file for a value (e.g. `data_runs`).
2. If the config value is missing or empty, it falls back to the command‑line argument.
3. If both are unset, the script’s internal default is used.

So a non-empty config value **overrides** the corresponding CLI argument. In practical terms:

- If you want to control something via CLI, leave the relevant key empty or remove it from `config.yaml`.
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
