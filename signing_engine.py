"""
signing_engine.py — Image processing and metadata embedding for ImageIP

Includes:
- Transparency detection and routing
- JPEG conversion and EXIF metadata embedding
- GPG signature generation
- Filesystem tagging fallback
"""

import os
import tempfile
from PIL import Image
import piexif
from piexif.helper import UserComment
from tkinter import messagebox
from utils import has_transparency, extract_creation_year, tag_filesystem_metadata
from utils import gpg  # pulled from utils
from copyright_types import LICENSE_URLS

SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.webp', '.tiff', '.bmp')

def sign_images_in_folder(folder_path: str, profile: dict):
    """
    Process all images in the given folder using the metadata profile.

    Args:
        folder_path (str): Directory of images to process.
        profile (dict): Metadata profile containing author, copyright, etc.
    """
    if not os.path.isdir(folder_path):
        messagebox.showerror("Invalid Folder", f"Folder not found: {folder_path}")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(SUPPORTED_FORMATS)]
    author = profile.get("author")
    copyright_holder = profile.get("copyright")
    license_type = profile.get("license", "All rights reserved")
    license_url = LICENSE_URLS.get(license_type)
    gpg_key = profile.get("gpg_key")

    for filename in files:
        filepath = os.path.join(folder_path, filename)
        try:
            image = Image.open(filepath)
            year = extract_creation_year(filepath)

            if has_transparency(image):
                label = f"© {year} {copyright_holder}"
                tag_filesystem_metadata(filepath, label)
                continue

            # Convert to RGB JPEG
            rgb = image.convert("RGB")
            out_path = os.path.splitext(filepath)[0] + "_signed.jpg"
            rgb.save(out_path, "JPEG", quality=100, subsampling=0)

            # Generate GPG signature
            with open(out_path, 'rb') as f:
                with tempfile.NamedTemporaryFile(delete=False) as temp_sig:
                    sig = gpg.sign_file(f, detach=True, output=temp_sig.name, default_key=gpg_key)
                    signature = temp_sig.read().decode("utf-8", errors="ignore")

            # Embed EXIF metadata
            exif_dict = piexif.load(out_path)
            exif_dict["0th"][piexif.ImageIFD.Artist] = author.encode()
            exif_dict["0th"][piexif.ImageIFD.Copyright] = f"© {year} {copyright_holder}".encode()
            if license_url:
                exif_dict["0th"][piexif.ImageIFD.XPComment] = license_url.encode("utf-16le")
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = UserComment.dump(signature)

            piexif.insert(piexif.dump(exif_dict), out_path)

        except Exception as e:
            print(f"[!] Error processing {filename}: {e}")

    messagebox.showinfo("Done", f"Processed {len(files)} images in: {folder_path}")
