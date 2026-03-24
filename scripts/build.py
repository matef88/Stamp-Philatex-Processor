"""
Stamp Philatex Processor - PyInstaller Build Script
Creates a standalone Windows executable.
"""

import sys
import shutil
import os
from pathlib import Path

try:
    import PyInstaller.__main__
except ImportError:
    print("Error: PyInstaller not found. Please install it with 'pip install pyinstaller'")
    sys.exit(1)


def build():
    print("=" * 60)
    print("  Stamp Philatex Processor - Build Script")
    print("=" * 60)

    # Ensure we are in project root
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    print(f"Building from: {project_root}")
    os.chdir(project_root)

    # force clean
    clean()

    # Verify required files exist
    required_files = [
        project_root / 'run_gui.py',
        project_root / 'config.yaml',
        project_root / 'gui' / 'main_window.py',
        project_root / 'scripts' / 'utils.py',
    ]

    for f in required_files:
        if not f.exists():
            print(f"[ERROR] Required file not found: {f}")
            sys.exit(1)

    # Load configuration
    config_path = project_root / 'config.yaml'
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("[OK] Config loaded")
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        sys.exit(1)

    # Get model path from config
    model_rel_path = config.get('paths', {}).get('model_weights', 'models/stamp_detector_seg/weights/best.pt')
    model_path = project_root / model_rel_path
    
    print(f"Target Model: {model_path}")

    # Check for model file
    if not model_path.exists():
        print(f"[ERROR] Model file not found: {model_path}")
        print("          Please check 'paths.model_weights' in config.yaml")
        sys.exit(1)
    else:
        include_model = True
        print(f"[OK] Model file found and will be included.")

    # Clean previous builds
    print("\nCleaning previous builds...")

    import time
    for folder in ["build", "dist"]:
        folder_path = project_root / folder
        if folder_path.exists():
            for attempt in range(3):
                try:
                    shutil.rmtree(folder_path)
                    break
                except PermissionError as e:
                    print(f"  [WARN] Cannot remove {folder}/ (attempt {attempt+1}/3): {e}")
                    if attempt < 2:
                        print("  Waiting 2 seconds and retrying...")
                        time.sleep(2)
                    else:
                        print(f"  [WARN] Proceeding anyway - {folder}/ may have stale files")
                except Exception as e:
                    print(f"  [WARN] Error removing {folder}/: {e}")

    # Build data files list
    # Format: 'source;destination' (Windows uses ;)
    separator = ';' if sys.platform == 'win32' else ':'

    datas = [
        f'{project_root / "config.yaml"}{separator}.',
        f'{project_root / "gui"}{separator}gui',
        f'{project_root / "scripts"}{separator}scripts',
    ]

    # Add assets if exists
    assets_dir = project_root / "assets"
    if assets_dir.exists():
        datas.append(f'{assets_dir}{separator}assets')

    # Add GUI resources
    gui_resources = project_root / "gui" / "resources"
    if gui_resources.exists():
        datas.append(f'{gui_resources}{separator}gui/resources')

    # Add model if exists
    if include_model:
        # We place it in the same relative path structure inside the exe
        # Logic: We want 'models/...' to mirror. 
        # So we take the parent folder of the weights as destination? 
        # Actually simplest is just to copy it to where the code expects it.
        # The code expects: project_root / 'models' / ...
        # logic in config is "models/stamp_detector_seg/weights/best.pt"
        
        # We need to calculate the destination directory structure
        # If model_rel_path is "models/foo/bar.pt", we want it at "models/foo/"
        
        # However, PyInstaller add-data format is "source;dest"
        # Dest is the FOLDER containing the file.
        
        rel_path = Path(model_rel_path)
        dest_folder = rel_path.parent # e.g. models/stamp_detector_seg/weights
        
        datas.append(f'{model_path}{separator}{dest_folder}')

    # Output to Desktop to avoid Google Drive sync issues
    desktop_path = Path.home() / "Desktop" / "StampPhilatexProcessor_Build"
    build_dir = desktop_path / "build"
    dist_dir = desktop_path / "dist"

    # Clean previous desktop builds
    if desktop_path.exists():
        try:
            shutil.rmtree(desktop_path)
        except Exception as e:
            print(f"  [WARN] Could not clean previous build: {e}")

    # Create output directory
    desktop_path.mkdir(parents=True, exist_ok=True)

    print(f"\n[OUTPUT LOCATION]")
    print(f"  Desktop folder: {desktop_path}")
    print(f"  Build directory: {build_dir}")
    print(f"  Dist directory: {dist_dir}")

    # Build arguments
    args = [
        str(project_root / 'run_gui.py'),
        '--noconfirm',
        '--onedir',
        '--windowed',
        '--name=StampPhilatexProcessor',
        f'--workpath={build_dir}',
        f'--distpath={dist_dir}',
        f'--specpath={project_root}',

        # Add icon if exists
        # f'--icon={project_root / "assets" / "icon.ico"}',

        # Hidden imports - all required modules
        '--hidden-import=ultralytics',
        '--hidden-import=ultralytics.nn',
        '--hidden-import=ultralytics.nn.tasks',
        '--hidden-import=ultralytics.utils',
        '--hidden-import=ultralytics.engine',
        '--hidden-import=ultralytics.engine.predictor',
        '--hidden-import=ultralytics.engine.results',
        '--hidden-import=ultralytics.models',
        '--hidden-import=ultralytics.models.yolo',
        '--hidden-import=ultralytics.data',
        '--hidden-import=pandas',
        '--hidden-import=yaml',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=torch',
        '--hidden-import=torchvision',
        '--hidden-import=torchvision.transforms',
        '--hidden-import=torchvision.ops',
        '--hidden-import=imagehash',
        '--hidden-import=pillow_heif',
        '--hidden-import=sqlite3',
        '--hidden-import=torch_directml',
        '--hidden-import=tqdm',
        '--hidden-import=scipy',
        '--hidden-import=scipy.ndimage',
        '--hidden-import=matplotlib',
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.sip',

        # Exclude unnecessary modules to reduce warnings and size
        '--exclude-module=tensorboard',
        '--exclude-module=torch.utils.tensorboard',
        '--exclude-module=test',
        '--exclude-module=tests',
        # Note: unittest is needed by torch/ultralytics, do NOT exclude
        '--exclude-module=IPython',
        '--exclude-module=notebook',

        # Collect all from ultralytics (includes configs, models, etc.)
        '--collect-all=ultralytics',
        '--collect-all=torch_directml',
        '--collect-all=scipy',  # CRITICAL FIX: Include ALL scipy binaries (.pyd files)

        # Collect submodules
        '--collect-submodules=ultralytics',
        '--collect-submodules=torch',
        '--collect-submodules=torchvision',
        '--collect-submodules=scipy',  # Include all scipy submodules

        # Copy metadata
        '--copy-metadata=ultralytics',
        '--copy-metadata=torch',
        '--copy-metadata=torchvision',
        '--copy-metadata=tqdm',
        '--copy-metadata=numpy',
        '--copy-metadata=pillow_heif',
        '--copy-metadata=scipy',  # Add scipy metadata
    ]

    # Add all data files
    for data in datas:
        args.append(f'--add-data={data}')

    print("\nPyInstaller arguments:")
    for arg in args:
        if arg.startswith('--add-data') or arg.startswith('--hidden-import'):
            print(f"  {arg}")

    print("\nRunning PyInstaller... (this may take several minutes)")

    try:
        PyInstaller.__main__.run(args)

        print("\n" + "=" * 60)
        print("  Build Complete!")
        print("=" * 60)

        # Check dist location
        exe_folder = dist_dir / 'StampPhilatexProcessor'
        exe_path = exe_folder / 'StampPhilatexProcessor.exe'

        if exe_path.exists():
            print(f"\nExecutable created: {exe_path}")

            # Get size
            total_size = sum(
                f.stat().st_size for f in exe_folder.rglob('*') if f.is_file()
            )
            print(f"Total size: {total_size / (1024*1024):.1f} MB")

            # Create ZIP file
            print("\nCreating ZIP archive...")
            zip_path = desktop_path / "StampDetectionClaude_Portable.zip"
            shutil.make_archive(
                str(zip_path.with_suffix('')),  # Remove .zip as make_archive adds it
                'zip',
                dist_dir,
                'StampDetectionClaude'
            )
            zip_size = zip_path.stat().st_size / (1024*1024)
            print(f"ZIP created: {zip_path} ({zip_size:.1f} MB)")

            # Clean up build folder (keep dist and zip)
            print("\nCleaning up build files...")
            shutil.rmtree(build_dir, ignore_errors=True)

            print("\n" + "=" * 60)
            print("  OUTPUT FILES (on Desktop)")
            print("=" * 60)
            print(f"\n  [FOLDER] {exe_folder}")
            print(f"           Run: StampPhilatexProcessor.exe")
            print(f"\n  [ZIP]    {zip_path}")
            print(f"           Portable version for distribution")
            print(f"\n  Location: {desktop_path}")

        else:
            print("\n[WARNING] Executable not found at expected location!")
            print(f"  Expected: {exe_path}")

    except Exception as e:
        print(f"\n[ERROR] Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def clean():
    """Clean build artifacts."""
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    print("Cleaning build artifacts...")
    shutil.rmtree(project_root / "build", ignore_errors=True)
    shutil.rmtree(project_root / "dist", ignore_errors=True)

    # Remove .spec file
    spec_file = project_root / "StampPhilatexProcessor.spec"
    if spec_file.exists():
    if spec_file.exists():
        spec_file.unlink()

    print("Clean complete!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean()
    else:
        build()
