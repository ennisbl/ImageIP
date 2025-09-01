"""
utils.py — Cross-platform utility functions for ImageIP

Includes:
- Transparency detection
- EXIF and file timestamp parsing
- Filesystem metadata tagging (Windows/macOS/Linux)
- GPG key management helpers
"""

import os
import platform
from datetime import datetime
from PIL import Image
import piexif

def normalise_strings(s):
    return " ".join(s.strip().split())

def clean_xp_field(field):
    if isinstance(field, tuple):
        field = bytes(field)
    if isinstance(field, bytes):
        return normalise_strings(field.decode("utf-16le", "ignore"))
    if isinstance(field, str):
        return normalise_strings(field)
    return ""


def has_transparency(image: Image.Image) -> bool:
    """
    Check if the given image has an alpha channel or transparency metadata.

    Args:
        image (PIL.Image): Image object.

    Returns:
        bool: True if transparent, else False.
    """
    return image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    )


def extract_creation_year(image_path: str) -> int:
    """
    Extract the creation year from EXIF or fallback to file timestamps.

    Args:
        image_path (str): Path to image file.

    Returns:
        int: Earliest known year of image creation.
    """
    try:
        exif = piexif.load(image_path)
        possible_tags = [
            ("Exif", piexif.ExifIFD.DateTimeOriginal),
            ("Exif", piexif.ExifIFD.DateTimeDigitized),
            ("0th", piexif.ImageIFD.DateTime),
        ]
        for ifd, tag in possible_tags:
            val = exif.get(ifd, {}).get(tag)
            if val:
                decoded = val.decode() if isinstance(val, bytes) else val
                dt = datetime.strptime(decoded, "%Y:%m:%d %H:%M:%S")
                return dt.year
    except Exception:
        pass

    try:
        stat = os.stat(image_path)
        return min(datetime.fromtimestamp(stat.st_ctime), datetime.fromtimestamp(stat.st_mtime)).year
    except Exception:
        return datetime.now().year

def tag_filesystem_metadata(file_path: str, label: str):
    """
    Write metadata directly to the file system based on OS platform.

    Args:
        file_path (str): Path to image.
        label (str): Metadata label to apply (e.g. "© 2025 Bernard Ennis").
    """
    system = platform.system()
    try:
        if system in ("Darwin", "Linux"):
            import xattr
            xattr.setxattr(file_path, b"user.comment", label.encode())
        elif system == "Windows":
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
            folder = shell.Namespace(os.path.dirname(file_path))
            item = folder.ParseName(os.path.basename(file_path))
            folder.GetDetailsOf(item, 21)
            item.ExtendedProperty("System.Comment", label)
        else:
            raise NotImplementedError(f"Unsupported OS: {system}")
    except Exception as e:
        # Fallback: create .meta.json sidecar file
        try:
            with open(file_path + ".meta.json", "w", encoding="utf-8") as f:
                from json import dump
                dump({"label": label}, f, indent=2)
        except:
            print(f"Failed to tag metadata for {file_path}: {e}")