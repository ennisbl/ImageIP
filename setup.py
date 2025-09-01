from setuptools import setup, find_packages
import os

APP_NAME = "ImageIP"
VERSION = "1.1.1"
AUTHOR = "Bernard Ennis"
AUTHOR_EMAIL = "majikthijs@gmail.com"
DESCRIPTION = "Digital Rights & Metadata Companion for Image Creators"
ICON_FILE = "assets/ImageIP_logo.png"

# Read long description from README
def read_long_description():
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    return DESCRIPTION

# Read requirements
def read_requirements():
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return ['Pillow>=10.0.0', 'piexif>=1.1.3', 'python-gnupg>=0.5.0']

APP = ['main.py']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': ICON_FILE,
    'packages': ['PIL', 'piexif', 'gnupg', 'tkinter'],
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION,
        'CFBundleIdentifier': f'com.bernard.{APP_NAME.lower()}',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Image Files',
                'CFBundleTypeExtensions': ['jpg', 'jpeg', 'png', 'webp', 'tiff', 'bmp'],
                'CFBundleTypeRole': 'Editor'
            }
        ]
    }
}

setup(
    name=APP_NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/ennisbl/ImageIP",
    packages=find_packages(),
    py_modules=[
        'main', 'gui', 'signing_engine', 'crypto_fingerprint', 
        'profile_manager', 'signature_utils', 'signature_verifier', 
        'signature_viewer', 'utils', 'copyright_types'
    ],
    install_requires=read_requirements(),
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'imageip=main:main',
        ],
        'gui_scripts': [
            'imageip-gui=main:main',
        ],
    },
    classifiers=[
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
    ],
    keywords="digital-rights image-signing photography copyright gpg exif metadata",
    project_urls={
        "Bug Reports": "https://github.com/ennisbl/ImageIP/issues",
        "Source": "https://github.com/ennisbl/ImageIP",
        "Documentation": "https://github.com/ennisbl/ImageIP#readme",
    },
    # py2app options (macOS)
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'] if os.sys.platform == 'darwin' else [],
    include_package_data=True,
    package_data={
        '': ['*.md', '*.txt', '*.png', '*.jpg', '*.ico'],
    },
)
