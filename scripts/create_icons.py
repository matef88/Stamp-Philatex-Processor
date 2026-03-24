from PIL import Image, ImageDraw
import os
from pathlib import Path

def create_check_icon():
    # Define paths
    project_root = Path(__file__).parent.parent
    resources_dir = project_root / 'gui' / 'resources'
    resources_dir.mkdir(parents=True, exist_ok=True)
    
    icon_path = resources_dir / 'check.png'
    
    # Settings
    size = 64
    bg_color = (0, 0, 0, 0) # Transparent
    check_color = (255, 255, 255, 255) # White
    
    # Create image
    img = Image.new('RGBA', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Points for checkmark (scaled 0-1)
    # Start, Mid, End
    points = [
        (0.2, 0.5), # Start (left)
        (0.4, 0.7), # Bottom center
        (0.8, 0.2)  # End (top right)
    ]
    
    # Scale points
    scaled_points = [(x * size, y * size) for x, y in points]
    
    # Draw thicker line
    width = 8
    draw.line(scaled_points, fill=check_color, width=width, joint='curve')
    
    # Save
    img.save(icon_path)
    print(f"Created icon: {icon_path}")

    # Also create a black version for light theme
    icon_path_light = resources_dir / 'check_black.png'
    img_light = Image.new('RGBA', (size, size), bg_color)
    draw_light = ImageDraw.Draw(img_light)
    draw_light.line(scaled_points, fill=(0, 0, 0, 255), width=width, joint='curve')
    img_light.save(icon_path_light)
    print(f"Created icon: {icon_path_light}")

if __name__ == "__main__":
    create_check_icon()
