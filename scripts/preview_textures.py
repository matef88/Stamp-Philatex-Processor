"""
Stamp Philatex Processor - Texture Preview Generator
Creates sample textures for visual comparison.
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import os


def get_project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


def create_linen_texture(width=800, height=600, color=(240, 235, 220)):
    """
    Create realistic linen/canvas texture with woven pattern.
    Mimics archival stamp album pages.
    """
    # Base cream/linen color (BGR)
    texture = np.full((height, width, 3), color, dtype=np.float32)

    # Create horizontal threads
    for y in range(0, height, 3):
        strength = np.random.uniform(0.7, 1.0)
        texture[y:y+2, :] *= strength

    # Create vertical threads
    for x in range(0, width, 3):
        strength = np.random.uniform(0.7, 1.0)
        texture[:, x:x+2] *= strength

    # Add fine weave noise
    noise = np.random.normal(0, 3, (height, width, 3))
    texture += noise

    # Add subtle shadows for depth
    shadow = np.random.normal(0, 2, (height, width, 3))
    shadow = cv2.GaussianBlur(shadow.astype(np.float32), (7, 7), 0)
    texture += shadow

    return np.clip(texture, 0, 255).astype(np.uint8)


def create_album_page_texture(width=800, height=600, color=(245, 240, 230)):
    """
    Create cream album page texture with paper fibers.
    Industry standard for philatelic collections.
    """
    # Base cream color
    texture = np.full((height, width, 3), color, dtype=np.float32)

    # Add paper fiber texture (directional)
    for i in range(500):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        length = np.random.randint(5, 20)
        thickness = np.random.randint(1, 2)
        angle = np.random.uniform(-np.pi/6, np.pi/6)  # Mostly horizontal

        # Draw fiber
        x_end = int(x + length * np.cos(angle))
        y_end = int(y + length * np.sin(angle))

        if 0 <= x_end < width and 0 <= y_end < height:
            color_variation = np.random.uniform(-5, 5)
            cv2.line(texture, (x, y), (x_end, y_end),
                    (color[0] + color_variation, color[1] + color_variation, color[2] + color_variation),
                    thickness)

    # Add fine grain
    fine_noise = np.random.normal(0, 4, (height, width, 3))
    texture += fine_noise

    # Add subtle large variations
    large_noise = np.random.normal(0, 6, (height, width, 3))
    large_noise = cv2.GaussianBlur(large_noise.astype(np.float32), (15, 15), 0)
    texture += large_noise

    return np.clip(texture, 0, 255).astype(np.uint8)


def create_cardstock_texture(width=800, height=600, color=(235, 235, 235)):
    """
    Create smooth cardstock/mat board texture.
    Museum-quality archival appearance.
    """
    # Base light grey/cream
    texture = np.full((height, width, 3), color, dtype=np.float32)

    # Very fine grain (smoother than paper)
    fine_noise = np.random.normal(0, 2, (height, width, 3))
    texture += fine_noise

    # Subtle large variations for depth
    large_noise = np.random.normal(0, 4, (height, width, 3))
    large_noise = cv2.GaussianBlur(large_noise.astype(np.float32), (31, 31), 0)
    texture += large_noise

    return np.clip(texture, 0, 255).astype(np.uint8)


def create_stockbook_texture(width=800, height=600, color=(250, 250, 250)):
    """
    Create stockbook page with grid pattern.
    Practical collection storage appearance.
    """
    # Base white/light grey
    texture = np.full((height, width, 3), color, dtype=np.float32)

    # Add fine noise
    noise = np.random.normal(0, 3, (height, width, 3))
    texture += noise

    # Draw subtle grid lines (stockbook pockets)
    grid_color = (220, 220, 220)

    # Horizontal lines (pocket rows)
    pocket_height = 80
    for y in range(0, height, pocket_height):
        cv2.line(texture, (0, y), (width, y), grid_color, 1)

    # Vertical lines (columns)
    pocket_width = 160
    for x in range(0, width, pocket_width):
        cv2.line(texture, (x, 0), (x, height), grid_color, 1)

    return np.clip(texture, 0, 255).astype(np.uint8)


def create_vintage_album_texture(width=800, height=600):
    """
    Create vintage/aged album page texture.
    For historical stamp collections.
    """
    # Base aged cream/beige
    base_color = (215, 225, 235)  # Slightly yellowed
    texture = np.full((height, width, 3), base_color, dtype=np.float32)

    # Add aging variations (yellowing)
    aging = np.random.normal(0, 8, (height, width, 3))
    aging[:, :, 0] -= 10  # Less blue (more yellow)
    aging = cv2.GaussianBlur(aging.astype(np.float32), (51, 51), 0)
    texture += aging

    # Add paper fibers
    for i in range(300):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        length = np.random.randint(5, 15)
        thickness = 1
        angle = np.random.uniform(0, 2 * np.pi)

        x_end = int(x + length * np.cos(angle))
        y_end = int(y + length * np.sin(angle))

        if 0 <= x_end < width and 0 <= y_end < height:
            cv2.line(texture, (x, y), (x_end, y_end),
                    (base_color[0] - 10, base_color[1] - 10, base_color[2] - 10),
                    thickness)

    # Add age spots
    for i in range(50):
        x = np.random.randint(20, width - 20)
        y = np.random.randint(20, height - 20)
        radius = np.random.randint(2, 8)
        spot_color = (max(0, base_color[0] - 30), max(0, base_color[1] - 30), max(0, base_color[2] - 30))
        cv2.circle(texture, (x, y), radius, spot_color, -1)
        # Blur the spots
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.circle(mask, (x, y), radius + 5, 255, -1)
        texture = cv2.GaussianBlur(texture, (5, 5), 0)

    # Add fine noise
    fine_noise = np.random.normal(0, 5, (height, width, 3))
    texture += fine_noise

    return np.clip(texture, 0, 255).astype(np.uint8)


def create_burlap_texture(width=800, height=600, color=(200, 180, 150)):
    """
    Create burlap/jute fabric texture.
    Rustic, decorative appearance.
    """
    # Base tan color
    texture = np.full((height, width, 3), color, dtype=np.float32)

    # Create coarse weave pattern
    weave_size = 6

    # Horizontal threads (thicker)
    for y in range(0, height, weave_size * 2):
        for offset in range(weave_size):
            if y + offset < height:
                strength = np.random.uniform(0.6, 0.9)
                texture[y + offset, :] *= strength

    # Vertical threads (thicker)
    for x in range(0, width, weave_size * 2):
        for offset in range(weave_size):
            if x + offset < width:
                strength = np.random.uniform(0.6, 0.9)
                texture[:, x + offset] *= strength

    # Add coarse fiber noise
    noise = np.random.normal(0, 8, (height, width, 3))
    texture += noise

    # Add texture depth
    depth = np.random.normal(0, 5, (height, width, 3))
    depth = cv2.GaussianBlur(depth.astype(np.float32), (9, 9), 0)
    texture += depth

    return np.clip(texture, 0, 255).astype(np.uint8)


def create_comparison_grid(textures_dict, output_path):
    """
    Create a grid showing all textures side by side.
    """
    # Calculate grid dimensions
    n_textures = len(textures_dict)
    cols = 3
    rows = (n_textures + cols - 1) // cols

    # Texture dimensions
    tex_height, tex_width = 400, 600

    # Create canvas
    canvas_height = rows * (tex_height + 80)
    canvas_width = cols * (tex_width + 40)
    canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255

    # Place textures
    for idx, (name, texture) in enumerate(textures_dict.items()):
        row = idx // cols
        col = idx % cols

        # Resize texture to standard size
        texture_resized = cv2.resize(texture, (tex_width, tex_height))

        # Position
        y_start = row * (tex_height + 80) + 40
        x_start = col * (tex_width + 40) + 20

        # Place texture
        canvas[y_start:y_start + tex_height, x_start:x_start + tex_width] = texture_resized

        # Add label
        label_y = y_start - 15
        cv2.putText(canvas, name, (x_start, label_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    # Save
    cv2.imwrite(str(output_path), canvas)
    print(f"Comparison grid saved: {output_path}")
    return canvas


def main():
    """Generate all texture samples."""
    print("=" * 60)
    print("  Texture Preview Generator")
    print("=" * 60)
    print()

    # Create output directory
    project_root = get_project_root()
    preview_dir = project_root / "texture_previews"
    preview_dir.mkdir(exist_ok=True)

    print(f"Output directory: {preview_dir}")
    print()

    # Generate textures
    textures = {}

    print("[1/6] Generating Linen Texture...")
    textures["1. Linen (Woven)"] = create_linen_texture()

    print("[2/6] Generating Album Page Texture...")
    textures["2. Album Page (Cream)"] = create_album_page_texture()

    print("[3/6] Generating Cardstock Texture...")
    textures["3. Cardstock (Smooth)"] = create_cardstock_texture()

    print("[4/6] Generating Stockbook Texture...")
    textures["4. Stockbook (Grid)"] = create_stockbook_texture()

    print("[5/6] Generating Vintage Album Texture...")
    textures["5. Vintage Album (Aged)"] = create_vintage_album_texture()

    print("[6/6] Generating Burlap Texture...")
    textures["6. Burlap (Rustic)"] = create_burlap_texture()

    print()
    print("Saving individual samples...")

    # Save individual textures
    for name, texture in textures.items():
        filename = name.split('. ')[1].replace(' ', '_').replace('(', '').replace(')', '').lower() + ".jpg"
        filepath = preview_dir / filename
        cv2.imwrite(str(filepath), texture)
        print(f"  [OK] {filename}")

    print()
    print("Creating comparison grid...")

    # Create comparison grid
    comparison_path = preview_dir / "ALL_TEXTURES_COMPARISON.jpg"
    create_comparison_grid(textures, comparison_path)

    print()
    print("=" * 60)
    print("  Preview Generation Complete!")
    print("=" * 60)
    print()
    print(f"Location: {preview_dir}")
    print()
    print("Files created:")
    print("  - ALL_TEXTURES_COMPARISON.jpg  ← View this for side-by-side comparison")
    print("  - linen_woven.jpg")
    print("  - album_page_cream.jpg")
    print("  - cardstock_smooth.jpg")
    print("  - stockbook_grid.jpg")
    print("  - vintage_album_aged.jpg")
    print("  - burlap_rustic.jpg")
    print()
    print("Open the images to see the textures and choose your favorites!")
    print()


if __name__ == "__main__":
    main()
