# 📦 Installation Guide

Complete guide to install and configure Stamp Philatex Processor on your system.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Detailed Installation](#detailed-installation)
4. [GPU Setup](#gpu-setup)
5. [Model Download](#model-download)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10/11, macOS 10.15+, Linux |
| **Python** | 3.9 - 3.11 |
| **RAM** | 8 GB |
| **Disk Space** | 5 GB |
| **Display** | 1280 x 720 |

### Recommended Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 11, macOS 12+, Ubuntu 22.04 |
| **Python** | 3.11 |
| **RAM** | 16 GB |
| **GPU** | AMD (DirectML) or NVIDIA (CUDA) |
| **Disk Space** | 10 GB (including models) |
| **Display** | 1920 x 1080 |

### GPU Support

| GPU Type | Backend | Installation |
|----------|---------|--------------|
| **NVIDIA** | CUDA | Automatic with PyTorch |
| **AMD (Windows)** | DirectML | `pip install torch-directml` |
| **Apple Silicon** | MPS | Built into PyTorch |
| **CPU Only** | - | No additional setup |

---

## Quick Installation

### Windows (One-Click)

```batch
REM Run the quick setup script
quick_setup.bat
```

This will:
1. Create a conda environment named `stamp_env`
2. Install all dependencies
3. Download required models
4. Create desktop shortcuts

### Manual Installation

```bash
# 1. Clone the repository
git clone https://github.com/matef88/Stamp-Philatex-Processor.git
cd stamp-philatex-processor

# 2. Create conda environment
conda create -n stamp_env python=3.11
conda activate stamp_env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python run_gui.py
```

---

## Detailed Installation

### Step 1: Install Python/Conda

#### Option A: Anaconda (Recommended)

1. Download from [anaconda.com/download](https://www.anaconda.com/download)
2. Run the installer
3. Verify installation:
   ```bash
   conda --version
   ```

#### Option B: Miniconda (Lightweight)

1. Download from [docs.conda.io/en/latest/miniconda](https://docs.conda.io/en/latest/miniconda.html)
2. Run the installer
3. Verify installation:
   ```bash
   conda --version
   ```

#### Option C: Python Only

1. Download from [python.org](https://www.python.org/downloads/)
2. Ensure you select "Add Python to PATH"
3. Verify installation:
   ```bash
   python --version
   ```

### Step 2: Clone Repository

```bash
# Using HTTPS
git clone https://github.com/matef88/Stamp-Philatex-Processor.git

# Using SSH
git clone git@github.com:matef88/Stamp-Philatex-Processor.git

# Navigate to project
cd stamp-philatex-processor
```

### Step 3: Create Virtual Environment

#### Using Conda (Recommended)

```bash
# Create environment
conda create -n stamp_env python=3.11

# Activate environment
conda activate stamp_env
```

#### Using venv

```bash
# Create environment
python -m venv stamp_env

# Activate (Windows)
stamp_env\Scripts\activate

# Activate (Linux/Mac)
source stamp_env/bin/activate
```

### Step 4: Install Dependencies

```bash
# Install all requirements
pip install -r requirements.txt
```

**This installs:**
- `ultralytics` - YOLOv8 framework
- `torch` - PyTorch deep learning
- `opencv-python` - Image processing
- `PyQt6` - GUI framework
- `pillow` - Image manipulation
- `imagehash` - Duplicate detection
- And more...

### Step 5: Install GPU Support (Optional)

See [GPU Setup](#gpu-setup) section below.

---

## GPU Setup

### NVIDIA (CUDA)

CUDA support is included with PyTorch by default.

**Verify CUDA:**
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

**Expected output:** `True`

**If False:**
1. Update NVIDIA drivers
2. Install CUDA toolkit from [developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads)
3. Reinstall PyTorch:
   ```bash
   pip install torch torchvision --upgrade
   ```

### AMD (DirectML - Windows Only)

```bash
# Install DirectML support
pip install torch-directml
```

**Verify DirectML:**
```bash
python -c "import torch_directml; print(torch_directml.device())"
```

**Update config.yaml:**
```yaml
hardware:
  device: "directml"
```

### Apple Silicon (MPS)

MPS is built into PyTorch 2.0+.

**Verify MPS:**
```bash
python -c "import torch; print(torch.backends.mps.is_available())"
```

**Update config.yaml:**
```yaml
hardware:
  device: "mps"
```

### CPU Only

No additional setup required. The system will automatically fall back to CPU.

**Update config.yaml:**
```yaml
hardware:
  device: "cpu"
```

---

## Model Download

### Pre-trained Model

The application requires a trained YOLOv8 segmentation model.

**Option 1: Download from Releases**

1. Go to [GitHub Releases](https://github.com/matef88/Stamp-Philatex-Processor/releases)
2. Download `stamp_detector_model.zip`
3. Extract to `models/stamp_detector_seg/weights/`

**Option 2: Use Base Model**

```bash
# The system will auto-download yolov8n-seg.pt on first run
# For better accuracy, train your own model
```

### Model Structure

```
models/
└── stamp_detector_seg/
    └── weights/
        ├── best.pt      # Best performing model
        ├── last.pt      # Last checkpoint
        └── ...
```

### Training Custom Model

See [docs/TRAINING.md](TRAINING.md) for instructions on training your own model.

---

## Verification

### Run System Check

```bash
python scripts/check_gpu.py
```

**Expected output:**
```
=== GPU Check ===
CUDA available: True/False
DirectML available: True/False
MPS available: True/False
Recommended device: cuda/directml/mps/cpu
```

### Run Test Suite

```bash
python scripts/test_setup.py
```

**This verifies:**
- Python version
- All dependencies installed
- GPU detection
- Model loading
- Basic processing

### Launch GUI

```bash
python run_gui.py
```

If the GUI opens without errors, installation is successful!

---

## Troubleshooting

### Common Issues

#### "Module not found: ultralytics"

```bash
pip install ultralytics
# OR
pip install -r requirements.txt
```

#### "DLL load failed" (Windows)

1. Install Visual C++ Redistributable:
   - Download from [Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - Install and restart

#### "CUDA out of memory"

Reduce batch size in `config.yaml`:
```yaml
hardware:
  batch_size: 4  # Reduce from 8
```

#### "torch_directml not found"

```bash
pip install torch-directml
```

#### GUI not opening

1. Check PyQt6 installation:
   ```bash
   pip install PyQt6 --upgrade
   ```
2. Try reinstalling:
   ```bash
   pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
   pip install PyQt6
   ```

### Environment Issues

#### Reset Environment

```bash
# Remove environment
conda deactivate
conda env remove -n stamp_env

# Recreate
conda create -n stamp_env python=3.11
conda activate stamp_env
pip install -r requirements.txt
```

#### Dependency Conflicts

```bash
# Create fresh environment
conda create -n stamp_env_new python=3.11
conda activate stamp_env_new
pip install -r requirements.txt
```

### Platform-Specific Issues

#### Windows

- Run Command Prompt as Administrator
- Check Windows Defender isn't blocking Python
- Ensure Visual C++ Redistributable is installed

#### macOS

- Install Xcode Command Line Tools:
  ```bash
  xcode-select --install
  ```
- For M1/M2 Macs, use Rosetta if needed

#### Linux

- Install system dependencies:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-dev python3-pip
  
  # Fedora
  sudo dnf install python3-devel python3-pip
  ```

---

## Uninstallation

### Remove Environment

```bash
conda deactivate
conda env remove -n stamp_env
```

### Remove Project

```bash
# Delete project folder
rm -rf stamp-philatex-processor
```

---

## Next Steps

After successful installation:

1. Read [USAGE.md](USAGE.md) for how to use the application
2. Review [CONFIGURATION.md](CONFIGURATION.md) for settings
3. Check [TRAINING.md](TRAINING.md) to train custom models

---

## Getting Help

If you encounter issues not covered here:

1. Check [GitHub Issues](https://github.com/matef88/Stamp-Philatex-Processor/issues)
2. Create a new issue with:
   - Your OS and version
   - Python version
   - Full error message
   - Steps to reproduce

---

*Last updated: December 2024*
