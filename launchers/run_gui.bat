@echo off
REM Stamp Philatex Processor - GUI Launcher
REM Usage: Double-click to start

call "%~dp0run_with_env.bat" run_gui.py
if %errorlevel% neq 0 pause
