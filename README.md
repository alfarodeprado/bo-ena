# bo-ena - Tool for submission of plastid biosamples, reads and annotations to ENA

A simple program to submit biosample metadata (Biosample), sequences (Experiment + Run) and assemblies or annotations (Analysis) to ENA, using simple python scripts and Webin-CLI.


## Folder structure

The structure inside the main working directory should look like this:
```

├── biosamples/
│   ├── biosamples.py
│   └── MetadataList.xlsx
│
├── analysis/
│   ├── analysis.py
│   ├── AssemblyList.xlsx
│   └── assembly_file.<fasta | gb | embl>
│
├── runs/
│   ├── runs.py
│   └── ExperimentList.xlsx
│
├── config.yaml
├── set_env.py
├── credentials.txt
├── webin-cli-xxx.jar
├── .gitignore
└── README.md
```

## Usage

Each script is run independently for now.

- First and foremost, run `set_env.py` in order to create the environment (it is recommended to only run #3 every time):

```
    #1 To only create or update the environment:
    python set_env.py -s

    #2 After setup, spawn a new interactive shell in order to be able to run the programs using the environment:
    python set_env.py -r

    #3 Do both in one command (recommended):
    python set_env.py -s -r [-H]

    (Add -H if running on the HPC, this way it will directly "load Java")
```

- Once created the environment, one can also run it manually by `source env/bin/activate` (Linux/Mac), or `env\Scripts\activate` (Windows cmd). Then once finished `deactivate`.

- The config file should be filled, and in case any argument is left empty, the scripts will read the arguments passed when called. Then if missing also, the default values will be used as input.

- **Run each script in its folder**, since it will be easier to define paths, and all submission files will be created in that folder.

- May use `-c` and `-s` if not using the config file, to generate XML or manifest(s) and to submit to ENA, respectively. Can do one or the two.

- By default, scripts run in “test” mode, the `live` field in the config file (or `--live` flag as argument) switches from the test endpoint to the production server.

- Credentials may come from the `credentials` field, or (only for biosamples.py) when using terminal arguments, `--cred_file` or `--username` and `--password`. This credentials file is assumed to be a text file with the username in line 1, and password in line 2.

- Logs and Webin-CLI receipts go into `logs/` by default, which is created automatically in the working directory.

## Requirements

If running set_env.py:

- **Python ≥ 3.8**  
  All scripts are written for Python 3; tested on 3.8–3.12.

- **Java ≥ 17**  
  Only for data files submission (runs and analysis objects), not necessary for biosample submission. (not required if running on FUB HPC)

- **curl**  
  Only for biosample submission.
  
If not:

- **pandas ≥ 1.2**  
  Used for reading and processing Excel files in both `analysis.py` and `biosamples.py`.

- **openpyxl ≥ 3.0**  
  Required by pandas to parse `.xlsx` workbooks.

- **pyyaml**  
  Used to read the config file.

- **biopython**  
  Required for annotation conversion from Genbank to EMBL format (`.gb` -> `.embl`).

More often than not, just running `pip install module_name` works.

When running on FU Berlin's HPC, only running the command `module load Python/3.11.3-GCCcore-12.3.0` is necessary, in order to run set_env.py and the rest of the scripts.

---

*Under construction*: merging alll scripts into a single entry point later, they must be run separately for now.