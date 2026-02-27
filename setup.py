from setuptools import setup, find_packages
import os
import sys

# Add build directory to path for project_config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'build'))

try:
    from build.project_config import VERSION, APP_NAME, DESCRIPTION, AUTHOR, AUTHOR_EMAIL
except ImportError:
    # Fallback values if project_config is not available
    VERSION = "1.0.0"
    APP_NAME = "ImageIP"
    DESCRIPTION = "Digital Image Authentication and Copyright Protection Tool"
    AUTHOR = "ImageIP Team"
    AUTHOR_EMAIL = "contact@imageip.com"

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
    return REQUIRED_PACKAGES

APP = ['main.py']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': ICON_FILE,
    'packages': ['PIL', 'piexif', 'gnupg', 'tkinter'],
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION,
        'CFBundleIdentifier': MACOS_BUNDLE_IDENTIFIER,
        'CFBundleDocumentTypes': MACOS_DOCUMENT_TYPES
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
    url=PROJECT_URL,
    packages=find_packages(),
    py_modules=PY_MODULES,
    install_requires=read_requirements(),
    python_requires=PYTHON_REQUIRES,
    entry_points={
        'console_scripts': CONSOLE_SCRIPTS,
        'gui_scripts': GUI_SCRIPTS,
    },
    classifiers=CLASSIFIERS,
    keywords=KEYWORDS,
    project_urls={
        "Bug Reports": BUG_REPORTS_URL,
        "Source": SOURCE_URL,
        "Documentation": DOCUMENTATION_URL,
    },
    # py2app options (macOS)
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'] if sys.platform == 'darwin' else [],
    include_package_data=True,
    package_data={
        '': PACKAGE_DATA_PATTERNS,
    },
)
