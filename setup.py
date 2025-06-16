from setuptools import setup

APP_NAME = "ImageIP"
VERSION = "1.0.0"
AUTHOR = "Bernard Ennis"
DESCRIPTION = "Digital Rights & Metadata Companion for Image Creators"
ICON_FILE = "assets/icon.png"  # Change to .icns if using for macOS app

APP = ['main.py']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': ICON_FILE,
    'packages': ['PIL', 'piexif', 'gnupg'],
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION,
        'CFBundleIdentifier': f'com.bernard.{APP_NAME.lower()}'
    }
}

setup(
    app=APP,
    name=APP_NAME,
    version=VERSION,
    author=AUTHOR,
    description=DESCRIPTION,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
