"""
Project Configuration for ImageIP

This file contains all project metadata and configuration in one central location.
Update version and other project details here.
"""

# Core Project Information
APP_NAME = "ImageIP"
VERSION = "1.1.1"
__version__ = VERSION  # For compatibility with standard Python packaging
AUTHOR = "Bernard Ennis"
AUTHOR_EMAIL = "majikthijs@gmail.com"
DESCRIPTION = "Digital Rights & Metadata Companion for Image Creators"

# Project URLs
PROJECT_URL = "https://github.com/ennisbl/ImageIP"
BUG_REPORTS_URL = "https://github.com/ennisbl/ImageIP/issues"
SOURCE_URL = "https://github.com/ennisbl/ImageIP"
DOCUMENTATION_URL = "https://github.com/ennisbl/ImageIP#readme"

# Assets
ICON_FILE = "assets/ImageIP_logo.png"

# Python Requirements
PYTHON_REQUIRES = ">=3.8"
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]

# Dependencies
REQUIRED_PACKAGES = [
    'Pillow>=10.0.0',
    'piexif>=1.1.3', 
    'python-gnupg>=0.5.0'
]

# Entry Points
CONSOLE_SCRIPTS = [
    'imageip=main:main',
]
GUI_SCRIPTS = [
    'imageip-gui=main:main',
]

# Modules to include
PY_MODULES = [
    'main', 'gui', 'signing_engine', 'crypto_fingerprint', 
    'profile_manager', 'signature_utils', 'verification_service',
    'signature_viewer', 'utils', 'copyright_types', 'project_config'
]

# Keywords for search/discovery
KEYWORDS = "digital-rights image-signing photography copyright gpg exif metadata"

# Supported file types
SUPPORTED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'tiff', 'bmp']

# Package classifiers
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Multimedia :: Graphics",
    "Topic :: Security :: Cryptography",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Environment :: X11 Applications",
    "Environment :: Win32 (MS Windows)",
    "Environment :: MacOS X",
]

# macOS py2app configuration
MACOS_BUNDLE_IDENTIFIER = f"com.bernard.{APP_NAME.lower()}"
MACOS_DOCUMENT_TYPES = [
    {
        'CFBundleTypeName': 'Image Files',
        'CFBundleTypeExtensions': SUPPORTED_IMAGE_EXTENSIONS,
        'CFBundleTypeRole': 'Editor'
    }
]

# Package data patterns
PACKAGE_DATA_PATTERNS = ['*.md', '*.txt', '*.png', '*.jpg', '*.ico']
