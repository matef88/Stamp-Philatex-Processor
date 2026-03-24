# 📋 Changelog

All notable changes to Stamp Philatex Processor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Initial GitHub release preparation
- Comprehensive documentation suite
- Contributing guidelines

---

## [1.0.0] - 2024-12-25

### Added

#### Core Features
- **AI-Powered Detection** - YOLOv8 instance segmentation for precise stamp boundaries
- **Smart Auto-Alignment** - Hough line detection + minAreaRect for deskewing
- **Auto-Merge** - Multiple stamps in one image merged into single "sale unit"
- **Duplicate Detection** - Perceptual hashing for finding duplicate stamps
- **Batch Processing** - Process hundreds of images automatically

#### GUI Features
- **Modern PyQt6 Interface** - Professional dark theme
- **Drag & Drop Support** - Drop folders or files directly
- **Real-time Preview** - See results as they process
- **Theme Toggle** - Switch between dark/light modes (Ctrl+T)
- **Color Picker** - Custom border color selection
- **Adjustable Margins** - Fine-tune expansion and border percentages

#### Processing Features
- **HEIC Support** - Auto-convert iPhone HEIC/HEIF images
- **GPU Acceleration** - AMD (DirectML), NVIDIA (CUDA), Apple (MPS)
- **eBay Optimization** - Output sized at 1600px max
- **Textured Borders** - Beautiful green felt texture backgrounds

#### Alignment System
- **Hough Line Detection** - Analyzes actual stamp edges
- **Sub-Degree Accuracy** - Corrects tilts as small as 0.3°
- **Debug Visualization** - "Show alignment line" feature
- **Intelligent Fallback** - minAreaRect when edges not detected

#### Documentation
- **README.md** - Project overview and quick start
- **INSTALLATION.md** - Detailed installation guide
- **USAGE.md** - Complete usage instructions
- **CONFIGURATION.md** - All configuration options
- **TRAINING.md** - Model training guide
- **TROUBLESHOOTING.md** - Common issues and solutions

### Changed
- Improved alignment accuracy for small tilts (0.3-5°)
- Lower rotation threshold (0.3° from 0.5°)
- Enhanced portrait/landscape handling
- Better error handling and logging

### Fixed
- Alignment issues with rotated stamps
- Memory management in batch processing
- Path resolution for frozen executables
- Theme persistence across sessions

---

## [0.9.0] - 2024-12-15

### Added
- Initial beta release
- Basic stamp detection
- Simple cropping functionality
- Command-line interface

### Known Issues
- Alignment not accurate for small tilts
- Memory issues with large batches
- Limited GPU support

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | Dec 2024 | Full release with GUI, alignment, duplicates |
| 0.9.0 | Dec 2024 | Initial beta with basic detection |

---

## Upcoming Features

Planned for future releases:

- [ ] Multi-class stamp categorization
- [ ] Automatic catalog number recognition (OCR)
- [ ] Integration with stamp catalog APIs
- [ ] Batch rename based on detection results
- [ ] Web-based interface option
- [ ] Mobile companion app

---

## Migration Guides

### Upgrading from 0.9.0 to 1.0.0

1. **Update config.yaml** - New settings added:
   ```yaml
   processing:
     rotation_correction: true
     max_rotation_angle: 45
   ```

2. **Reinstall dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Download new model** - Updated model weights available

---

*For detailed commit history, see [GitHub Releases](https://github.com/matef88/Stamp-Philatex-Processor/releases)*
