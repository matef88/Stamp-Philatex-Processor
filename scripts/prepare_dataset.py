"""
Stamp Philatex Processor - Dataset Preparation Script
Organizes images and labels into YOLO training format.
"""

import os
import sys
import shutil
import random
import argparse
from pathlib import Path
from tqdm import tqdm

try:
    from utils import load_config, setup_logging, get_project_root, ensure_dirs
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from scripts.utils import load_config, setup_logging, get_project_root, ensure_dirs


logger = setup_logging("prepare_dataset")


def split_dataset(
    source_dir: str,
    dest_dir: str = None,
    split_ratio: float = 0.8,
    copy_files: bool = True,
    seed: int = 42
):
    """
    Split images and labels into train/val folders for YOLO training.

    Expects source_dir to contain:
    - Images (.jpg, .jpeg, .png)
    - Labels (.txt) with same base name as images

    Creates structure:
    dest_dir/
      images/train/
      images/val/
      labels/train/
      labels/val/

    Args:
        source_dir: Directory containing images and labels
        dest_dir: Output dataset directory
        split_ratio: Ratio of training data (0.8 = 80% train, 20% val)
        copy_files: If True, copy files. If False, move files.
        seed: Random seed for reproducibility
    """
    config = load_config()
    project_root = get_project_root()

    # Set random seed
    random.seed(seed)

    # Paths
    source_path = Path(source_dir)
    if dest_dir:
        dest_path = Path(dest_dir)
    else:
        dest_path = project_root / config['paths']['dataset']

    # Create directory structure
    dirs = [
        dest_path / 'images' / 'train',
        dest_path / 'images' / 'val',
        dest_path / 'labels' / 'train',
        dest_path / 'labels' / 'val'
    ]
    ensure_dirs(dirs)

    # Supported extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}

    # Find all images
    logger.info(f"Scanning {source_path} for images...")
    image_files = []

    for root, _, files in os.walk(source_path):
        for f in files:
            if Path(f).suffix.lower() in image_extensions:
                image_files.append(Path(root) / f)

    if not image_files:
        logger.error("No images found in source directory!")
        return

    logger.info(f"Found {len(image_files)} images")

    # Check for labels
    images_with_labels = []
    images_without_labels = []

    for img_path in image_files:
        # Look for label file
        label_path = img_path.with_suffix('.txt')

        # Also check in parallel 'labels' folder
        if not label_path.exists():
            parent = img_path.parent
            if parent.name == 'images':
                alt_label_dir = parent.parent / 'labels'
                alt_label_path = alt_label_dir / (img_path.stem + '.txt')
                if alt_label_path.exists():
                    label_path = alt_label_path

        if label_path.exists():
            images_with_labels.append((img_path, label_path))
        else:
            images_without_labels.append(img_path)

    logger.info(f"Images with labels: {len(images_with_labels)}")
    if images_without_labels:
        logger.warning(f"Images WITHOUT labels: {len(images_without_labels)}")
        logger.warning("  (These will be skipped)")

    if not images_with_labels:
        logger.error("No images with matching labels found!")
        return

    # Shuffle and split
    random.shuffle(images_with_labels)
    split_idx = int(len(images_with_labels) * split_ratio)

    train_files = images_with_labels[:split_idx]
    val_files = images_with_labels[split_idx:]

    logger.info(f"Split: {len(train_files)} train, {len(val_files)} val")

    # Copy/move files
    def process_files(file_list, img_dest, lbl_dest, desc):
        for img_path, lbl_path in tqdm(file_list, desc=desc):
            # Handle image
            img_dest_path = img_dest / img_path.name
            if copy_files:
                shutil.copy2(img_path, img_dest_path)
            else:
                shutil.move(str(img_path), str(img_dest_path))

            # Handle label
            lbl_dest_path = lbl_dest / (img_path.stem + '.txt')
            if copy_files:
                shutil.copy2(lbl_path, lbl_dest_path)
            else:
                shutil.move(str(lbl_path), str(lbl_dest_path))

    process_files(
        train_files,
        dest_path / 'images' / 'train',
        dest_path / 'labels' / 'train',
        "Training set"
    )

    process_files(
        val_files,
        dest_path / 'images' / 'val',
        dest_path / 'labels' / 'val',
        "Validation set"
    )

    logger.info("Dataset preparation complete!")
    logger.info(f"Output: {dest_path}")
    logger.info(f"  - Training: {len(train_files)} images")
    logger.info(f"  - Validation: {len(val_files)} images")


def validate_labels(dataset_dir: str):
    """
    Validate YOLO label files for correct format.

    Args:
        dataset_dir: Path to dataset directory
    """
    dataset_path = Path(dataset_dir)
    issues = []

    for split in ['train', 'val']:
        labels_dir = dataset_path / 'labels' / split

        if not labels_dir.exists():
            continue

        for label_file in labels_dir.glob('*.txt'):
            with open(label_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split()

                    # Check minimum parts (class + at least 3 points for polygon)
                    if len(parts) < 7:  # class + 3 points (x,y pairs)
                        issues.append(f"{label_file.name}:{line_num} - Too few values")
                        continue

                    try:
                        class_id = int(parts[0])
                        if class_id != 0:
                            issues.append(f"{label_file.name}:{line_num} - Class ID should be 0, got {class_id}")

                        # Check coordinates are normalized (0-1)
                        coords = [float(x) for x in parts[1:]]
                        for i, coord in enumerate(coords):
                            if coord < 0 or coord > 1:
                                issues.append(f"{label_file.name}:{line_num} - Coordinate {i} out of range: {coord}")
                                break

                    except ValueError as e:
                        issues.append(f"{label_file.name}:{line_num} - Invalid format: {e}")

    if issues:
        logger.warning(f"Found {len(issues)} label issues:")
        for issue in issues[:20]:  # Show first 20
            logger.warning(f"  {issue}")
        if len(issues) > 20:
            logger.warning(f"  ... and {len(issues) - 20} more")
    else:
        logger.info("All labels validated successfully!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Prepare dataset for YOLO training")

    parser.add_argument("--source", type=str, default="raw_data",
                       help="Source directory with images and labels")
    parser.add_argument("--dest", type=str, default=None,
                       help="Destination dataset directory")
    parser.add_argument("--split", type=float, default=0.8,
                       help="Train split ratio (default: 0.8)")
    parser.add_argument("--move", action='store_true',
                       help="Move files instead of copying")
    parser.add_argument("--validate", action='store_true',
                       help="Validate existing labels only")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.validate:
        dest = args.dest or str(get_project_root() / 'dataset')
        validate_labels(dest)
    else:
        split_dataset(
            args.source,
            args.dest,
            args.split,
            copy_files=not args.move,
            seed=args.seed
        )


if __name__ == "__main__":
    main()
