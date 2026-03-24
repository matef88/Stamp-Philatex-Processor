"""
Stamp Philatex Processor - Environment Validation Script
Verifies all dependencies are correctly installed and configured.
"""

import sys
import os
from pathlib import Path


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")


def print_result(name: str, success: bool, detail: str = "") -> bool:
    """Print a test result."""
    status = "[OK]" if success else "[FAIL]"
    color_start = "\033[92m" if success else "\033[91m"
    color_end = "\033[0m"

    if detail:
        print(f"  {color_start}{status}{color_end} {name}: {detail}")
    else:
        print(f"  {color_start}{status}{color_end} {name}")

    return success


def check_import(module_name: str, pip_name: str = None, version_attr: str = "__version__") -> bool:
    """
    Check if a module can be imported and get its version.

    Args:
        module_name: Python module name
        pip_name: pip package name (if different)
        version_attr: Attribute containing version string

    Returns:
        True if import successful
    """
    if pip_name is None:
        pip_name = module_name

    try:
        module = __import__(module_name)
        version = getattr(module, version_attr, "unknown")
        return print_result(pip_name, True, f"v{version}")
    except ImportError as e:
        return print_result(pip_name, False, str(e))


def check_directory(path: str, create: bool = False) -> bool:
    """
    Check if a directory exists.

    Args:
        path: Directory path
        create: Whether to create if missing

    Returns:
        True if exists or created
    """
    path_obj = Path(path)
    exists = path_obj.is_dir()

    if not exists and create:
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
            return print_result(f"Directory '{path}'", True, "created")
        except Exception as e:
            return print_result(f"Directory '{path}'", False, str(e))

    return print_result(f"Directory '{path}'", exists, "exists" if exists else "missing")


def check_file(path: str) -> bool:
    """Check if a file exists."""
    exists = Path(path).is_file()
    return print_result(f"File '{path}'", exists, "found" if exists else "not found")


def check_gpu() -> dict:
    """Check available GPU/acceleration options."""
    result = {
        'cuda': False,
        'directml': False,
        'mps': False,
        'device': 'cpu'
    }

    # Check CUDA (NVIDIA)
    try:
        import torch
        if torch.cuda.is_available():
            result['cuda'] = True
            result['device'] = 'cuda'
            gpu_name = torch.cuda.get_device_name(0)
            print_result("CUDA (NVIDIA)", True, gpu_name)
        else:
            print_result("CUDA (NVIDIA)", False, "not available")
    except ImportError:
        print_result("CUDA (NVIDIA)", False, "torch not installed")

    # Check DirectML (AMD on Windows)
    try:
        import torch_directml
        result['directml'] = True
        if result['device'] == 'cpu':
            result['device'] = 'directml'
        print_result("DirectML (AMD)", True, "available")
    except ImportError:
        print_result("DirectML (AMD)", False, "torch-directml not installed")

    # Check MPS (Apple Silicon)
    try:
        import torch
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            result['mps'] = True
            if result['device'] == 'cpu':
                result['device'] = 'mps'
            print_result("MPS (Apple)", True, "available")
        else:
            print_result("MPS (Apple)", False, "not available")
    except Exception:
        print_result("MPS (Apple)", False, "not available")

    return result


def check_heic_support() -> bool:
    """Check if HEIC/HEIF support is available."""
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        return print_result("HEIC Support", True, "pillow-heif registered")
    except ImportError:
        return print_result("HEIC Support", False, "pillow-heif not installed")


def main():
    """Run all environment checks."""
    print_header("Stamp Philatex Processor - Environment Check")

    all_good = True

    # Core Libraries
    print("\n[Core Libraries]")
    all_good &= check_import("cv2", "opencv-python", "version")
    all_good &= check_import("torch", "torch")
    all_good &= check_import("ultralytics", "ultralytics")
    all_good &= check_import("numpy", "numpy")
    all_good &= check_import("yaml", "pyyaml", "version")
    all_good &= check_import("PIL", "pillow")

    # GUI
    print("\n[GUI Libraries]")
    all_good &= check_import("PyQt6", "PyQt6")

    # Duplicate Detection
    print("\n[Duplicate Detection]")
    all_good &= check_import("imagehash", "imagehash")

    # HEIC Support
    print("\n[iPhone Support]")
    check_heic_support()  # Not critical

    # GPU/Acceleration
    print("\n[Hardware Acceleration]")
    gpu_info = check_gpu()

    # Project Directories
    print("\n[Project Directories]")

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    required_dirs = [
        "dataset",
        "dataset/images",
        "dataset/labels",
        "raw_data",
        "output",
        "output/crops",
        "output/visuals",
        "output/reports",
        "models",
        "database",
        "assets"
    ]

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        check_directory(str(dir_path), create=True)

    # Config File
    print("\n[Configuration]")
    config_path = project_root / "config.yaml"
    config_exists = check_file(str(config_path))

    if config_exists:
        try:
            from utils import load_config
            config = load_config(str(config_path))
            print_result("Config parsing", True, f"{len(config)} sections loaded")
        except Exception as e:
            print_result("Config parsing", False, str(e))
            all_good = False

    # Summary
    print_header("Summary")

    print(f"\n  Python Version: {sys.version.split()[0]}")
    print(f"  Platform: {sys.platform}")
    print(f"  Best Device: {gpu_info['device']}")

    if all_good:
        print("\n  \033[92mSUCCESS: Environment is ready!\033[0m")
        print(f"\n  Next steps:")
        print(f"    1. Add your stamp images to: {project_root / 'raw_data'}")
        print(f"    2. Run: python scripts/process_stamps.py --input raw_data")
        print(f"    3. Check output in: {project_root / 'output' / 'crops'}")
    else:
        print("\n  \033[91mWARNING: Some checks failed.\033[0m")
        print(f"\n  To fix missing dependencies, run:")
        print(f"    pip install -r requirements.txt")

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
