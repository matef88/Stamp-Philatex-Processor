"""
Stamp Philatex Processor - Model Training Script
Trains YOLOv8 segmentation model for stamp detection.
Optimized for AMD GPU via DirectML.
"""

import os
import sys
import argparse
from pathlib import Path
import yaml

from ultralytics import YOLO

try:
    from utils import load_config, setup_logging, get_project_root, ensure_dirs
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from scripts.utils import load_config, setup_logging, get_project_root, ensure_dirs


logger = setup_logging("train")


def create_data_yaml(config: dict) -> Path:
    """
    Create or update data.yaml for YOLO training.

    Args:
        config: Project configuration

    Returns:
        Path to data.yaml file
    """
    project_root = get_project_root()
    dataset_path = project_root / config['paths']['dataset']
    data_yaml_path = dataset_path / 'data.yaml'

    # Create data configuration
    data_config = {
        'path': str(dataset_path.absolute()),
        'train': 'train/images',
        'val': 'valid/images',
        'names': {
            0: 'stamp'
        },
        'nc': 1  # number of classes
    }

    # Write data.yaml
    with open(data_yaml_path, 'w') as f:
        yaml.dump(data_config, f, default_flow_style=False)

    logger.info(f"Created data.yaml at {data_yaml_path}")
    return data_yaml_path


def check_dataset(dataset_path: Path) -> dict:
    """
    Check dataset structure and count images.

    Args:
        dataset_path: Path to dataset directory

    Returns:
        Dictionary with dataset statistics
    """
    stats = {
        'train_images': 0,
        'val_images': 0,
        'train_labels': 0,
        'val_labels': 0,
        'valid': False
    }

    train_images = dataset_path / 'train' / 'images'
    val_images = dataset_path / 'valid' / 'images'
    train_labels = dataset_path / 'train' / 'labels'
    val_labels = dataset_path / 'valid' / 'labels'

    if train_images.exists():
        stats['train_images'] = len(list(train_images.glob('*.[jJ][pP][gG]')) +
                                    list(train_images.glob('*.[pP][nN][gG]')))

    if val_images.exists():
        stats['val_images'] = len(list(val_images.glob('*.[jJ][pP][gG]')) +
                                  list(val_images.glob('*.[pP][nN][gG]')))

    if train_labels.exists():
        stats['train_labels'] = len(list(train_labels.glob('*.txt')))

    if val_labels.exists():
        stats['val_labels'] = len(list(val_labels.glob('*.txt')))

    # Check if valid
    stats['valid'] = (
        stats['train_images'] > 0 and
        stats['val_images'] > 0 and
        stats['train_labels'] > 0
    )

    return stats


def train_model(
    epochs: int = 100,
    batch_size: int = 16,
    img_size: int = 640,
    device: str = 'auto',
    resume: bool = False
):
    """
    Train the YOLOv8 segmentation model.

    Args:
        epochs: Number of training epochs
        batch_size: Batch size (adjust for GPU memory)
        img_size: Training image size
        device: Device to use ('auto', 'cpu', '0' for GPU)
        resume: Resume from last checkpoint
    """
    config = load_config()
    project_root = get_project_root()

    # Check dataset
    dataset_path = project_root / config['paths']['dataset']
    stats = check_dataset(dataset_path)

    logger.info("Dataset Statistics:")
    logger.info(f"  Training images: {stats['train_images']}")
    logger.info(f"  Validation images: {stats['val_images']}")
    logger.info(f"  Training labels: {stats['train_labels']}")
    logger.info(f"  Validation labels: {stats['val_labels']}")

    if not stats['valid']:
        logger.error("Dataset not valid! Please check:")
        logger.error("  - dataset/train/images/ has images")
        logger.error("  - dataset/valid/images/ has images")
        logger.error("  - dataset/train/labels/ has .txt label files")
        logger.error("  - dataset/valid/labels/ has .txt label files")
        return

    # Create data.yaml
    data_yaml_path = create_data_yaml(config)

    # Determine device
    if device == 'auto':
        import torch
        if torch.cuda.is_available():
            device = '0'
            logger.info("Using CUDA GPU")
        else:
            try:
                import torch_directml
                device = 'cpu'  # DirectML uses CPU in YOLO but accelerates internally
                logger.info("DirectML available (AMD GPU acceleration)")
            except ImportError:
                device = 'cpu'
                logger.info("Using CPU")
    else:
        logger.info(f"Using device: {device}")

    # Load base model
    base_model = config.get('training', {}).get('base_model', 'yolov8n-seg.pt')
    logger.info(f"Loading base model: {base_model}")
    model = YOLO(base_model)

    # Training output directory
    models_dir = project_root / config['paths']['models']
    ensure_dirs([models_dir])

    # Start training
    logger.info(f"Starting training for {epochs} epochs...")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  Image size: {img_size}")

    # Get augmentation settings
    aug_config = config.get('training', {}).get('augmentation', {})

    try:
        results = model.train(
            data=str(data_yaml_path),
            epochs=epochs,
            batch=batch_size,
            imgsz=img_size,
            device=device,
            project=str(models_dir),
            name='stamp_detector_seg',
            exist_ok=True,
            resume=resume,

            # Augmentation
            flipud=aug_config.get('vertical_flip', 0.0),
            fliplr=0.5 if aug_config.get('horizontal_flip', True) else 0.0,
            degrees=aug_config.get('rotation', 15),
            scale=aug_config.get('scale', 0.2),
            mosaic=1.0 if aug_config.get('mosaic', True) else 0.0,
            mixup=aug_config.get('mixup', 0.1),

            # Performance
            workers=4,
            patience=50,  # Early stopping
            save=True,
            save_period=10,  # Save checkpoint every 10 epochs

            # Logging
            verbose=True,
            plots=True
        )

        logger.info("Training complete!")
        logger.info(f"Best model saved to: {models_dir / 'stamp_detector_seg' / 'weights' / 'best.pt'}")

        # Copy best model to expected location
        best_model_src = models_dir / 'stamp_detector_seg' / 'weights' / 'best.pt'
        if best_model_src.exists():
            import shutil
            target_dir = models_dir / 'stamp_detector_seg' / 'weights'
            ensure_dirs([target_dir])
            target_dir = models_dir / 'stamp_detector_seg' / 'weights'
            ensure_dirs([target_dir])
            logger.info(f"Model saved at: {target_dir / 'best.pt'}")

        # Sanity Check
        logger.info("Running post-training sanity check...")
        try:
            check_model = YOLO(str(models_dir / 'stamp_detector_seg' / 'weights' / 'best.pt'))
            # Try predicting on a dummy image (zeros) just to check loading and inference pass
            dummy_img = ['https://ultralytics.com/images/bus.jpg'] # Use standard test image or random
            # Actually better to use a real image from val set if available
            dataset_path = project_root / config['paths']['dataset']
            val_images = list((dataset_path / 'valid' / 'images').glob('*.jpg'))
            if val_images:
                check_model.predict(str(val_images[0]), verbose=False)
                logger.info("Sanity check passed: Model loaded and ran inference successfully.")
            else:
                logger.warning("Sanity check skipped: No validation images found.")
        except Exception as e:
            logger.error(f"Sanity check failed: {e}")
            logger.warning("The model may be corrupted or incompatible.")

    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Train YOLOv8 segmentation model for stamp detection")

    parser.add_argument("--epochs", type=int, default=100,
                       help="Number of training epochs (default: 100)")
    parser.add_argument("--batch", type=int, default=16,
                       help="Batch size (default: 16, reduce if out of memory)")
    parser.add_argument("--img-size", type=int, default=640,
                       help="Training image size (default: 640)")
    parser.add_argument("--device", type=str, default='auto',
                       help="Device to use: 'auto', 'cpu', '0' for GPU")
    parser.add_argument("--resume", action='store_true',
                       help="Resume from last checkpoint")

    args = parser.parse_args()

    train_model(
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.img_size,
        device=args.device,
        resume=args.resume
    )


if __name__ == "__main__":
    main()
