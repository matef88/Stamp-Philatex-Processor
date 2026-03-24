"""
Stamp Philatex Processor - Robust Environment Setup Script
Usage: python setup_env.py

1. Creates a local virtual environment (.venv) if missing
2. Upgrades pip
3. Installs dependencies from requirements.txt
4. Handles special cases like DirectML
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

# Configuration
REQUIREMENTS_FILE = "requirements.txt"
PROJECT_ROOT = Path(__file__).parent.parent

def get_venv_dir(root):
    """Detect venv directory, preferring 'venv' then '.venv'."""
    if (root / "venv").exists():
        return root / "venv"
    if (root / ".venv").exists():
        return root / ".venv"
    return root / "venv"  # Default to venv for new creation

def run_command(cmd, cwd=None, exit_on_error=True):
    """Run a shell command and handle errors."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        if exit_on_error:
            sys.exit(1)
        return False

def get_python_exe(venv_path):
    """Get path to python executable in venv."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"

def main():
    print("=" * 60)
    print(" Stamp Philatex Processor - Environment Setup")
    print(f" Python: {sys.version}")
    print("=" * 60)

    # Convert paths to absolute
    root_dir = PROJECT_ROOT.resolve()
    venv_path = get_venv_dir(root_dir).resolve()
    req_path = (root_dir / REQUIREMENTS_FILE).resolve()

    os.chdir(root_dir)

    # 1. Check for existing venv
    venv_python = get_python_exe(venv_path)
    if not venv_python.exists():
        print(f"\n[1/4] Creating virtual environment at {venv_path}...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
            print("Virtual environment created.")
        except subprocess.CalledProcessError:
            print("Error: Failed to create venv. Make sure you have 'venv' module installed.")
            sys.exit(1)
    else:
        print(f"\n[1/4] Found existing virtual environment at {venv_path}")

    # 2. Upgrade pip inside venv
    print("\n[2/4] Upgrading pip...")
    run_command([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])

    # 3. Install dependencies
    if req_path.exists():
        print(f"\n[3/4] Installing dependencies from {REQUIREMENTS_FILE}...")
        # Use --no-cache-dir to avoid using cached wheels for wrong python versions
        run_command([
            str(venv_python), "-m", "pip", "install", 
            "-r", str(req_path),
            "--no-cache-dir" 
        ])
    else:
        print(f"Warning: {REQUIREMENTS_FILE} not found!")

    # 4. Special Handling for DirectML (AMD GPU)
    print("\n[4/4] Verifying DirectML support...")
    try:
        subprocess.check_call([
            str(venv_python), "-c", "import torch_directml"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("torch-directml is already installed.")
    except subprocess.CalledProcessError:
        print("Installing torch-directml for AMD GPU support...")
        run_command([
            str(venv_python), "-m", "pip", "install", "torch-directml"
        ], exit_on_error=False)

    print("\n" + "=" * 60)
    print(" SETUP COMPLETE!")
    print("=" * 60)
    print(f"Interpreter: {venv_python}")
    print("\nYou can now run the application using 'run_gui.bat'")

if __name__ == "__main__":
    main()
