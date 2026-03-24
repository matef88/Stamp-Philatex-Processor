# ⚙️ Configuration Guide

Complete guide to configuring Stamp Philatex Processor using `config.yaml`.

---

## Table of Contents

1. [Configuration File Location](#configuration-file-location)
2. [Hardware Settings](#hardware-settings)
3. [Input Settings](#input-settings)
4. [Detection Settings](#detection-settings)
5. [Processing Settings](#processing-settings)
6. [Background Settings](#background-settings)
7. [Duplicate Detection](#duplicate-detection)
8. [GUI Settings](#gui-settings)
9. [Training Settings](#training-settings)
10. [Logging Settings](#logging-settings)

---

## Configuration File Location

The main configuration file is `config.yaml` in the project root.

```bash
Stamp Philatex Processor/
├── config.yaml    ← Main configuration file
├── run_gui.py
└── ...
```

### Editing Configuration

**Option 1: Text Editor**
```bash
notepad config.yaml        # Windows
nano config.yaml           # Linux/Mac
code config.yaml           # VS Code
```

**Option 2: GUI**
Settings can also be adjusted in the GUI's Settings tabs.

---

## Hardware Settings

Configure hardware acceleration and performance.

```yaml
hardware:
  # Device options: "cpu", "cuda", "directml", "mps"
  device: "directml"
  
  # Batch size for parallel processing
  batch_size: 8
  
  # Number of data loading workers
  num_workers: 4
```

### Device Options

| Device | Description | Requirements |
|--------|-------------|--------------|
| `cpu` | CPU only | None (slowest) |
| `cuda` | NVIDIA GPU | NVIDIA GPU + CUDA |
| `directml` | AMD GPU (Windows) | AMD GPU + DirectML |
| `mps` | Apple Silicon | M1/M2/M3 Mac |

### Batch Size Guidelines

| VRAM | Recommended Batch Size |
|------|----------------------|
| 4 GB | 4 |
| 8 GB | 8 |
| 16 GB | 16 |
| 32 GB+ | 32 |

---

## Input Settings

Configure input image handling.

```yaml
input:
  # Supported image formats
  supported_formats: [".jpg", ".jpeg", ".png", ".heic", ".heif", ".bmp", ".tiff", ".webp"]
  
  # Auto-convert iPhone HEIC to JPG
  auto_convert_heic: true
  
  # Delete HEIC after conversion
  delete_heic_after_convert: true
  
  # JPEG quality for HEIC conversion (1-100)
  heic_conversion_quality: 95
  
  # Background optimization
  background_type: "dark"
```

### HEIC Conversion

For iPhone photos:
- `auto_convert_heic: true` - Automatically convert HEIC to JPG
- `delete_heic_after_convert: true` - Save disk space
- `heic_conversion_quality: 95` - Near-lossless quality

---

## Detection Settings

Configure YOLOv8 detection parameters.

```yaml
detection:
  # Task type (don't change)
  task: "segment"
  
  # Confidence threshold (0.0 - 1.0)
  confidence_threshold: 0.5
  
  # IoU threshold for NMS
  iou_threshold: 0.45
  
  # Input image size for model
  img_size: 640
  
  # Minimum stamp area in pixels
  min_stamp_area: 5000
```

### Confidence Threshold Guide

| Value | Behavior | Use Case |
|-------|----------|----------|
| 0.3 | More detections, more false positives | Noisy images |
| 0.5 | Balanced (default) | General use |
| 0.7 | Fewer detections, high precision | Clean scans |

### IoU Threshold

Controls overlap filtering:
- Lower (0.3): More overlapping detections
- Higher (0.6): Fewer overlapping detections
- Default (0.45): Balanced

---

## Processing Settings

Configure stamp processing and output.

```yaml
processing:
  # Margin from stamp edge (expansion)
  expand_margin_percent: 0.05    # 5%
  
  # Texture border size
  texture_margin_percent: 0.10   # 10%
  
  # Aspect ratio normalization
  max_aspect_ratio: 2.0
  normalize_aspect_ratio: true
  
  # Rotation correction
  rotation_correction: true
  max_rotation_angle: 45
  
  # Output settings
  output_format: "jpg"
  output_quality: 95
  ebay_max_dimension: 1600
  preserve_aspect_ratio: true
  
  # Debug options
  show_alignment_line: false
  show_segmentation_points: true
  save_visuals: true
```

### Margin Settings

| Setting | Effect | Recommended |
|---------|--------|-------------|
| `expand_margin_percent` | Background context around stamp | 0.05 (5%) |
| `texture_margin_percent` | Green border size | 0.10 (10%) |

### Rotation Correction

- `rotation_correction: true` - Enable auto-alignment
- `max_rotation_angle: 45` - Maximum correction (prevents flipping)

### Output Settings

| Setting | Options |
|---------|---------|
| `output_format` | "jpg", "png" |
| `output_quality` | 1-100 (95 recommended) |
| `ebay_max_dimension` | 1600 (eBay optimal) |

---

## Background Settings

Configure border texture and colors.

```yaml
background:
  # Path to texture image
  texture_path: "assets/green_texture.jpg"
  
  # Fallback color (BGR format)
  color: [51, 112, 68]    # Green
  
  # Texture noise level
  noise_level: 10
```

### Color Values (BGR Format)

| Color | BGR Value |
|-------|-----------|
| Green | [51, 112, 68] |
| Black | [0, 0, 0] |
| White | [255, 255, 255] |
| Gray | [128, 128, 128] |

---

## Duplicate Detection

Configure duplicate stamp detection.

```yaml
duplicates:
  # Enable/disable
  enabled: true
  
  # Hash algorithm
  hash_algorithm: "phash"
  
  # Similarity threshold (Hamming distance)
  similarity_threshold: 10
  
  # Cross-batch checking
  check_cross_batch: true
  check_within_batch: true
  
  # Action: "skip", "flag", "move"
  duplicate_action: "flag"
  
  # Folder for flagged duplicates
  duplicates_folder: "output/duplicates"
```

### Hash Algorithms

| Algorithm | Speed | Accuracy |
|-----------|-------|----------|
| `phash` | Medium | High (recommended) |
| `dhash` | Fast | Medium |
| `ahash` | Fastest | Lowest |

### Similarity Threshold

| Value | Sensitivity |
|-------|-------------|
| 5 | Very strict |
| 10 | Balanced (recommended) |
| 15 | Loose |
| 20 | Very loose |

---

## GUI Settings

Configure the graphical interface.

```yaml
gui:
  # Theme: "dark", "light", "system"
  theme: "dark"
  
  # Preview panel
  preview_enabled: true
  
  # Show confidence scores
  show_confidence: true
  
  # Auto-scroll to latest
  auto_scroll: true
  
  # Thumbnail size
  thumbnail_size: 150
  
  # Window size
  window_width: 1400
  window_height: 900
```

---

## Training Settings

Configure model training parameters.

```yaml
training:
  # Base model for transfer learning
  base_model: "yolov8n-seg.pt"
  
  # Training epochs
  epochs: 100
  
  # Batch size
  batch_size: 16
  
  # Image size
  img_size: 640
  
  # Data augmentation
  augmentation:
    horizontal_flip: true
    vertical_flip: false
    rotation: 15
    scale: 0.2
    mosaic: true
    mixup: 0.1
```

---

## Logging Settings

Configure logging and debugging.

```yaml
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR
  level: "INFO"
  
  # Save to file
  save_to_file: true
  log_file: "output/processing.log"
  
  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Log Levels

| Level | Description |
|-------|-------------|
| DEBUG | Detailed debugging info |
| INFO | General information |
| WARNING | Warning messages |
| ERROR | Error messages only |

---

## Quick Reference

### Most Common Settings

```yaml
# For better detection on difficult images
detection:
  confidence_threshold: 0.3

# For faster processing
processing:
  save_visuals: false
  
# For different border color
background:
  color: [0, 0, 0]  # Black

# For GPU acceleration
hardware:
  device: "cuda"  # or "directml" for AMD
```

---

*Last updated: December 2024*
