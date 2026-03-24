# 🔧 Troubleshooting Guide

Solutions to common issues with Stamp Philatex Processor.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Detection Issues](#detection-issues)
3. [Processing Issues](#processing-issues)
4. [GUI Issues](#gui-issues)
5. [GPU Issues](#gpu-issues)
6. [Performance Issues](#performance-issues)
7. [Error Messages](#error-messages)

---

## Installation Issues

### "Module not found: ultralytics"

**Cause:** Dependencies not installed

**Solution:**
```bash
pip install ultralytics
# OR
pip install -r requirements.txt
```

### "DLL load failed" (Windows)

**Cause:** Missing Visual C++ Redistributable

**Solution:**
1. Download from [Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Install and restart computer

### "Permission denied" during installation

**Cause:** Insufficient permissions

**Solution:**
```bash
# Run as administrator (Windows)
# OR use --user flag
pip install -r requirements.txt --user
```

### Conda environment not activating

**Cause:** Conda not initialized

**Solution:**
```bash
# Initialize conda
conda init cmd.exe    # Windows CMD
conda init powershell # Windows PowerShell
conda init bash       # Linux/Mac

# Restart terminal
```

---

## Detection Issues

### "No stamps detected"

**Possible causes and solutions:**

| Cause | Solution |
|-------|----------|
| Confidence too high | Lower `confidence_threshold` to 0.3 |
| Poor image quality | Use higher resolution images |
| Wrong model | Verify model path in config |
| Unusual stamps | Train model with similar stamps |

**Quick fix:**
```yaml
# config.yaml
detection:
  confidence_threshold: 0.3
```

### Too many false positives

**Cause:** Confidence threshold too low

**Solution:**
```yaml
detection:
  confidence_threshold: 0.6  # Increase
```

### Partial stamp detection

**Cause:** Minimum area filter too high

**Solution:**
```yaml
detection:
  min_stamp_area: 2000  # Decrease from 5000
```

### Duplicate detections

**Cause:** IoU threshold too low

**Solution:**
```yaml
detection:
  iou_threshold: 0.5  # Increase from 0.45
```

---

## Processing Issues

### Stamps not aligned correctly

**Solutions:**

1. **Enable rotation correction:**
   ```yaml
   processing:
     rotation_correction: true
   ```

2. **Debug alignment:**
   ```yaml
   processing:
     show_alignment_line: true
   ```

3. **Adjust max rotation:**
   ```yaml
   processing:
     max_rotation_angle: 30  # Reduce if flipping
   ```

### Cropped stamps too tight

**Cause:** Margin too small

**Solution:**
```yaml
processing:
  expand_margin_percent: 0.10  # Increase to 10%
```

### Border texture not showing

**Cause:** Texture file missing

**Solution:**
1. Verify `assets/green_texture.jpg` exists
2. Check path in config:
   ```yaml
   background:
     texture_path: "assets/green_texture.jpg"
   ```

### HEIC files not converting

**Cause:** pillow-heif not installed

**Solution:**
```bash
pip install pillow-heif
```

---

## GUI Issues

### GUI not opening

**Solutions:**

1. **Reinstall PyQt6:**
   ```bash
   pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
   pip install PyQt6
   ```

2. **Check Python version:**
   ```bash
   python --version  # Should be 3.9-3.11
   ```

3. **Run from command line:**
   ```bash
   python run_gui.py
   ```
   Check for error messages.

### GUI crashes on startup

**Cause:** Display/graphics issues

**Solution:**
```bash
# Try software rendering
set QT_OPENGL=software
python run_gui.py
```

### Theme not changing

**Cause:** Config cache

**Solution:**
1. Close application
2. Delete any `.pyc` files in `gui/`
3. Restart

### Drag & drop not working

**Cause:** Permission issue

**Solution:**
- Run as administrator (Windows)
- Check folder permissions

---

## GPU Issues

### "CUDA not available"

**Solutions:**

1. **Update NVIDIA drivers:**
   - Download from [NVIDIA](https://www.nvidia.com/Download/index.aspx)

2. **Install CUDA toolkit:**
   - Download from [NVIDIA CUDA](https://developer.nvidia.com/cuda-downloads)

3. **Verify installation:**
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

### "DirectML not available" (AMD)

**Solutions:**

1. **Install DirectML:**
   ```bash
   pip install torch-directml
   ```

2. **Verify installation:**
   ```bash
   python -c "import torch_directml; print(torch_directml.device())"
   ```

3. **Update config:**
   ```yaml
   hardware:
     device: "directml"
   ```

### "MPS not available" (Apple)

**Solutions:**

1. **Update macOS** to 12.3 or later

2. **Verify PyTorch version:**
   ```bash
   pip install torch --upgrade
   ```

3. **Verify MPS:**
   ```bash
   python -c "import torch; print(torch.backends.mps.is_available())"
   ```

### "Out of memory"

**Solutions:**

1. **Reduce batch size:**
   ```yaml
   hardware:
     batch_size: 4  # Reduce from 8
   ```

2. **Use smaller image size:**
   ```yaml
   detection:
     img_size: 480  # Reduce from 640
   ```

3. **Close other applications**

---

## Performance Issues

### Processing too slow

**Solutions:**

1. **Enable GPU:**
   ```yaml
   hardware:
     device: "cuda"  # or "directml"
   ```

2. **Use fast mode:**
   ```bash
   python scripts/process_stamps.py --fast
   ```

3. **Disable debug visuals:**
   ```yaml
   processing:
     save_visuals: false
   ```

4. **Increase workers:**
   ```yaml
   hardware:
     num_workers: 8
   ```

### High memory usage

**Solutions:**

1. **Reduce batch size:**
   ```yaml
   hardware:
     batch_size: 4
   ```

2. **Process smaller batches**
3. **Close other applications**

---

## Error Messages

### "FileNotFoundError: [Errno 2] No such file or directory"

**Cause:** Missing file or wrong path

**Solution:**
- Check file paths in config.yaml
- Use absolute paths if needed
- Verify files exist

### "ValueError: not enough values to unpack"

**Cause:** Corrupt label file

**Solution:**
- Check label files in dataset/labels/
- Ensure YOLO format is correct

### "RuntimeError: CUDA error: device-side assert triggered"

**Cause:** GPU memory or driver issue

**Solution:**
1. Restart computer
2. Update GPU drivers
3. Reduce batch size

### "KeyboardInterrupt"

**Cause:** User cancelled operation

**Solution:**
- This is normal - just restart the operation

---

## Getting Help

### Before Asking

1. **Check this guide** for your issue
2. **Search existing issues** on GitHub
3. **Try the solutions** listed above

### When Reporting Issues

Include:
- Operating system and version
- Python version (`python --version`)
- Full error message
- Steps to reproduce
- Config file (remove sensitive info)

### Debug Mode

Enable debug logging:
```yaml
logging:
  level: "DEBUG"
  save_to_file: true
```

Check logs in `output/processing.log`

---

## Quick Fixes Summary

| Issue | Quick Fix |
|-------|-----------|
| No detections | Lower confidence to 0.3 |
| Too many detections | Raise confidence to 0.6 |
| Not aligned | Enable rotation correction |
| Slow processing | Enable GPU |
| GUI not opening | Reinstall PyQt6 |
| Out of memory | Reduce batch size |

---

*Last updated: December 2024*
