@echo off
setlocal
REM Stamp Philatex Processor - Dependency Installer
REM Comprehensive environment setup matching ENVIRONMENT_SETUP.md guide

echo ==============================================
echo   Stamp Philatex Processor - Environment Setup
echo ==============================================
echo.

REM Get absolute path to launchers dir
set "LAUNCHERS_DIR=%~dp0"
REM Remove trailing backslash if present
if "%LAUNCHERS_DIR:~-1%"=="\" set "LAUNCHERS_DIR=%LAUNCHERS_DIR:~0,-1%"

REM Go to project root (parent of launchers)
cd /d "%LAUNCHERS_DIR%\.."

echo [Step 1/4] Checking for Conda installation...
echo.

REM Check if conda is available
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Conda is not installed or not in PATH!
    echo.
    echo Please install Miniconda or Anaconda first:
    echo   - Miniconda: https://docs.conda.io/en/latest/miniconda.html
    echo   - Anaconda: https://www.anaconda.com/download
    echo.
    echo After installation, run this script again from Anaconda Prompt.
    echo.
    pause
    exit /b 1
)

echo [OK] Conda is installed
conda --version
echo.

REM Check if stamp_env already exists
echo [Step 2/4] Checking for stamp_env environment...
echo.

conda env list | findstr /C:"stamp_env" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] stamp_env environment already exists
    echo.

    REM Ask if user wants to recreate or update
    set /p "CHOICE=Do you want to (U)pdate packages or (R)ecreate environment? [U/R]: "
    if /i "%CHOICE%"=="R" (
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
        goto CREATE_ENV
    ) else (
        goto INSTALL_DEPS
    )
) else (
    echo [INFO] stamp_env environment does not exist
    echo.
    goto CREATE_ENV
)

:CREATE_ENV
echo [Step 3/4] Creating stamp_env environment...
echo.

echo Creating environment with Python 3.11...
call conda create -n stamp_env python=3.11 -y
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to create conda environment!
    pause
    exit /b 1
)

echo [OK] Environment created successfully
echo.

:INSTALL_DEPS
echo [Step 4/4] Installing dependencies...
echo.

REM Activate environment and install packages
echo Activating stamp_env environment...
call conda activate stamp_env
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to activate stamp_env!
    echo Please ensure conda is properly initialized.
    echo Try running this from Anaconda Prompt.
    pause
    exit /b 1
)

echo [OK] Environment activated
echo.

echo Installing packages from requirements.txt...
echo This may take 5-10 minutes depending on your internet speed...
echo.

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies!
    echo.
    echo Troubleshooting steps:
    echo   1. Check your internet connection
    echo   2. Try running: pip install -r requirements.txt --no-cache-dir
    echo   3. Ensure Python 3.11 is being used: python --version
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] All dependencies installed successfully!
echo.

REM Check for GPU support
echo ==============================================
echo   GPU Support Information
echo ==============================================
echo.

echo Checking for GPU availability...
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())" 2>nul
if %errorlevel% equ 0 (
    echo.
    echo For AMD GPU support (DirectML), run:
    echo   conda activate stamp_env
    echo   pip install onnx onnxruntime-directml
    echo.
    echo For NVIDIA GPUs, CUDA support should already be included.
) else (
    echo [INFO] Could not check GPU status (PyTorch may still be installing)
)

echo.
echo ==============================================
echo   Setup Complete!
echo ==============================================
echo.

echo Next steps:
echo   1. Verify setup with: launchers\check_setup.bat
echo   2. Run the GUI with: launchers\run_gui.bat
echo   3. See ENVIRONMENT_SETUP.md for detailed documentation
echo.

echo Environment: stamp_env
echo Python version: 3.11
echo Installed packages: See requirements.txt
echo.

pause
