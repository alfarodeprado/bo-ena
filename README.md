# bo-ena
A simple program to submit sequences and annotations to ENA, using simple python scripts and Webin-CLI.



## Folder structure

The structure inside the main working directory should look like this:
```
├── analysis/
│   ├── analysis.py
│   ├── analysis.xlsx
│   └── assembly_file.<fasta | gb | embl>
│
├── biosamples/
│   ├── biosamples.py
│   └── biosamples.xlsx
│
├── .gitignore
└── README.md
```

## Usage

Each script is run independently in its own folder. Make sure you `cd` into the folder containing the script, Excel file, and any required inputs before invoking it.

- Always run from inside biosamples/ or analysis/, so that the excel file is in .

- May use --convert to generate XML or manifest(s), and add --submit to post it to ENA. Can do one or the two.

- Credentials may come from --username/--password or --cred_file

- By default runs in “test” mode, --live switches from test endpoint to the production server

- Logs and Webin-CLI receipts go into logs/ by default

## Requirements

This is an area under construction, as scripts will still move around a bit.

Requirements for both scripts:

- **Python ≥ 3.8**  
  All scripts are written for Python 3; tested on 3.8–3.11.

- **pandas ≥ 1.2**  
  Used for reading and processing Excel files in both `analysis.py` and `biosamples.py` :contentReference[oaicite:0]{index=0}.

- **openpyxl ≥ 3.0**  
  Required by pandas to parse `.xlsx` workbooks.



---

*Under construction*: making a python venv for most requirements, and merging both scripts into a single entry point later, they'll be kept separate for now.