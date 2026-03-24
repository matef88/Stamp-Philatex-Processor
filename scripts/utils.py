"""
Stamp Detection Claude - Shared Utilities
Common helper functions used across all scripts.
"""

import os
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import Union, List, Optional, Dict, Any


def is_frozen() -> bool:
    """Check if running as a PyInstaller frozen executable."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    Works whether called from scripts/ or project root,
    and supports PyInstaller frozen executable.
    """
    # Check if running as PyInstaller executable
    if is_frozen():
        # In onedir mode, sys.executable is the exe file
        # We want the directory containing the exe
        return Path(sys.executable).parent

    current_file = Path(__file__).resolve()

    # If we're in scripts/, go up one level
    if current_file.parent.name == 'scripts':
        return current_file.parent.parent

    # Otherwise assume we're at root
    return current_file.parent


def get_internal_path() -> Path:
    """
    Returns the path to internal bundled resources (for frozen exe).
    In development, returns project root.
    In frozen exe, returns _MEIPASS (where PyInstaller extracts files).
    """
    if is_frozen():
        return Path(sys._MEIPASS)
    return get_project_root()


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to a resource, works for dev and frozen exe.

    Args:
        relative_path: Path relative to project root (e.g., 'assets/texture.jpg')

    Returns:
        Absolute path to the resource
    """
    if is_frozen():
        # In frozen mode, check _MEIPASS first (bundled), then exe directory (runtime)
        meipass_path = Path(sys._MEIPASS) / relative_path
        if meipass_path.exists():
            return meipass_path
        # Fallback to exe directory for runtime files
        return Path(sys.executable).parent / relative_path
    return get_project_root() / relative_path


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads the YAML configuration file.

    Args:
        config_path: Optional path to config file. Defaults to project root/config.yaml

    Returns:
        Dictionary containing configuration
    """
    if config_path is None:
        # Use get_resource_path for frozen exe compatibility
        config_path = get_resource_path("config.yaml")
    else:
        config_path = Path(config_path)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)


def setup_logging(
    name: str = "stamp_detection",
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Sets up a logger with console and optional file output.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file
        log_format: Optional custom format string

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    logger.setLevel(level_map.get(level.upper(), logging.INFO))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def ensure_dirs(paths: Union[str, Path, List[Union[str, Path]]]) -> None:
    """
    Ensures that directories exist, creating them if necessary.

    Args:
        paths: Single path or list of paths to create
    """
    if isinstance(paths, (str, Path)):
        paths = [paths]

    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def get_timestamp() -> str:
    """
    Returns current timestamp as formatted string.
    Useful for unique file naming.

    Returns:
        Timestamp string in format YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_image_files(
    directory: Union[str, Path],
    recursive: bool = True,
    formats: Optional[List[str]] = None
) -> List[Path]:
    """
    Gets all image files from a directory.

    Args:
        directory: Directory to search
        recursive: Whether to search subdirectories
        formats: List of extensions to include (e.g., ['.jpg', '.png'])
                 If None, uses common image formats

    Returns:
        List of Path objects for found images
    """
    if formats is None:
        formats = ['.jpg', '.jpeg', '.png', '.heic', '.heif', '.bmp', '.tiff', '.webp']

    # Normalize extensions to lowercase with dot
    formats = [f.lower() if f.startswith('.') else f'.{f.lower()}' for f in formats]

    directory = Path(directory)
    image_files = []

    if recursive:
        for ext in formats:
            # Case-insensitive glob
            image_files.extend(directory.rglob(f'*{ext}'))
            image_files.extend(directory.rglob(f'*{ext.upper()}'))
    else:
        for ext in formats:
            image_files.extend(directory.glob(f'*{ext}'))
            image_files.extend(directory.glob(f'*{ext.upper()}'))

    # Remove duplicates and sort
    image_files = sorted(set(image_files))

    return image_files


def convert_heic_to_jpg(heic_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None, quality: int = 100) -> Path:
    """
    Converts HEIC/HEIF image to JPG format with maximum quality.
    Requires pillow-heif package.

    Args:
        heic_path: Path to HEIC file
        output_path: Optional output path. If None, uses same name with .jpg extension
        quality: JPEG quality (1-100), default 100 for maximum quality

    Returns:
        Path to converted JPG file

    Raises:
        ImportError: If pillow-heif is not installed
        RuntimeError: If conversion fails
    """
    try:
        from PIL import Image
        import pillow_heif

        # Register HEIF opener with PIL
        pillow_heif.register_heif_opener()

        heic_path = Path(heic_path)

        if output_path is None:
            output_path = heic_path.with_suffix('.jpg')
        else:
            output_path = Path(output_path)

        # Open and convert HEIC image
        with Image.open(heic_path) as img:
            # Convert color mode to RGB if it has alpha (RGBA, LA, P modes)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            # Save as JPEG with maximum quality settings
            # quality: JPEG quality level (100 = maximum)
            # optimize: False to prevent quality loss from optimization
            # subsampling: 0 for best quality (4:4:4 chroma subsampling)
            img.save(output_path, 'JPEG', quality=quality, optimize=False, subsampling=0)

        return output_path

    except ImportError:
        raise ImportError("pillow-heif package required for HEIC support. Install with: pip install pillow-heif")
    except Exception as e:
        raise RuntimeError(f"Failed to convert HEIC file: {e}")


def batch_convert_heic_to_jpg(
    directory: Union[str, Path],
    delete_heic: bool = False,
    quality: int = 95,
    logger: Optional[logging.Logger] = None
) -> tuple[list[Path], list[Path]]:
    """
    Batch convert all HEIC/HEIF files in a directory to JPG.

    This is a preprocessing step that ensures all images are in a standard format
    before detection and avoids duplicate processing of HEIC+JPG pairs.

    Safety features:
    - Validates JPG is readable before deleting HEIC
    - Cleans up partial JPGs on conversion failure
    - Never deletes HEIC until JPG is verified

    Args:
        directory: Directory containing HEIC files
        delete_heic: If True, delete original HEIC files after successful conversion
        quality: JPEG quality (1-100), default 95 for high quality
        logger: Optional logger for progress messages

    Returns:
        Tuple of (converted_files, failed_files) as lists of Paths
    """
    from PIL import Image
    import pillow_heif

    # Register HEIF opener with PIL (do this once at the beginning)
    pillow_heif.register_heif_opener()

    directory = Path(directory)

    # Find all HEIC/HEIF files (case-insensitive)
    heic_files = []
    for ext in ['.heic', '.heif', '.HEIC', '.HEIF']:
        heic_files.extend(directory.glob(f'*{ext}'))

    if not heic_files:
        if logger:
            logger.debug(f"No HEIC files found in {directory}")
        return [], []

    converted = []
    failed = []

    if logger:
        logger.info(f"Found {len(heic_files)} HEIC files for conversion")

    for heic_path in heic_files:
        jpg_path = None
        try:
            jpg_path = heic_path.with_suffix('.jpg')

            # Check if JPG with same name already exists
            if jpg_path.exists():
                if logger:
                    logger.debug(f"JPG already exists, skipping: {jpg_path.name}")

                # If delete_heic is enabled, still delete the HEIC since valid JPG exists
                if delete_heic:
                    # Verify the existing JPG is readable before deleting HEIC
                    try:
                        with Image.open(jpg_path) as test_img:
                            test_img.verify()
                        heic_path.unlink()
                        if logger:
                            logger.info(f"Deleted HEIC (valid JPG exists): {heic_path.name}")
                    except Exception as verify_error:
                        if logger:
                            logger.warning(f"Existing JPG is invalid, keeping HEIC: {jpg_path.name}")

                continue  # Skip conversion since JPG exists

            # Convert HEIC to JPG (JPG doesn't exist yet)
            if logger:
                logger.info(f"Converting: {heic_path.name} -> {jpg_path.name}")

            # Open and convert HEIC image
            with Image.open(heic_path) as img:
                # Convert color mode to RGB if it has alpha (RGBA, LA, P modes)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Save as JPEG with maximum quality settings
                # quality: Configurable JPEG quality level
                # optimize: False to prevent quality loss from optimization
                # subsampling: 0 for best quality (4:4:4 chroma subsampling)
                img.save(jpg_path, 'JPEG', quality=quality, optimize=False, subsampling=0)

            # Validate the created JPG is readable before deleting original
            try:
                with Image.open(jpg_path) as test_img:
                    test_img.verify()  # Verify the image is valid

                # JPG is verified, safe to mark as converted
                converted.append(jpg_path)

                # Delete original HEIC only after JPG is validated
                if delete_heic:
                    heic_path.unlink()
                    if logger:
                        logger.debug(f"Deleted original HEIC: {heic_path.name}")

            except Exception as verify_error:
                # JPG verification failed, remove the bad JPG file
                if jpg_path and jpg_path.exists():
                    jpg_path.unlink()
                    if logger:
                        logger.error(f"Created JPG was invalid, removed: {jpg_path.name}")
                raise RuntimeError(f"JPG verification failed: {verify_error}")

        except Exception as e:
            # Conversion failed - clean up any partial JPG files
            if jpg_path and jpg_path.exists():
                try:
                    jpg_path.unlink()
                    if logger:
                        logger.debug(f"Cleaned up partial JPG: {jpg_path.name}")
                except Exception as cleanup_error:
                    if logger:
                        logger.warning(f"Failed to clean up partial JPG: {cleanup_error}")

            failed.append(heic_path)
            if logger:
                logger.error(f"Failed to convert {heic_path.name}: {e}")

    # Log all operations for debugging
    if logger:
        logger.info(f"HEIC conversion complete: {len(converted)} converted, {len(failed)} failed")
        if delete_heic and converted:
            logger.info(f"Deleted {len(converted)} original HEIC files after verification")

    return converted, failed


def get_device(preferred: str = "auto") -> str:
    """
    Determines the best available device for PyTorch/YOLO.

    Args:
        preferred: Preferred device ("auto", "cpu", "cuda", "directml", "mps")

    Returns:
        Device string for PyTorch
    """
    import torch

    if preferred == "auto":
        # Check CUDA (NVIDIA)
        if torch.cuda.is_available():
            return "cuda"

        # Check DirectML (AMD on Windows)
        try:
            import torch_directml
            return "privateuseone"  # DirectML device name in PyTorch
        except ImportError:
            pass

        # Check MPS (Apple Silicon)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"

        # Fallback to CPU
        return "cpu"

    elif preferred == "directml":
        try:
            import torch_directml
            return "privateuseone"
        except ImportError:
            print("Warning: DirectML not available. Falling back to CPU.", file=sys.stderr)
            return "cpu"

    elif preferred == "cuda":
        if torch.cuda.is_available():
            return "cuda"
        print("Warning: CUDA not available. Falling back to CPU.")
        return "cpu"

    elif preferred == "mps":
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        print("Warning: MPS not available. Falling back to CPU.")
        return "cpu"

    return "cpu"


def format_size(size_bytes: int) -> str:
    """
    Formats byte size to human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Formats duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


class ProgressTracker:
    """
    Tracks processing progress with ETA estimation.
    """

    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items to process
            description: Description for progress display
        """
        self.total = total
        self.description = description
        self.current = 0
        self.start_time = datetime.now()
        self.errors = []
        self.successes = 0

    def update(self, success: bool = True, error_msg: Optional[str] = None) -> None:
        """
        Update progress after processing an item.

        Args:
            success: Whether the item was processed successfully
            error_msg: Error message if not successful
        """
        self.current += 1
        if success:
            self.successes += 1
        elif error_msg:
            self.errors.append(error_msg)

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress statistics.

        Returns:
            Dictionary with progress info
        """
        elapsed = (datetime.now() - self.start_time).total_seconds()

        if self.current > 0:
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate if rate > 0 else 0
        else:
            rate = 0
            remaining = 0

        return {
            "current": self.current,
            "total": self.total,
            "percent": (self.current / self.total * 100) if self.total > 0 else 0,
            "elapsed": elapsed,
            "remaining": remaining,
            "rate": rate,
            "successes": self.successes,
            "errors": len(self.errors),
            "elapsed_str": format_duration(elapsed),
            "remaining_str": format_duration(remaining)
        }

    def get_summary(self) -> str:
        """
        Get summary string of processing.

        Returns:
            Summary string
        """
        progress = self.get_progress()
        return (
            f"{self.description}: {progress['successes']}/{progress['total']} successful "
            f"({progress['errors']} errors) in {progress['elapsed_str']}"
        )


if __name__ == "__main__":
    # Test utilities
    print("Testing utilities...")

    root = get_project_root()
    print(f"Project root: {root}")

    config = load_config()
    print(f"Config loaded: {list(config.keys())}")

    logger = setup_logging("test")
    logger.info("Logger test successful")

    device = get_device("auto")
    print(f"Best device: {device}")

    print("\nAll utilities working correctly!")
