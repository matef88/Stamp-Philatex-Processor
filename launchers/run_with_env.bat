@echo off
REM Master Launcher for Stamp Philatex Processor
REM Ensures commands run inside the stamp_env conda environment
REM Usage: run_with_env.bat [script_name] [args...]

set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

echo ============================================
echo   Stamp Philatex Processor - Launcher
echo ============================================
echo.

REM Check if arguments provided
if "%~1"=="" (
    echo [ERROR] No script specified.
    echo Usage: run_with_env.bat script.py [args]
    echo.
    pause
    exit /b 1
)

echo [INFO] Detecting Python environment...
echo.

REM Method 1: Try conda activate (most reliable)
where conda >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Found conda, checking for stamp_env...

    REM Check if stamp_env exists
    conda env list | findstr /C:"stamp_env" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [INFO] Found stamp_env environment
        echo [INFO] Activating stamp_env...
        echo.

        REM Activate and run
        call conda activate stamp_env
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to activate stamp_env
            echo.
            echo Try running from Anaconda Prompt instead.
            echo.
            pause
            exit /b 1
        )

        echo [INFO] Running: python %*
        echo.
        python %*

        if %errorlevel% neq 0 (
            echo.
            echo [ERROR] Script failed with exit code %errorlevel%
            pause
            exit /b %errorlevel%
        )

        exit /b 0
    ) else (
        echo [WARNING] stamp_env not found in conda environments
        echo.
        echo Please create it first:
        echo   conda create -n stamp_env python=3.11
        echo   conda activate stamp_env
        echo   pip install -r requirements.txt
        echo.
        echo Or run: quick_setup.bat
        echo.
        pause
        exit /b 1
    )
)

REM Method 2: Try direct path to common conda locations
set "CONDA_PATHS=%USERPROFILE%\anaconda3;%USERPROFILE%\miniconda3;C:\ProgramData\anaconda3;C:\ProgramData\miniconda3"

for %%P in (%CONDA_PATHS%) do (
    if exist "%%P\envs\stamp_env\python.exe" (
        echo [INFO] Found stamp_env at: %%P\envs\stamp_env
        echo [INFO] Running script...
        echo.

        "%%P\envs\stamp_env\python.exe" %*

        if %errorlevel% neq 0 (
            echo.
            echo [ERROR] Script failed with exit code %errorlevel%
            pause
            exit /b %errorlevel%
        )

        exit /b 0
    )
)

REM Method 3: Fallback to local venv
if exist "venv\Scripts\python.exe" (
    echo [INFO] Found local venv
    echo [INFO] Running script...
    echo.

    "venv\Scripts\python.exe" %*

    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Script failed with exit code %errorlevel%
        pause
        exit /b %errorlevel%
    )

    exit /b 0
)

REM No environment found
echo.
echo ============================================
echo   [ERROR] Python Environment Not Found!
echo ============================================
echo.
echo Could not find:
echo   - Conda 'stamp_env' environment
echo   - Local virtual environment
echo.
echo Please set up the environment:
echo.
echo   Option 1 (Quick Setup):
echo     1. Install Miniconda or Anaconda
echo     2. Run: quick_setup.bat
echo.
echo   Option 2 (Manual):
echo     1. conda create -n stamp_env python=3.11
echo     2. conda activate stamp_env
echo     3. pip install -r requirements.txt
echo.
echo See ENVIRONMENT_SETUP.md for details.
echo.
pause
exit /b 1
