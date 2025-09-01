"""
signature_utils.py — Utilities for GPG signature handling in ImageIP.

This module provides common utilities for working with GPG signatures embedded
in image EXIF metadata, including extraction, encoding, and file operations.

Key Functions:
    - extract_signature_from_exif(): Safely extract and decode signatures from EXIF
    - write_signature_to_temp_file(): Create temporary files for GPG verification
    - compute_image_fingerprint(): Generate fingerprints from images and profiles

The module handles the complex process of extracting Base64-encoded GPG signatures
from EXIF UserComment fields, which involves:
1. Loading raw EXIF data (may be bytes or tuple)
2. Decoding UserComment with EXIF header handling
3. Base64 decoding to recover original ASCII-armored GPG signature
4. Proper encoding for GPG verification operations

Author: Bernard Ennis
License: MIT
"""

import base64
from piexif.helper import UserComment

def extract_signature_from_exif(exif_data) -> str:
    """
    Extract and return the ASCII-armored PGP signature from the raw EXIF UserComment data.
    """
    # Handle case where exif_data might be a tuple or other unexpected type
    if isinstance(exif_data, tuple):
        if len(exif_data) > 0:
            exif_data = exif_data[0]
        else:
            raise ValueError("Empty tuple provided as EXIF data")
    
    # Ensure we have bytes
    if not isinstance(exif_data, bytes):
        raise ValueError(f"Expected bytes or tuple, got {type(exif_data)}")
    
    # Load the UserComment string
    user_comment = UserComment.load(exif_data)
    
    # Optionally check and strip the header if present.
    header = "ASCII\0\0\0"
    if user_comment.startswith(header):
        user_comment = user_comment[len(header):]
    
    # Now, assume that what remains is a Base64-encoded string.
    try:
        decoded_signature = base64.b64decode(user_comment).decode("utf-8")
    except Exception as e:
        raise ValueError("Failed to decode Base64 signature: " + str(e))
    
    return decoded_signature

def write_signature_to_temp_file(signature: str) -> str:
    """
    Write the provided signature string to a temporary file and return the filename.
    The signature is written as exact bytes (UTF-8 encoded) in binary mode.
    """
    import tempfile, os
    signature_bytes = signature.encode("utf-8")
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp_sig_file:
        tmp_sig_file.write(signature_bytes)
        tmp_sig_file.flush()
        tmp_sig_filename = tmp_sig_file.name
    return tmp_sig_filename

def compute_image_fingerprint(image_path: str, profile: dict, debug: bool = False) -> str:
    """
    Extract image metadata, compute attribution string, and compute the image fingerprint.
    
    Args:
      image_path (str): Path to the image.
      profile (dict): Profile data containing author, copyright_holder, and license.
      debug (bool): Enable debug logging.
      
    Returns:
      A SHA-256 hash (string) computed from the image pixels combined with the attribution data.
    """
    from utils import extract_creation_year, normalise_strings
    from crypto_fingerprint import get_attribution_bytes, compute_visual_hash
    from copyright_types import LICENSE_URLS

    year = extract_creation_year(image_path)
    author = normalise_strings(profile.get("author", ""))
    copyright_holder = normalise_strings(profile.get("copyright", ""))
    license = normalise_strings(profile.get("license", ""))
    license_url = LICENSE_URLS.get(license)  # if you need to use it later

    # Get attribution bytes (or Base64; name should imply what it returns)
    attribution_bytes = get_attribution_bytes(author, copyright_holder, license, year)

    # Compute the image fingerprint using the provided attribution data
    sha256 = compute_visual_hash(image_path, attribution_bytes, debug=debug)
    if debug:
        print("[DEBUG] Computed SHA-256:", sha256)
    
    return sha256
