@echo off
REM Stamp Philatex Processor - Environment Check
call "%~dp0run_with_env.bat" scripts/test_setup.py
if %errorlevel% neq 0 pause
pause


