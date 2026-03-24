# 📖 Usage Guide

This comprehensive guide explains how to use Stamp Philatex Processor effectively.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [GUI Overview](#gui-overview)
3. [Processing Images](#processing-images)
4. [Settings Explained](#settings-explained)
5. [Output Structure](#output-structure)
6. [Advanced Features](#advanced-features)
7. [Command Line Usage](#command-line-usage)
8. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Launching the Application

**Windows:**
```bash
# Double-click launchers\run_gui.bat
# OR
python run_gui.py
```

**Linux/Mac:**
```bash
python run_gui.py
```

### First Run

On first launch, the application will:
1. Load the configuration from `config.yaml`
2. Initialize the YOLOv8 model
3. Prepare the GPU/CPU for processing

---

## GUI Overview

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  File  Edit  View  Help                    [Theme Toggle] [-□×] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐  │
│  │   FOLDER        │  │          PREVIEW AREA               │  │
│  │   SELECTION     │  │                                     │  │
│  │                 │  │     [Selected Image Preview]        │  │
│  │  [Browse...]    │  │                                     │  │
│  │                 │  │                                     │  │
│  │  Path: /path    │  │                                     │  │
│  └─────────────────┘  └─────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐  │
│  │    SETTINGS     │  │          RESULTS GRID               │  │
│  │                 │  │                                     │  │
│  │  □ General      │  │  [thumb] [thumb] [thumb] [thumb]   │  │
│  │  □ Appearance   │  │  [thumb] [thumb] [thumb] [thumb]   │  │
│  │  □ Detection    │  │  [thumb] [thumb] [thumb] [thumb]   │  │
│  │                 │  │                                     │  │
│  │  [Process]      │  │                                     │  │
│  └─────────────────┘  └─────────────────────────────────────┘  │
│                                                                 │
│  Status: Ready | Processed: 0 | Success: 0 | Failed: 0         │
└─────────────────────────────────────────────────────────────────┘
```

### Key Interface Elements

| Element | Description |
|---------|-------------|
| **Folder Selection** | Choose input folder containing stamp images |
| **Preview Area** | Large preview of selected/processing image |
| **Settings Tabs** | Configure processing parameters |
| **Results Grid** | Thumbnails of processed stamps |
| **Status Bar** | Processing statistics and progress |

---

## Processing Images

### Step-by-Step Process

#### 1. Select Input Folder

Click **"Browse Folder"** or drag & drop a folder onto the window.

**Supported formats:**
- `.jpg` / `.jpeg`
- `.png`
- `.heic` / `.heif` (iPhone)
- `.bmp`
- `.tiff`
- `.webp`

#### 2. Configure Settings

Adjust settings in the tabs (see [Settings Explained](#settings-explained)).

#### 3. Process Batch

Click **"Process Batch"** to start processing.

The application will:
1. Scan all images in the folder
2. Detect stamps using AI
3. Align and crop each stamp
4. Add textured borders
5. Save to output folder

#### 4. Review Results

- Check the **Results Grid** for thumbnails
- Click any thumbnail to preview
- Check the **Status Bar** for statistics
- Find files in `output/crops/`

---

## Settings Explained

### General Tab

| Setting | Description | Default |
|---------|-------------|---------|
| **Auto-rotate (deskew)** | Automatically straighten tilted stamps | ✅ Enabled |
| **Max rotation angle** | Maximum degrees to rotate (prevents flipping) | 45° |
| **Output format** | Image format for output | JPG |
| **Output quality** | JPEG quality (1-100) | 95 |

### Appearance Tab

| Setting | Description | Default |
|---------|-------------|---------|
| **Background expansion** | Margin around detected stamp | 5% |
| **Texture border** | Green textured border size | 10% |
| **Border color** | Color of the texture border | Green |
| **Show alignment line** | Debug: show detection outline | ❌ Disabled |

### Detection Tab

| Setting | Description | Default |
|---------|-------------|---------|
| **Confidence threshold** | Detection sensitivity (0-1) | 0.5 |
| **IoU threshold** | Overlap filtering | 0.45 |
| **Minimum stamp area** | Minimum pixels for valid detection | 5000 |

### Understanding Thresholds

**Confidence Threshold:**
- **Lower (0.3)**: More detections, more false positives
- **Higher (0.7)**: Fewer detections, more accurate

**Recommended values:**
- Clear scans: `0.5` - `0.6`
- Noisy images: `0.3` - `0.4`
- High precision: `0.6` - `0.7`

---

## Output Structure

### Folder Organization

```
output/
├── crops/                    # Final processed stamps
│   ├── stamp_001.jpg
│   ├── stamp_002.jpg
│   └── ...
│
├── visuals/                  # Debug visualizations
│   ├── detection_overlay.jpg
│   └── ...
│
├── duplicates/               # Flagged duplicate stamps
│   └── ...
│
└── reports/                  # Processing reports
    └── batch_report.csv
```

### File Naming Convention

Processed files are named sequentially:
```
stamp_001.jpg
stamp_002.jpg
stamp_003.jpg
...
```

### Image Specifications

| Property | Value |
|----------|-------|
| Max dimension | 1600px (eBay optimized) |
| Format | JPEG |
| Quality | 95% |
| Color space | RGB |

---

## Advanced Features

### Duplicate Detection

The system automatically detects duplicate stamps using perceptual hashing.

**How it works:**
1. Generates a visual hash of each stamp
2. Compares against previous batches
3. Flags potential duplicates

**Configuration:**
```yaml
duplicates:
  enabled: true
  hash_algorithm: "phash"        # perceptual hash
  similarity_threshold: 10       # hamming distance
  duplicate_action: "flag"       # skip, flag, or move
```

### Batch Processing Statistics

Track your processing with real-time stats:
- **Processed**: Total images processed
- **Success**: Successfully extracted stamps
- **Failed**: Images with no detections
- **Duplicates**: Flagged duplicate stamps

### Theme Customization

Toggle between themes:
- **Dark Theme**: Default, easy on eyes
- **Light Theme**: Better for bright environments

**Shortcut:** `Ctrl + T`

---

## Command Line Usage

For automation and scripting, use the command line interface:

### Basic Processing

```bash
python scripts/process_stamps.py --input ./my_stamps --output ./processed
```

### Available Arguments

| Argument | Description |
|----------|-------------|
| `--input` | Input folder path |
| `--output` | Output folder path |
| `--config` | Custom config file |
| `--fast` | Skip debug visuals (faster) |
| `--dry-run` | Test without saving |
| `--no-duplicates` | Skip duplicate detection |

### Examples

```bash
# Fast processing (no debug)
python scripts/process_stamps.py --input ./scans --fast

# Test run
python scripts/process_stamps.py --input ./scans --dry-run

# Custom config
python scripts/process_stamps.py --input ./scans --config custom.yaml
```

---

## Tips & Best Practices

### Image Quality

✅ **Do:**
- Use high-resolution scans (300 DPI minimum)
- Ensure good lighting and contrast
- Keep stamps flat and straight
- Use consistent background colors

❌ **Don't:**
- Use blurry or low-quality images
- Mix different background colors
- Overlap stamps in scans

### Batch Organization

**Recommended folder structure:**
```
stamps_to_process/
├── batch_001/
│   ├── scan_001.jpg
│   ├── scan_002.jpg
│   └── ...
├── batch_002/
│   └── ...
```

### Performance Optimization

**For faster processing:**
1. Enable `--fast` mode
2. Increase `batch_size` in config
3. Use GPU acceleration
4. Disable `save_visuals`

**For better quality:**
1. Use higher confidence threshold
2. Enable rotation correction
3. Keep debug visuals enabled
4. Review flagged duplicates

### Common Workflows

#### eBay Listing Preparation
1. Process batch with default settings
2. Review results in `output/crops/`
3. Check for duplicates
4. Upload to eBay

#### Collection Digitization
1. Enable duplicate detection
2. Process in organized batches
3. Generate inventory report
4. Backup processed images

---

## Troubleshooting

### No Stamps Detected

**Possible causes:**
- Confidence threshold too high
- Poor image quality
- Model not trained for stamp type

**Solutions:**
1. Lower confidence threshold to 0.3
2. Improve image quality
3. Retrain model with similar stamps

### Stamps Not Aligned

**Possible causes:**
- Rotation correction disabled
- Unclear stamp edges
- Extreme tilt angle

**Solutions:**
1. Enable rotation correction
2. Enable "Show alignment line" to debug
3. Check `max_rotation_angle` setting

### Slow Processing

**Possible causes:**
- CPU-only mode
- Large batch sizes
- Debug visuals enabled

**Solutions:**
1. Enable GPU acceleration
2. Reduce batch size
3. Use `--fast` mode

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + O` | Open folder |
| `Ctrl + T` | Toggle theme |
| `Ctrl + P` | Process batch |
| `Ctrl + Q` | Quit |
| `F5` | Refresh |

---

## Getting Help

- **Documentation**: Check the `docs/` folder
- **Issues**: Report bugs on GitHub
- **Config**: Review `config.yaml` for all options

---

*Last updated: December 2024*
