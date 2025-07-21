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

The Webin CLI jar file can be downloaded from `https://github.com/enasequence/webin-cli/releases`.

## Usage

If running on the HPC, all you need to set is the configuration file, in which you will find all necessary configuration settings, like designated paths and parameters. Then, simply running `hpc.sh` with the option that you want (either `biosamples`, `analysis`, or `runs`) will run the proper script.

A typical command will look like this (once you are in the proper root directory):  
`bash hpc.sh runs` or `./hpc.sh biosamples`

Each script is run independently.

If not running on the HPC:

- The configuration file should be filled, and in case any argument is left empty, the scripts will read the arguments passed when called. Then if missing also, the default values will be used as input.

- Then run `set_env.py` in order to create the environment (it is recommended to only run #3 every time):

```
    #1 To only create or update the environment:
    python set_env.py -s

    #2 After setup, spawn a new interactive shell in order to be able to run the programs using the environment:
    python set_env.py -r

    #3 Do both in one command (recommended):
    python set_env.py -s -r
```

- Once created the environment, one can also run it manually by `source env/bin/activate` (Linux/Mac), or `env\Scripts\activate` (Windows cmd). Then once finished `deactivate`.

- **Run each script in its folder**, since it will be easier to define paths, and all submission files will be created in that folder (by default, if not specified in the configuration file).

- May use `-c` and `-s` if not using the configuration file, to generate XML or manifest(s) and to submit to ENA, respectively. Can do one or the two.

- By default, scripts run in “test” mode, the `live` field in the configuration file (or `--live` flag as argument) switches from the test endpoint to the production server.

- Credentials may come from the `credentials` field, or (only for biosamples.py) when using terminal arguments, `--cred_file` or `--username` and `--password`. This credentials file is assumed to be a text file with the username in line 1, and password in line 2.

- Logs and Webin-CLI receipts go into `logs/` by default, which is created automatically in the working directory.

## Warnings

- All objects depend on the associated Study object, which serves as an umbrella under which all other objects are. This object (Study) controls the release date of all objects associated with it. An explanation for the ENA metadata model can be found here: `https://ena-docs.readthedocs.io/en/latest/submit/general-guide/metadata.html`.

- The center name is determined by the user's account.


## Requirements

If running on FU Berlin's HPC, there are no software requirements, all necessary modules are already there.

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
  Used to read the configuration file.

- **biopython**  
  Required for annotation conversion from Genbank to EMBL format (`.gb` -> `.embl`).

More often than not, just running `pip install "module_name"` works.
