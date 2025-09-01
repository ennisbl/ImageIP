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

def get_version():
    """Get version from setup.py without triggering setuptools."""
    import os
    import re
    setup_path = os.path.join(os.path.dirname(__file__), 'setup.py')
    with open(setup_path, 'r') as f:
        content = f.read()
    
    # Find VERSION = "x.x.x" pattern
    version_match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        return version_match.group(1)
    return "1.1.0"  # fallback

VERSION = get_version()
__version__ = VERSION

from gui import launch_gui

def main():
    """Launch the ImageIP graphical user interface."""
    launch_gui()

if __name__ == "__main__":
    main()
