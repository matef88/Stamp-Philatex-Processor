# 🏋️ Model Training Guide

Learn how to train your own custom stamp detection model.

---

## Table of Contents

1. [Overview](#overview)
2. [Dataset Preparation](#dataset-preparation)
3. [Training Options](#training-options)
4. [Google Colab Training](#google-colab-training)
5. [Local Training](#local-training)
6. [Model Evaluation](#model-evaluation)
7. [Tips & Best Practices](#tips--best-practices)

---

## Overview

### Why Train Your Own Model?

The default YOLOv8 model is trained on general objects. For optimal stamp detection:

- **Better accuracy** on your specific stamp types
- **Fewer false positives** on similar-looking objects
- **Custom classes** for different stamp categories
- **Improved edge detection** for your stamp styles

### Training Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Images | 100 | 500+ |
| GPU | Any CUDA/DirectML | NVIDIA T4/A100 |
| RAM | 8 GB | 16 GB+ |
| Time | 1-2 hours | 4-8 hours |

---

## Dataset Preparation

### Step 1: Collect Images

**Best practices:**
- Use diverse stamp types and sizes
- Include various backgrounds
- Capture different lighting conditions
- Mix single and multiple stamps per image

**Recommended count:**
- Training: 70% of images
- Validation: 20% of images
- Test: 10% of images

### Step 2: Annotate Images

#### Option A: Roboflow (Recommended)

1. Create account at [roboflow.com](https://roboflow.com)
2. Create new project → "Instance Segmentation"
3. Upload images
4. Annotate using polygon tool
5. Generate dataset
6. Export as **YOLOv8 Segmentation** format

#### Option B: LabelMe

```bash
pip install labelme
labelme
```

1. Draw polygons around each stamp
2. Save as JSON
3. Convert to YOLO format

#### Option C: CVAT

1. Use [CVAT](https://github.com/opencv/cvat)
2. Annotate with polygons
3. Export as YOLO format

### Step 3: Organize Dataset

```
dataset/
├── data.yaml           # Dataset configuration
├── train/
│   ├── images/
│   │   ├── stamp_001.jpg
│   │   └── ...
│   └── labels/
│       ├── stamp_001.txt
│       └── ...
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

### Step 4: Create data.yaml

```yaml
# dataset/data.yaml
path: ./dataset
train: train/images
val: valid/images
test: test/images

nc: 1  # Number of classes
names: ['stamp']  # Class names
```

---

## Training Options

### Option A: Google Colab (Free GPU)

**Pros:**
- Free GPU access (T4)
- No local setup needed
- Easy to use

**Cons:**
- Time limits (12 hours)
- Need to reupload if disconnected

### Option B: Local Training

**Pros:**
- No time limits
- Full control
- Faster iteration

**Cons:**
- Requires GPU
- More setup

---

## Google Colab Training

### Step 1: Prepare Project

1. Upload project to Google Drive
2. Ensure dataset is in `dataset/` folder

### Step 2: Open Notebook

1. Open `notebooks/train_stamps_colab.ipynb` in Colab
2. Set runtime to GPU (Runtime → Change runtime type → T4 GPU)

### Step 3: Run Training

The notebook will:
1. Mount Google Drive
2. Install dependencies
3. Train the model
4. Save weights to `models/stamp_detector_seg/weights/best.pt`

### Quick Colab Script

```python
# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Navigate to project
%cd /content/drive/MyDrive/stamp-philatex-processor

# Install dependencies
!pip install ultralytics

# Train model
from ultralytics import YOLO
model = YOLO('yolov8n-seg.pt')
model.train(
    data='dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0  # GPU
)

# Copy best weights
!cp runs/segment/train/weights/best.pt models/stamp_detector_seg/weights/best.pt
```

---

## Local Training

### Step 1: Setup Environment

```bash
# Activate environment
conda activate stamp_env

# Verify GPU
python scripts/check_gpu.py
```

### Step 2: Configure Training

Edit `config.yaml`:

```yaml
training:
  base_model: "yolov8n-seg.pt"
  epochs: 100
  batch_size: 16
  img_size: 640
  
  augmentation:
    horizontal_flip: true
    vertical_flip: false
    rotation: 15
    scale: 0.2
    mosaic: true
    mixup: 0.1
```

### Step 3: Run Training

```bash
# Using Python script
python scripts/train.py

# OR using launcher (Windows)
launchers\train_model.bat

# OR using YOLO directly
yolo segment train data=dataset/data.yaml model=yolov8n-seg.pt epochs=100
```

### Step 4: Monitor Progress

Training logs are saved to `runs/segment/train/`

Monitor metrics:
- **Box Loss**: Bounding box regression loss
- **Seg Loss**: Segmentation mask loss  
- **mAP50**: Mean Average Precision at 50% IoU
- **mAP50-95**: mAP at 50-95% IoU

---

## Model Evaluation

### Evaluate Model

```bash
# Run evaluation
python scripts/evaluate.py

# OR using YOLO
yolo segment val model=models/stamp_detector_seg/weights/best.pt data=dataset/data.yaml
```

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| mAP50 | Detection accuracy at 50% IoU | > 0.90 |
| mAP50-95 | Detection accuracy at various IoU | > 0.70 |
| Precision | True positives / all detections | > 0.85 |
| Recall | True positives / all ground truth | > 0.85 |

### Visual Evaluation

```bash
# Run inference on test images
yolo segment predict model=models/stamp_detector_seg/weights/best.pt source=dataset/test/images/
```

---

## Tips & Best Practices

### Dataset Quality

✅ **Do:**
- Use high-quality, diverse images
- Include edge cases (partial stamps, overlaps)
- Balance classes if using multiple categories
- Annotate consistently

❌ **Don't:**
- Use blurry or low-quality images
- Skip difficult images
- Mix annotation styles
- Over-augment rare classes

### Training Tips

1. **Start with pre-trained weights**
   - Use `yolov8n-seg.pt` as base
   - Transfer learning speeds up training

2. **Monitor for overfitting**
   - Watch validation loss
   - Use early stopping if needed

3. **Adjust batch size**
   - Larger batch = more stable training
   - Reduce if running out of memory

4. **Use augmentation**
   - Helps generalization
   - Don't overdo it

### Hyperparameter Tuning

```yaml
# For small datasets (< 200 images)
training:
  epochs: 150
  batch_size: 8
  augmentation:
    mosaic: true
    mixup: 0.2

# For large datasets (> 500 images)
training:
  epochs: 100
  batch_size: 32
  augmentation:
    mosaic: true
    mixup: 0.1
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Low mAP | More training data needed |
| Overfitting | Add augmentation, reduce epochs |
| Out of memory | Reduce batch size |
| Slow training | Use GPU, increase batch size |

---

## Exporting Model

### After Training

```bash
# Best weights are saved to:
models/stamp_detector_seg/weights/best.pt

# Copy to active model location
cp runs/segment/train/weights/best.pt models/stamp_detector_seg/weights/best.pt
```

### Export to Other Formats

```python
from ultralytics import YOLO

model = YOLO('models/stamp_detector_seg/weights/best.pt')

# Export to ONNX
model.export(format='onnx')

# Export to TensorRT
model.export(format='engine')
```

---

## Next Steps

After training:
1. Test on new images
2. Adjust confidence threshold if needed
3. Update `config.yaml` with new model path
4. Process your stamp collection!

---

*Last updated: December 2024*
