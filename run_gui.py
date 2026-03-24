#!/usr/bin/env python
"""
Stamp Philatex Processor - GUI Launcher
Run this script to start the graphical interface.
"""

import sys
import os
from pathlib import Path


def setup_paths():
    """Setup Python paths for both development and frozen exe."""
    # Check if running as PyInstaller frozen executable
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as frozen exe
        # _MEIPASS is where PyInstaller extracts files
        base_path = Path(sys._MEIPASS)
    else:
        # Running as script
        base_path = Path(__file__).parent

    # Add paths to sys.path
    scripts_path = base_path / 'scripts'
    gui_path = base_path / 'gui'

    for path in [str(base_path), str(scripts_path), str(gui_path)]:
        if path not in sys.path:
            sys.path.insert(0, path)


def main():
    """Main entry point."""
    # Setup paths first
    setup_paths()

    # Now import and run GUI
    try:
        from gui.main_window import main as gui_main
        gui_main()
    except ImportError as e:
        # Fallback: try direct import
        print(f"Import error: {e}")
        print("Attempting fallback import...")
        try:
            from main_window import main as gui_main
            gui_main()
        except ImportError as e2:
            print(f"Fallback import also failed: {e2}")
            print("\nDebug info:")
            print(f"  sys.frozen: {getattr(sys, 'frozen', False)}")
            print(f"  sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
            print(f"  sys.executable: {sys.executable}")
            print(f"  sys.path: {sys.path[:5]}...")
            input("\nPress Enter to exit...")
            sys.exit(1)


if __name__ == "__main__":
    main()
