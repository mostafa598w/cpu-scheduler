"""
main.py
-------
Entry point for the Smart CPU Scheduling Simulator.

Run:
    python main.py

Requirements:
    pip install matplotlib numpy
    (tkinter is bundled with standard Python)
"""

import sys
import os

# Add the project folder to the import path
sys.path.insert(0, os.path.dirname(__file__))


def check_dependencies():
    """Verify required packages are installed before launching the GUI."""
    missing = []
    for pkg in ("matplotlib", "numpy"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[ERROR] Missing packages: {', '.join(missing)}")
        print(f"  Install with:  pip install {' '.join(missing)}")
        sys.exit(1)


if __name__ == "__main__":
    check_dependencies()
    from gui import App
    app = App()
    app.mainloop()
