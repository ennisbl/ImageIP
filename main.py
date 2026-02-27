"""
main.py — Entry point for the ImageIP application.

ImageIP is a digital rights management and image signing tool that allows
photographers and content creators to embed cryptographic signatures and
copyright metadata directly into their images.

This module serves as the main entry point for the GUI application.

Author: Bernard Ennis
License: MIT
Version: 1.1.1
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

# Add build directory to path for project_config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'build'))

try:
    from build.project_config import VERSION, APP_NAME
except ImportError:
    # Fallback if project_config is not available
    VERSION = "Unknown"
    APP_NAME = "ImageIP"

from gui import launch_gui

def main():
    """Launch the ImageIP graphical user interface."""
    launch_gui()

if __name__ == "__main__":
    main()
