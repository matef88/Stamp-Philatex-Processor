@echo off
REM Stamp Philatex Processor - Image Processor
REM Usage: Double-click to process images in raw_data

call "%~dp0run_with_env.bat" scripts/process_stamps.py --input raw_data --parallel
pause
