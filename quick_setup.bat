@echo off
REM ============================================================
REM  Stamp Philatex Processor - Quick Setup (One-Click Install)
REM ============================================================
REM
REM This script automates the complete environment setup.
REM
REM Prerequisites:
REM   - Miniconda or Anaconda must be installed
REM   - Run this from Anaconda Prompt (or regular Command Prompt if conda is in PATH)
REM
REM What this script does:
REM   1. Checks for Conda installation
REM   2. Creates stamp_env environment (Python 3.11)
REM   3. Installs all dependencies from requirements.txt
REM   4. Verifies the setup
REM   5. Provides next steps
REM
REM ============================================================

echo.
echo ============================================================
echo   Stamp Philatex Processor - Quick Setup
echo ============================================================
echo.
echo This will automatically set up your development environment.
echo.
echo Time required: 5-10 minutes (depending on internet speed)
echo Disk space: ~3-4 GB
echo.
echo Press Ctrl+C to cancel, or
pause

cd /d "%~dp0"

echo.
echo ============================================================
echo   Starting Automated Setup...
echo ============================================================
echo.

REM Step 1: Check for Conda
echo [1/5] Checking for Conda installation...
echo.

where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Conda is not found!
    echo.
    echo Please install Miniconda or Anaconda first:
    echo   - Miniconda: https://docs.conda.io/en/latest/miniconda.html
    echo   - Anaconda: https://www.anaconda.com/download
    echo.
    echo After installation:
    echo   1. Open Anaconda Prompt
    echo   2. Navigate to this folder
    echo   3. Run: quick_setup.bat
    echo.
    pause
    exit /b 1
)

echo [OK] Conda found:
conda --version
echo.

REM Step 2: Check if environment exists
echo [2/5] Checking for existing stamp_env environment...
echo.

conda env list | findstr /C:"stamp_env" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] stamp_env environment already exists!
    echo.
    set /p "RECREATE=Do you want to recreate it? This will delete the existing environment. (Y/N): "
    if /i "%RECREATE%"=="Y" (
        echo.
        echo Removing existing environment...
        call conda remove -n stamp_env --all -y
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to remove environment
            pause
            exit /b 1
        )
        echo [OK] Environment removed
        echo.
    ) else (
        echo.
        echo Skipping environment creation. Using existing stamp_env.
        echo Will update packages instead...
        echo.
        goto INSTALL_DEPS
    )
)

REM Step 3: Create environment
echo [3/5] Creating stamp_env environment with Python 3.11...
echo.
echo This may take a few minutes...

call conda create -n stamp_env python=3.11 -y
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to create conda environment!
    echo.
    echo Troubleshooting:
    echo   - Ensure you have sufficient disk space (5GB+)
    echo   - Try closing other applications
    echo   - Check your internet connection
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Environment created successfully!
echo.

:INSTALL_DEPS
REM Step 4: Install dependencies
echo [4/5] Installing dependencies...
echo.
echo Activating stamp_env...

call conda activate stamp_env
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to activate stamp_env!
    echo.
    echo Try running this script from Anaconda Prompt instead.
    echo.
    pause
    exit /b 1
)

echo [OK] Environment activated
echo.
echo Installing packages from requirements.txt...
echo This will take 5-10 minutes...
echo.
echo Progress: [Installing PyTorch, YOLOv8, PyQt6, and other dependencies...]
echo.

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install some dependencies!
    echo.
    echo What to do:
    echo   1. Check the error messages above
    echo   2. Ensure you have a stable internet connection
    echo   3. Try running manually: pip install -r requirements.txt --no-cache-dir
    echo   4. See ENVIRONMENT_SETUP.md for detailed troubleshooting
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] All dependencies installed successfully!
echo.

REM Step 5: Verify setup
echo [5/5] Verifying setup...
echo.

echo Running setup verification...
call launchers\check_setup.bat
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Setup verification detected some issues.
    echo Please review the errors above.
    echo.
) else (
    echo.
    echo [OK] Setup verification passed!
)

echo.
echo ============================================================
echo   Setup Complete!
echo ============================================================
echo.
echo Your development environment is ready.
echo.
echo Environment name: stamp_env
echo Python version: 3.11
echo.
echo GPU Support:
echo   - For AMD GPUs: Run 'conda activate stamp_env' then 'pip install torch-directml'
echo   - For NVIDIA GPUs: CUDA support is already included
echo   - For CPU only: No additional steps needed
echo.
echo Next steps:
echo   1. Close this window
echo   2. Double-click: launchers\run_gui.bat
echo   3. Test with some sample images
echo.
echo Documentation:
echo   - README.md - Full feature documentation
echo   - ENVIRONMENT_SETUP.md - Detailed setup guide
echo   - BUILD_GUIDE.md - How to build executables
echo.
echo ============================================================
echo.
pause
