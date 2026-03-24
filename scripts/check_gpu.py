
import sys
import torch
import platform
import os

output_file = "gpu_report.txt"

with open(output_file, "w", encoding="utf-8") as f:
    def log(msg):
        print(msg)
        f.write(msg + "\n")

    log("="*60)
    log("GPU CAPABILITY DIAGNOSTIC")
    log("="*60)
    log(f"OS: {platform.system()} {platform.release()}")
    log(f"Python: {sys.version}")
    log(f"PyTorch Version: {torch.__version__}")
    log("-" * 60)

    # Check CUDA
    if torch.cuda.is_available():
        log(f"✅ CUDA (NVIDIA) is AVAILABLE")
        log(f"   Device Count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            log(f"   Device {i}: {torch.cuda.get_device_name(i)}")
        best_device = "cuda"
    else:
        log(f"❌ CUDA (NVIDIA) is NOT available")

    log("-" * 60)

    # Check DirectML
    try:
        import torch_directml
        dml = torch_directml.device()
        log(f"✅ DirectML (AMD/Intel) is AVAILABLE")
        log(f"   Device: {dml}")
        # Try to move a tensor to DML to verify it actually works
        try:
            t = torch.ones(1).to(dml)
            log("   Test Tensor: Successfully created on DirectML device")
            if not torch.cuda.is_available():
                best_device = "directml"
        except Exception as e:
            log(f"   WARNING: DirectML device found but failed to use: {e}")
            
    except ImportError:
        log(f"❌ DirectML (torch-directml) is NOT installed")
    except Exception as e:
        log(f"❌ DirectML Error: {e}")

    log("-" * 60)

    if 'best_device' not in locals():
        best_device = "cpu"

    log(f"RECOMMENDED DEVICE: {best_device}")
    log("="*60)

print(f"Report written to {output_file}")
