import sys
import subprocess
import os
from pathlib import Path
import argparse

# Paths
ROOT    = Path(__file__).parent.resolve()
ENV_DIR = ROOT / "env"
BIN_DIR = ENV_DIR / ("Scripts" if os.name == "nt" else "bin")


def run_bash(cmd_list):
    """
    Run a single shell command using 'bash -lc', so that 'module load' works.
    """
    bash_cmd = ["/bin/bash", "-lc", " ".join(cmd_list)]
    return subprocess.run(bash_cmd, check=True)


def bootstrap_venv():
    """
    Create or update the virtual environment in ENV_DIR, then pip-install dependencies.
    """
    if not ENV_DIR.exists():
        print(f"→ Creating virtual environment in {ENV_DIR}")
        subprocess.check_call([sys.executable, "-m", "venv", str(ENV_DIR)])
    else:
        print(f"→ Virtual environment already exists at {ENV_DIR}, upgrading packages…")

    python_bin = BIN_DIR / ("python.exe" if os.name == "nt" else "python")

    # 1) Upgrade pip
    print("→ Upgrading pip inside the venv…")
    subprocess.check_call([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])

    # 2) Install / upgrade required packages
    packages = ["pandas", "openpyxl", "biopython", "pyyaml"]
    print(f"→ Installing/updating packages: {', '.join(packages)}")
    subprocess.check_call([str(python_bin), "-m", "pip", "install", "--upgrade"] + packages)

    print("Virtual environment is ready.\n")


def open_venv_shell(use_hpc):
    """
    Launch a new interactive bash shell with:
      - optional 'module load' if use_hpc is True
      - then 'source env/bin/activate' so the venv is active inside that shell.
    """
    if use_hpc:
        print("→ Loading HPC modules (Java) before opening shell…")
        try:
            run_bash(["module add Java/21.0.5"])
        except subprocess.CalledProcessError as e:
            print("Error: failed to load Java:", e)
            sys.exit(1)
        

    activate_script = BIN_DIR / ("activate.bat" if os.name == "nt" else "activate")
    if not activate_script.exists():
        print(f"Error: cannot find activation script at {activate_script}")
        sys.exit(1)

    # Spawn a new interactive bash that sources the venv’s activate script.
    cmd = f"source '{activate_script}' && exec bash"
    print("→ Launching a new shell with virtualenv activated. (type 'exit' to return.)\n")
    subprocess.run(["/bin/bash", "-lc", cmd])


def main():
    """
    Quick usage:

      # 1) Create or update "env/":
      python set_env.py -s

      # 2) After setup, spawn a new interactive shell:
      python set_env.py -r

      # 3) Do both in one command:
      python set_env.py -s -r [-H]

      (Add -H if running on the HPC, this way it will directly module load Java)
    """
    parser = argparse.ArgumentParser(
        description="Create/update venv and/or open a shell with venv activated"
    )
    parser.add_argument(
        "--hpc", "-H", action="store_true",
        help="Load Java in case it's being called from the FU's HPC before setup or shell."
    )
    parser.add_argument(
        "--setup", "-s", action="store_true",
        help="Create or update the virtual environment and install packages."
    )
    parser.add_argument(
        "--run", "-r", action="store_true",
        help="Open a new interactive shell with the venv activated (and HPC modules if requested)."
    )

    args = parser.parse_args()

    if not (args.setup or args.run):
        parser.print_help()
        sys.exit(1)

    # If HPC modules are requested for either action, load them first
    if args.hpc:
        print("→ HPC=True: loading required modules…")
        try:
            run_bash(["module add Java/21.0.5"])
        except subprocess.CalledProcessError as e:
            print("Error: failed to load Java:", e)
            sys.exit(1)
    else:
        print("→ HPC=False: skipping 'module load'.")

    # Perform setup if requested
    if args.setup:
        bootstrap_venv()

    # Open the shell if requested
    if args.run:
        open_venv_shell(use_hpc=False)  # HPC already processed above

    # If only setup was requested, remind user how to enter the shell
    if args.setup and not args.run:
        print("Done. To enter the environment shell, run:\n  python set_env.py -r\n")


if __name__ == "__main__":
    main()
