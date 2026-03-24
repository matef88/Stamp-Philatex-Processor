# Dataset

This folder contains training data for the stamp detection model.

## Structure

```
dataset/
├── data.yaml           # Dataset configuration
├── train/
│   ├── images/       # Training images
│   └── labels/       # Training labels (YOLO format)
├── valid/
│   ├── images/       # Validation images
│   └── labels/       # Validation labels
└── test/
    ├── images/       # Test images
    └── labels/       # Test labels
```

## Getting Dataset

### Option 1: Use Your Own Images

1. Collect stamp images
2. Annotate using [Roboflow](https://roboflow.com)
3. Export as **YOLOv8 Segmentation** format
4. Extract to this folder

### Option 2: Download Sample Dataset

Download a sample dataset from the [Releases](https://github.com/matef88/Stamp-Philatex-Processor/releases) page.

## data.yaml Format

```yaml
# Dataset configuration for YOLOv8
path: ./dataset
train: train/images
val: valid/images
test: test/images

# Classes
nc: 1  # Number of classes
names: ['stamp']  # Class names
```

## Label Format (YOLO)

Each label file (`.txt`) corresponds to an image and contains one line per object:

```
class_id x_center y_center width height x1 y1 x2 y2 ... xn yn
```

For segmentation:
- `class_id`: Class ID (0 for stamp)
- `x_center, y_center, width, height`: Normalized bounding box (0-1)
- `x1, y1, ..., xn, yn`: Normalized polygon points (0-1)

## Tips

- **Minimum images**: 100+ for basic training
- **Recommended**: 500+ for good accuracy
- **Balance**: Mix different stamp types,- **Augmentation**: Applied automatically during training
