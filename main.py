"""
main.py — Entry point for the ImageIP application.

ImageIP is a digital rights management and image signing tool that allows
photographers and content creators to embed cryptographic signatures and
copyright metadata directly into their images.

This module serves as the main entry point for the GUI application.

Author: Bernard Ennis
License: MIT
Version: 1.0.2
"""

from gui import launch_gui

__version__ = "1.0.2"

def main():
    """Launch the ImageIP graphical user interface."""
    launch_gui()

if __name__ == "__main__":
    main()
