"""
signing_engine.py — Core image signing and processing engine for ImageIP.

This module handles the core functionality of ImageIP's digital signature system:

- Image format conversion and optimization for signing
- Cryptographic fingerprint generation combining pixel data and metadata
- GPG-based digital signature creation and embedding
- EXIF metadata injection with copyright and licensing information
- Batch processing of image folders
- Transparency-preserving handling for images with alpha channels

The signing process:
1. Converts non-JPEG images to JPEG format (preserving originals with transparency)
2. Extracts or generates creation year metadata
3. Combines pixel data with attribution metadata to create a unique fingerprint
4. Signs the fingerprint using GPG with automatic key management
5. Embeds the signature and metadata into EXIF fields
6. Preserves image quality with maximum compression settings

Supported formats: JPEG, PNG, WebP, TIFF, BMP
Output format: JPEG (with embedded signatures and metadata)

Key Features:
    - Automatic transparency detection and handling
    - Passphrase-free GPG signing for improved user experience
    - Base64 signature encoding for reliable EXIF storage
    - Comprehensive metadata embedding (author, copyright, license)
    - Cross-platform folder opening after processing

Author: Bernard Ennis
License: MIT
"""

import os
import subprocess
import platform
import webbrowser
from PIL import Image
import piexif
from piexif.helper import UserComment
from tkinter import messagebox
import base64

from utils import (
    has_transparency,
    extract_creation_year,
    tag_filesystem_metadata,
    normalise_strings,
)
from copyright_types import LICENSE_URLS
from crypto_fingerprint import compute_visual_hash, get_attribution_bytes, gpg_manager

SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.webp', '.tiff', '.bmp')

def sign_images_in_folder(folder_path: str, profile: dict, open_folder=True, debug: bool = True):
    """
    Process and digitally sign all supported images in the specified folder.
    
    This function is the main entry point for batch image signing. It handles:
    - Image format conversion (non-JPEG to JPEG)
    - Transparency preservation (filesystem metadata for transparent images)
    - Cryptographic signature generation and embedding
    - EXIF metadata injection with copyright information
    - Cross-platform folder opening after processing
    
    Args:
        folder_path (str): Absolute path to folder containing images to sign
        profile (dict): User profile containing:
            - author (str): Image author name
            - copyright (str): Copyright holder name  
            - license (str): License type (e.g., "CC BY", "All rights reserved")
            - gpg_key (str): GPG key identifier for signing
        open_folder (bool, optional): Whether to open folder after processing. Defaults to True.
        debug (bool, optional): Enable debug output. Defaults to True.
        
    Returns:
        None: Displays success message dialog when complete
        
    Raises:
        Various exceptions related to image processing, GPG operations, or file I/O
        are caught and printed to console, allowing batch processing to continue
        for other images.
        
    Note:
        - Transparent images (PNG with alpha, etc.) are tagged with filesystem metadata only
        - Non-transparent images are converted to JPEG and digitally signed
        - Original files are preserved; converted files get "_converted.jpg" suffix
        - GPG signatures are embedded in EXIF UserComment field as Base64
        - Copyright metadata is embedded in standard EXIF fields
    """
    if not os.path.isdir(folder_path):
        messagebox.showerror("Invalid Folder", f"Folder not found: {folder_path}")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(SUPPORTED_FORMATS)]
    gpg_key = "4D08AD65CF951188848876CCD45D139CF7A5C3A8" # New key without passphrase

    # Convert transparency-capable non-JPEGs to JPEG, and leave originals untouched
    for filename in files:
        src_path = os.path.join(folder_path, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in (".jpg", ".jpeg"):
            try:
                image = Image.open(src_path)
                if has_transparency(image):
                    # Tag original and skip conversion
                    year = extract_creation_year(src_path)
                    label = f"© {year} {profile.get('copyright', '')}"
                    tag_filesystem_metadata(src_path, label)
                    print(f"⚪ Skipped signing {filename} (transparency preserved)")
                    continue

                # Otherwise convert to JPEG
                rgb = image.convert("RGB")
                new_name = os.path.splitext(filename)[0] + "_converted.jpg"
                new_path = os.path.join(folder_path, new_name)
                rgb.save(new_path, "JPEG", quality=100, subsampling=0)
                print(f"🌀 Converted {filename} → {new_name}")
            except Exception as e:
                print(f"[!] Failed to process {filename}: {e}")

    # Sign all JPEGs
    jpeg_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg"))]

    for filename in jpeg_files:
        path = os.path.join(folder_path, filename)
        try:
            # Extract metadata
            year = extract_creation_year(path)
            author = normalise_strings(profile.get("author", ""))
            copyright_holder = normalise_strings(profile.get("copyright", ""))
            license = normalise_strings(profile.get("license", ""))
            license_url = LICENSE_URLS.get(license)

            attribution_b64 = get_attribution_bytes(author, copyright_holder, license, year)

            # Save image as JPEG first to ensure consistent compression
            image = Image.open(path).convert("RGB")
            image.save(path, "JPEG", quality=100, subsampling=0)

            # Compute pixel+attribution fingerprint AFTER saving
            sha256 = compute_visual_hash(path, attribution_b64, debug=debug)

            # Sign the SHA-256 fingerprint
            print("Secret keys:", gpg_manager.gpg.list_keys(secret=True))
            print(f"[DEBUG] gpg key: {gpg_key}")
            # Signing without passphrase for simplicity
            print(f"[DEBUG] Signing without passphrase")
            result = gpg_manager.sign_data(sha256, detach=True, keyid=gpg_key)  # ASCII-armored by default

            # Step 1: get signature as clean string
            signature_str = str(result).strip()
            print("[DEBUG] Signature type:", type(signature_str))
            print("[DEBUG] Signature preview:", signature_str[:60])

            # Step 2: convert to bytes, then base64 encode
            signature_b64 = base64.b64encode(signature_str.encode("utf-8")).decode("ascii")
            print("[DEBUG] Base64 signature used:", signature_b64[:60])
            # Verify base64 roundtrip BEFORE embedding
            reconstructed = base64.b64decode(signature_b64).decode("utf-8")
            assert reconstructed == signature_str, "[!] Signature mutated during base64 encode/decode"

            if not signature_str.strip():
                print(f"[!] GPG signing failed for {filename}: {result.stderr}")
                continue
            print("signature_str type:", type(signature_str))
            print("signature_b64_bytes type:", type(signature_b64))

            # Embed signature in EXIF
            try:
                exif_dict = piexif.load(path)
            except Exception:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

            exif_dict["0th"][piexif.ImageIFD.Artist] = author.encode()
            exif_dict["0th"][piexif.ImageIFD.Copyright] = f"©{year} {copyright_holder}.".encode()
            exif_dict["0th"][piexif.ImageIFD.XPAuthor] = copyright_holder.encode("utf-16le")
            exif_dict["0th"][piexif.ImageIFD.XPKeywords] = license.encode("utf-16le")
            if license_url:
                exif_dict["0th"][piexif.ImageIFD.XPComment] = license_url.encode("utf-16le")
            # ✅ Step 3: directly pass to UserComment.dump()
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = UserComment.dump(signature_b64)

            print("[DEBUG] Base64 signature used:", signature_b64[:60])
            print("UserComment final type:", type(UserComment.dump(signature_b64)))  # Should be <class 'bytes'>

            piexif.insert(piexif.dump(exif_dict), path)
            print(f"✅ Signed: {filename}")

        except Exception as e:
            print(f"[!] Error signing {filename}: {e}")

    messagebox.showinfo("Done", f"Processed {len(jpeg_files)} signed image(s) in: {folder_path}")

    if open_folder:
        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            print(f"[!] Could not open folder: {e}")
            webbrowser.open(f"file://{os.path.abspath(folder_path)}")
