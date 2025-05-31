# bo-ena
A simple program to submit sequences and annotations to ENA, using simple python scripts and Webin-CLI.



## Folder structure

The structure inside the main working directory should look like this:
```
├── analysis/
│   ├── analysis.py
│   ├── ExperimentList.xlsx
│   └── assembly_file.<fasta | gb | embl>
│
├── biosamples/
│   ├── biosamples.py
│   └── MetadataList.xlsx
│
├── .gitignore
└── README.md
```

## Usage

Each script is run independently for now.

- Run each script in its folder, since it will be easier to define paths, and all submission files will be created in that folder

- May use -c (--convert) to generate XML or manifest(s), and add -s (--submit) to post it to ENA. Can do one or the two.

- By default runs in “test” mode, --live switches from test endpoint to the production server

- Credentials may come from --username/--password or --cred_file

- Logs and Webin-CLI receipts go into logs/ by default, which is created automatically in the working directory

## Requirements

This is an area under construction, as scripts will still move around a bit.

General requirements:

- **Python ≥ 3.8**  
  All scripts are written for Python 3; tested on 3.8–3.12.

- **pandas ≥ 1.2**  
  Used for reading and processing Excel files in both `analysis.py` and `biosamples.py` :contentReference[oaicite:0]{index=0}.

- **openpyxl ≥ 3.0**  
  Required by pandas to parse `.xlsx` workbooks.


---

*Under construction*: making a python venv for most requirements, and merging alll scripts into a single entry point later, they'll be kept separate for now.