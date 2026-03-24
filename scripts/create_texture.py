"""
Stamp Philatex Processor - Texture Generator
Creates the green background texture used for stamp borders.
"""

import cv2
import numpy as np
import argparse
from pathlib import Path
import sys
import os

try:
    from utils import load_config, get_project_root, ensure_dirs
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from scripts.utils import load_config, get_project_root, ensure_dirs


def create_texture(
    width: int = 1000,
    height: int = 1000,
    color: tuple = (51, 112, 68),
    noise_level: int = 10,
    output_path: str = None
) -> np.ndarray:
    """
    Create a green noise texture.

    Args:
        width: Texture width in pixels
        height: Texture height in pixels
        color: BGR color tuple
        noise_level: Standard deviation for noise
        output_path: Optional path to save texture

    Returns:
        Numpy array with texture image
    """
    # Create base color image
    base_color = np.full((height, width, 3), color, dtype=np.uint8)

    # Add Gaussian noise for texture effect
    noise = np.random.normal(0, noise_level, (height, width, 3)).astype(np.int16)

    # Combine and clip to valid range
    texture = np.clip(base_color.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Save if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), texture)
        print(f"Texture saved to: {output_path}")

    return texture


def create_gradient_texture(
    width: int = 1000,
    height: int = 1000,
    color_start: tuple = (40, 100, 55),
    color_end: tuple = (60, 125, 80),
    noise_level: int = 8,
    output_path: str = None
) -> np.ndarray:
    """
    Create a gradient texture with noise.

    Args:
        width: Texture width
        height: Texture height
        color_start: Starting BGR color
        color_end: Ending BGR color
        noise_level: Noise standard deviation
        output_path: Optional output path

    Returns:
        Numpy array with gradient texture
    """
    # Create gradient
    gradient = np.zeros((height, width, 3), dtype=np.float32)

    for i in range(3):
        gradient[:, :, i] = np.linspace(
            color_start[i], color_end[i], height
        ).reshape(-1, 1)

    # Add noise
    noise = np.random.normal(0, noise_level, (height, width, 3))
    texture = np.clip(gradient + noise, 0, 255).astype(np.uint8)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), texture)
        print(f"Gradient texture saved to: {output_path}")

    return texture


def create_paper_texture(
    width: int = 1000,
    height: int = 1000,
    base_color: tuple = (51, 112, 68),
    output_path: str = None
) -> np.ndarray:
    """
    Create a paper-like texture with subtle variations.

    Args:
        width: Texture width
        height: Texture height
        base_color: BGR base color
        output_path: Optional output path

    Returns:
        Numpy array with paper texture
    """
    # Start with base color
    texture = np.full((height, width, 3), base_color, dtype=np.float32)

    # Add multiple noise layers for paper effect
    # Fine grain
    fine_noise = np.random.normal(0, 5, (height, width, 3))
    texture += fine_noise

    # Medium grain (blurred)
    medium_noise = np.random.normal(0, 10, (height, width, 3))
    medium_noise = cv2.GaussianBlur(medium_noise.astype(np.float32), (5, 5), 0)
    texture += medium_noise

    # Large variations (more blur)
    large_noise = np.random.normal(0, 8, (height, width, 3))
    large_noise = cv2.GaussianBlur(large_noise.astype(np.float32), (21, 21), 0)
    texture += large_noise

    # Clip and convert
    texture = np.clip(texture, 0, 255).astype(np.uint8)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), texture)
        print(f"Paper texture saved to: {output_path}")

    return texture


def main():
    """Generate textures based on config or arguments."""
    parser = argparse.ArgumentParser(description="Generate background textures")
    parser.add_argument("--width", type=int, default=1000, help="Texture width")
    parser.add_argument("--height", type=int, default=1000, help="Texture height")
    parser.add_argument("--type", choices=["simple", "gradient", "paper"],
                       default="simple", help="Texture type")
    parser.add_argument("--output", type=str, help="Output path")
    parser.add_argument("--preview", action="store_true", help="Show preview window")

    args = parser.parse_args()

    # Load config for color
    try:
        config = load_config()
        color = tuple(config.get('background', {}).get('color', [51, 112, 68]))
        noise_level = config.get('background', {}).get('noise_level', 10)
    except Exception:
        color = (51, 112, 68)
        noise_level = 10

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        project_root = get_project_root()
        output_path = project_root / "assets" / "green_texture.jpg"

    # Create texture based on type
    if args.type == "simple":
        texture = create_texture(
            args.width, args.height, color, noise_level, output_path
        )
    elif args.type == "gradient":
        texture = create_gradient_texture(
            args.width, args.height, output_path=output_path
        )
    elif args.type == "paper":
        texture = create_paper_texture(
            args.width, args.height, color, output_path
        )

    # Preview if requested
    if args.preview:
        cv2.imshow("Texture Preview", texture)
        print("Press any key to close preview...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
