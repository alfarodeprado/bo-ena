# Downloadable libraries
import pandas as pd
import yaml

# Standard libraries
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import argparse  # Manage arguments
import sys
import os        # Paths, folders, etc
import datetime  # For conversion of date
import subprocess  # For curl
import re       # For date pattern matching
import tempfile
import shlex

def load_config(cfg_path: str = "../config.yaml") -> dict:
    """
    Return a dict with the YAML content or an empty dict if the file is absent.
    """
    if os.path.exists(cfg_path):
        with open(cfg_path, "r") as fh:
            return yaml.safe_load(fh) or {}
    return {}

# Default ENA endpoints
TEST_ENDPOINT = "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/"
LIVE_ENDPOINT = "https://www.ebi.ac.uk/ena/submit/drop-box/submit/"


def excel_to_xml(excel_file, output_xml="biosamples.xml"):
    # Expected fields (in the expected order)
    expected_fields = [
        "isolate", "organism", "taxon_id", "bio_material", "specimen_voucher",
        "collected_by", "collection date", "country", "region", "locality",
        "latitude", "longitude", "altitude", "plant structure",
        "plant developmental stage", "plant growth medium", "isolation and growth condition"
    ]
    
    # Define mandatory attributes mapping
    mandatory = [
        "taxon_id",
        "isolate",
        "organism",
        "collection date",
        "latitude",           # becomes geographic location (latitude)
        "longitude",          # becomes geographic location (longitude)
        "plant structure",
        "country",            # becomes geographic location (country and/or sea)
        "plant developmental stage",
        "plant growth medium",
        "isolation and growth condition",
        "bio_material",
        "altitude"
    ]
    
    # Define recommended attributes (will skip if empty)
    recommended = [
        "region",             # part of geographic location (region and locality)
        "locality",           # part of geographic location (region and locality)
        "collected_by",
        "specimen_voucher"
    ]
    
    # Read the first sheet of the excel file
    try:
        df = pd.read_excel(excel_file, sheet_name=0)
    except Exception as e:
        sys.exit(f"Error reading Excel file: {e}")
    
    # Verify that all expected columns are present
    missing_cols = [col for col in expected_fields if col not in df.columns]
    if missing_cols:
        sys.exit(f"Missing expected columns in Excel file: {', '.join(missing_cols)}")
    
    # Any extra columns beyond expected_fields?
    extra_fields = [col for col in df.columns if col not in expected_fields]
    
    # Create the root XML element
    root = ET.Element("SAMPLE_SET")
    
    # Helper function to add a SAMPLE_ATTRIBUTE element
    def add_attribute(parent, tag, value, units=None):
        attr_elem = ET.SubElement(parent, "SAMPLE_ATTRIBUTE")
        ET.SubElement(attr_elem, "TAG").text = tag
        ET.SubElement(attr_elem, "VALUE").text = str(value)
        if units:
            ET.SubElement(attr_elem, "UNITS").text = units
    
    # Process each row/sample
    for index, row in df.iterrows():
        row_number = index + 1

        # Default plant growth medium if blank
        pgm = row["plant growth medium"]
        if pd.isnull(pgm) or str(pgm).strip() == "":
            row["plant growth medium"] = "soil"

        # Check mandatory fields are not empty
        for field in mandatory:
            cell_value = row[field]
            if pd.isnull(cell_value) or str(cell_value).strip() == "":
                sys.exit(f"Error: Mandatory field '{field}' is empty for sample number {row_number}")

        # Convert the date to ISO format (allow only year, or DD.MM.YYYY)
        raw_date = row["collection date"]
        date_str = None
        # If it's a datetime object
        if isinstance(raw_date, datetime.datetime):
            date_str = raw_date.strftime("%Y-%m-%d")
        else:
            raw_text = str(raw_date).strip()
            # Year-only
            if re.fullmatch(r"\d{4}", raw_text):
                date_str = raw_text
            else:
                # Try German DD.MM.YYYY
                try:
                    date_obj = datetime.datetime.strptime(raw_text, "%d.%m.%Y")
                    date_str = date_obj.strftime("%Y-%m-%d")
                except Exception:
                    # Fallback: pass through original text
                    date_str = raw_text

        # Build the <SAMPLE> element
        sample = ET.SubElement(root, "SAMPLE", attrib={
            "alias": str(row["isolate"]),
            "center_name": ""
        })
        ET.SubElement(sample, "TITLE").text = str(row["organism"])
        sample_name = ET.SubElement(sample, "SAMPLE_NAME")
        ET.SubElement(sample_name, "TAXON_ID").text = str(row["taxon_id"])
        
        sample_attributes = ET.SubElement(sample, "SAMPLE_ATTRIBUTES")
        
        # Always-added attributes
        add_attribute(sample_attributes, "bio_material", row["bio_material"])
        add_attribute(sample_attributes, "collection date", date_str)
        add_attribute(sample_attributes, "geographic location (country and/or sea)", row["country"])
        add_attribute(sample_attributes, "geographic location (latitude)", row["latitude"], "DD")
        add_attribute(sample_attributes, "geographic location (longitude)", row["longitude"], "DD")
        add_attribute(sample_attributes, "altitude", row["altitude"], "m")
        add_attribute(sample_attributes, "plant structure", row["plant structure"])
        add_attribute(sample_attributes, "plant developmental stage", row["plant developmental stage"])
        add_attribute(sample_attributes, "plant growth medium", row["plant growth medium"])
        add_attribute(sample_attributes, "isolation and growth condition", row["isolation and growth condition"])
        
        # Recommended (only if non-empty)
        loc = str(row["locality"]).strip() if not pd.isnull(row["locality"]) else ""
        reg = str(row["region"]).strip() if not pd.isnull(row["region"]) else ""
        combined = f"{loc}, {reg}" if loc and reg else loc or reg
        if combined:
            add_attribute(sample_attributes, "geographic location (region and locality)", combined)
        if pd.notnull(row["collected_by"]) and str(row["collected_by"]).strip():
            add_attribute(sample_attributes, "collected_by", row["collected_by"])
        if pd.notnull(row["specimen_voucher"]) and str(row["specimen_voucher"]).strip():
            add_attribute(sample_attributes, "specimen_voucher", row["specimen_voucher"])
        
        # Any extra columns from the Excel become recommended too
        for field in extra_fields:
            val = row[field]
            if pd.notnull(val) and str(val).strip():
                add_attribute(sample_attributes, field, val)

        # Always include ENA-CHECKLIST
        add_attribute(sample_attributes, "ENA-CHECKLIST", "ERC000037")

    # Pretty-print and write out
    rough = ET.tostring(root, encoding="utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ")
    try:
        with open(output_xml, "w", encoding="utf-8") as f:
            f.write(pretty)
        print(f"{output_xml} file successfully written")
    except Exception as e:
        sys.exit(f"Error writing {output_xml}: {e}")


# Has <hold> so they don't become immediately public in case it goes to "live"
def create_submission_xml(submission_xml="submission.xml"):
    submission_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
    <SUBMISSION>
        <ACTIONS>
            <ACTION>
                <ADD/>
            </ACTION>
            <ACTION>
                <HOLD/>
            </ACTION>
        </ACTIONS>
    </SUBMISSION>
    '''
    if not os.path.exists(submission_xml):
        with open(submission_xml, "w") as f:
            f.write(submission_xml_content)
        print(f"{submission_xml} created.")
    else:
        print(f"{submission_xml} already exists.")


def prepare_logs_dir(logs_dir="logs"):
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"Directory '{logs_dir}' created.")
    else:
        print(f"Directory '{logs_dir}' already exists.")
    return logs_dir


# Uses the test submission as default, just in case
def submit_data(username, password, logs_dir="logs", url=TEST_ENDPOINT):
    # Build submission and receipt filenames
    submission_file = "submission.xml"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    receipt_file = os.path.join(logs_dir, f"biosample_receipt_{timestamp}.xml")

    # create a temporary netrc file for curl authentication
    if "://" in url:
        host = url.split("://", 1)[1].split("/", 1)[0]
    else:
        host = url.split("/", 1)[0]

    with tempfile.NamedTemporaryFile("w", delete=False) as tf:
        tf.write(f"machine {host}\nlogin {username}\npassword {password}\n")
    netrc_path = tf.name
    os.chmod(netrc_path, 0o600)

    try:
        curl_command = [
            "curl",
            "--netrc-file", netrc_path,              # <— no -u flag
            "-F", f"SUBMISSION=@{submission_file}",
            "-F", f"SAMPLE=@biosamples.xml",
            url,
            "-o", receipt_file
        ]

        # 3) print *safe* command (no secrets anywhere)
        print("→ Running:", " ".join(shlex.quote(a) for a in curl_command))

        result = subprocess.run(curl_command, capture_output=True, text=True)
    finally:
        os.remove(netrc_path)                        # ensure cleanup
    
    # Run curl
    # curl_command = [
    #     "curl",
    #     "-u", f"{username}:{password}",
    #     "-F", f"SUBMISSION=@{submission_file}",
    #     "-F", f"SAMPLE=@biosamples.xml",
    #     url,
    #     "-o", receipt_file
    # ]
    # result = subprocess.run(curl_command, capture_output=True, text=True)
    print("Curl exit code:", result.returncode)
    if result.stdout:
        print("Stdout:", result.stdout)
    if result.stderr:
        print("Stderr:", result.stderr)

    # Parse receipt XML, to look for accession codes, alias, and whether success or not
    if os.path.exists(receipt_file):
        try:
            tree = ET.parse(receipt_file)
            root = tree.getroot()
            success = root.attrib.get('success', 'false')
            print(f"Submission success: {success}")

            # Extract sample accession & alias
            records = []
            for samp in root.findall('SAMPLE'):
                acc = samp.attrib.get('accession')
                alias = samp.attrib.get('alias')
                records.append((acc, alias))

            # Write to text file
            out_file = os.path.join(os.path.dirname(__file__), 'biosample_accessions.txt')
            write_mode = "a+" if os.path.exists(out_file) else "w+"
            with open(out_file, write_mode) as out:
                out.seek(0)
                existing = {l.strip() for l in out if l.strip()}
                if not existing:
                    out.write("accession\talias\n")
                for acc, alias in records:
                    line = f"{acc}\t{alias}"
                    if line not in existing:
                        out.write(line + "\n")
            print(f"Accessions written to {out_file}")
        except Exception as e:
            print(f"Error parsing receipt XML: {e}")
    else:
        print(f"Receipt file not found: {receipt_file}")


def load_credentials(file_path):
    try:
        with open(file_path) as cred:
            lines = [l.strip() for l in cred if l.strip()]
        if len(lines) < 2:
            raise ValueError("Credentials file must have at least two non-empty lines: \nusername \npassword.")
        return lines[0], lines[1]
    except Exception as e:
        sys.exit(f"Error loading credentials from {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Biosamples submission tool to ENA, converts Excel to XML and submits."
    )

    parser.add_argument(
        "--config", default="../config.yaml",
        help="Path to YAML config file (default: config.yaml)")
    
    parser.add_argument("-c", "--convert", metavar="EXCEL_FILE",
                        help="Convert the given Excel file (e.g., 'MetadataList.xlsx') to biosamples.xml")

    parser.add_argument("-s", "--submit", action="store_true",
                        help="Submit the XML files using curl")

    parser.add_argument("-u", "--username",
                        help="Username for submission (optional if --cred_file is provided)")

    parser.add_argument("-p", "--password",
                        help="Password for submission (optional if --cred_file is provided)")

    parser.add_argument("--cred_file", default="credentials.txt",
                        help="Path to a text file with username on line 1 and password on line 2")

    parser.add_argument("--live", action="store_true",
                        help="Submit to the live ENA endpoint instead of test (DEV) endpoint")

    parser.add_argument("--logs_dir", default="logs",
                        help="Directory to store submission logs (default: logs)")

    args = parser.parse_args()

    cfg = load_config(args.config)

    excel_path = cfg.get("excel_biosamples")
    if not excel_path:
        excel_path = args.convert
    
    submit = cfg.get("submit")
    if not submit:
        submit = args.submit

    cred_path = cfg.get("credentials")
    if not cred_path:
        cred_path = args.cred_file

    live = cfg.get("live")
    if not live:
        live = args.live
    


    if excel_path:
        excel_to_xml(excel_path)

    if submit:
        # Load or override credentials
        if args.username and args.password:
            user, pw = args.username, args.password
        else:
            user, pw = load_credentials(cred_path)

        create_submission_xml()
        logs = prepare_logs_dir(args.logs_dir)
        endpoint = LIVE_ENDPOINT if live else TEST_ENDPOINT
        print(f"Using endpoint: {endpoint}")
        submit_data(user, pw, logs, endpoint)

    if not excel_path and not submit:
        parser.print_help()


if __name__ == "__main__":
    main()
