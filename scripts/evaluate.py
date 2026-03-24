"""
Stamp Detection Claude - Model Evaluation Script
Evaluates trained model performance on validation/test sets.
"""

import os
import sys
import argparse
from pathlib import Path

from ultralytics import YOLO

try:
    from utils import load_config, setup_logging, get_project_root
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from scripts.utils import load_config, setup_logging, get_project_root


logger = setup_logging("evaluate")


def evaluate_model(split: str = 'val', verbose: bool = True):
    """
    Evaluate model performance on validation or test set.

    Args:
        split: Dataset split to evaluate ('val' or 'test')
        verbose: Print detailed metrics
    """
    config = load_config()
    project_root = get_project_root()

    # Find model
    model_path = project_root / config['paths']['model_weights']

    if not model_path.exists():
        logger.error(f"Model not found at {model_path}")
        logger.error("Please train a model first using: python scripts/train.py")
        return

    logger.info(f"Loading model from {model_path}")
    model = YOLO(str(model_path))

    # Find data.yaml
    data_yaml_path = project_root / config['paths']['dataset'] / 'data.yaml'

    if not data_yaml_path.exists():
        logger.error(f"data.yaml not found at {data_yaml_path}")
        logger.error("Please run training first or create data.yaml manually")
        return

    logger.info(f"Evaluating on {split} set...")

    # Run validation
    metrics = model.val(data=str(data_yaml_path), split=split, verbose=verbose)

    # Print results
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)

    # Box metrics (detection)
    if hasattr(metrics, 'box'):
        print(f"\nDetection Metrics:")
        print(f"  mAP50:     {metrics.box.map50:.4f}")
        print(f"  mAP50-95:  {metrics.box.map:.4f}")
        print(f"  Precision: {metrics.box.mp:.4f}")
        print(f"  Recall:    {metrics.box.mr:.4f}")

    # Segmentation metrics
    if hasattr(metrics, 'seg'):
        print(f"\nSegmentation Metrics:")
        print(f"  mAP50:     {metrics.seg.map50:.4f}")
        print(f"  mAP50-95:  {metrics.seg.map:.4f}")

    # Speed
    if hasattr(metrics, 'speed'):
        print(f"\nSpeed:")
        print(f"  Preprocess: {metrics.speed.get('preprocess', 0):.2f}ms")
        print(f"  Inference:  {metrics.speed.get('inference', 0):.2f}ms")
        print(f"  Postprocess: {metrics.speed.get('postprocess', 0):.2f}ms")

    print("="*60)

    # Check if metrics meet requirements
    print("\nRequirement Check:")
    req_map50 = 0.85
    req_precision = 0.85
    req_recall = 0.90

    if hasattr(metrics, 'box'):
        map50_pass = metrics.box.map50 >= req_map50
        prec_pass = metrics.box.mp >= req_precision
        recall_pass = metrics.box.mr >= req_recall

        print(f"  mAP50 >= {req_map50*100:.0f}%:     {'PASS' if map50_pass else 'FAIL'} ({metrics.box.map50*100:.1f}%)")
        print(f"  Precision >= {req_precision*100:.0f}%: {'PASS' if prec_pass else 'FAIL'} ({metrics.box.mp*100:.1f}%)")
        print(f"  Recall >= {req_recall*100:.0f}%:    {'PASS' if recall_pass else 'FAIL'} ({metrics.box.mr*100:.1f}%)")

    return metrics


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Evaluate trained model")
    parser.add_argument("--split", type=str, default="val",
                       choices=['val', 'test'],
                       help="Dataset split to evaluate")
    parser.add_argument("--quiet", action='store_true',
                       help="Reduce output verbosity")

    args = parser.parse_args()

    evaluate_model(args.split, verbose=not args.quiet)


if __name__ == "__main__":
    main()
