"""
signature_viewer.py — View and verify embedded GPG signatures in images

Provides:
- A GUI file picker to inspect the EXIF > UserComment field
- Displays the full GPG signature in a read-only window
- (Optional) Verifies the embedded signature against known GPG public keys

Usage:
Call `view_embedded_signature()` from your GUI to allow users to inspect signed image files.

Requires:
- piexif
- GPG keys already present in the local keyring
"""

import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import piexif
from piexif.helper import UserComment
from utils import extract_creation_year
from crypto_fingerprint import compute_visual_hash, get_attribution_bytes, gpg_manager

# Remove duplicated header handling by importing our centralized function.
from signature_utils import extract_signature_from_exif


def view_embedded_signature():
    """
    Opens a file dialog for the user to select a JPEG image, extracts an embedded GPG signature from the image's EXIF UserComment field,
    verifies the signature against the SHA-256 hash of the image, and displays the verification result in a new window.
    Workflow:
      1. Prompts the user to select a JPEG image file.
      2. Loads the EXIF data from the selected image and attempts to retrieve the embedded signature from the UserComment field.
      3. Uses `extract_signature_from_exif()` to decode the signature.
      4. Computes the SHA-256 hash of the image file.
      5. Verifies the extracted signature against the computed hash using the GPG manager.
      6. Displays the verification result and the signature in a new window.
    Displays appropriate error or info dialogs if the image does not contain a signature or if any error occurs during processing.
    """
    filetypes = [("JPEG Images", "*.jpg *.jpeg")]
    path = filedialog.askopenfilename(title="Select Image to Inspect", filetypes=filetypes)
    if not path:
        return

    try:
        exif = piexif.load(path)
        raw = exif["Exif"].get(piexif.ExifIFD.UserComment)
        print("[DEBUG] Retrieved raw data from EXIF:", raw)
        if not raw:
            messagebox.showinfo("No Signature", "This image doesn't contain an embedded signature.")
            return

        # Use the centralized extraction function – it loads (and strips the EXIF header) then decodes Base64.
        signature = extract_signature_from_exif(raw)
        print("[DEBUG] Extracted signature using signature_utils:", repr(signature))

        # Extract attribution data from EXIF to reconstruct the same hash used during signing
        author = exif["0th"].get(piexif.ImageIFD.Artist, b"").decode("utf-8", "ignore").strip()
        
        # Extract copyright holder from XPAuthor field (where it's actually stored)
        copyright_holder = ""
        if piexif.ImageIFD.XPAuthor in exif["0th"]:
            xp_author_data = exif["0th"][piexif.ImageIFD.XPAuthor]
            if isinstance(xp_author_data, tuple):
                # Convert tuple of bytes to bytes, then decode
                copyright_holder = bytes(xp_author_data).decode("utf-16le", "ignore").strip()
            elif isinstance(xp_author_data, bytes):
                copyright_holder = xp_author_data.decode("utf-16le", "ignore").strip()
            else:
                print(f"[DEBUG] Unexpected XPAuthor data type: {type(xp_author_data)}")
                copyright_holder = str(xp_author_data)
        
        # Extract license from XPKeywords
        license = ""
        if piexif.ImageIFD.XPKeywords in exif["0th"]:
            xp_keywords_data = exif["0th"][piexif.ImageIFD.XPKeywords]
            if isinstance(xp_keywords_data, tuple):
                # Convert tuple of bytes to bytes, then decode
                license = bytes(xp_keywords_data).decode("utf-16le", "ignore").strip()
            elif isinstance(xp_keywords_data, bytes):
                license = xp_keywords_data.decode("utf-16le", "ignore").strip()
            else:
                print(f"[DEBUG] Unexpected XPKeywords data type: {type(xp_keywords_data)}")
                license = str(xp_keywords_data)
        
        year = extract_creation_year(path)
        
        # Compute the same hash used during signing (pixels + attribution)
        attribution_b64 = get_attribution_bytes(author, copyright_holder, license, year)
        sha256 = compute_visual_hash(path, attribution_b64)

        # Write signature to temp file for verification
        from signature_utils import write_signature_to_temp_file
        tmp_sig_filename = write_signature_to_temp_file(signature)
        verified = gpg_manager.verify_data(sha256, tmp_sig_filename)
        import os
        os.unlink(tmp_sig_filename)

        sigwin = tk.Toplevel()
        sigwin.title("Embedded Signature")
        sigwin.geometry("640x440")

        status = "✅ Signature is valid" if verified else "⚠️ Signature could not be verified"
        fg = "green" if verified else "orange"

        tk.Label(sigwin, text=status, foreground=fg, font=("Segoe UI", 10, "bold")).pack(pady=(10, 5))
        tk.Label(sigwin, text="GPG Signature (EXIF > UserComment):", font=("Segoe UI", 9, "bold")).pack()

        box = scrolledtext.ScrolledText(sigwin, wrap="word", font=("Consolas", 9))
        box.insert("1.0", signature.strip())
        box.configure(state="disabled")
        box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    except Exception as e:
        messagebox.showerror("Error", f"Could not read or verify signature:\n{e}")


def verify_signed_image(img_path: str, debug: bool = False) -> bool:
    """
    Verifies the signature embedded in the image's EXIF UserComment field.
    Extracts supporting EXIF metadata, computes the image hash with attribution, and calls GPG manager for verification.
    """
    try:
        exif = piexif.load(img_path)
        raw_sig = exif["Exif"].get(piexif.ExifIFD.UserComment)
        if not raw_sig:
            if debug:
                print("[DEBUG] No signature found in EXIF.")
            return False

        # Use the centralized extraction function.
        signature = extract_signature_from_exif(raw_sig)

        author = exif["0th"].get(piexif.ImageIFD.Artist, b"").decode("utf-8", "ignore").strip()
        
        # Extract copyright holder from XPAuthor field (where it's actually stored)
        copyright_holder = ""
        if piexif.ImageIFD.XPAuthor in exif["0th"]:
            xp_author_data = exif["0th"][piexif.ImageIFD.XPAuthor]
            if isinstance(xp_author_data, tuple):
                # Convert tuple of bytes to bytes, then decode
                copyright_holder = bytes(xp_author_data).decode("utf-16le", "ignore").strip()
            elif isinstance(xp_author_data, bytes):
                copyright_holder = xp_author_data.decode("utf-16le", "ignore").strip()
            else:
                if debug:
                    print(f"[DEBUG] Unexpected XPAuthor data type: {type(xp_author_data)}")
                copyright_holder = str(xp_author_data)
        
        license = ""
        if piexif.ImageIFD.XPKeywords in exif["0th"]:
            xp_keywords_data = exif["0th"][piexif.ImageIFD.XPKeywords]
            if isinstance(xp_keywords_data, tuple):
                # Convert tuple of bytes to bytes, then decode
                license = bytes(xp_keywords_data).decode("utf-16le", "ignore").strip()
            elif isinstance(xp_keywords_data, bytes):
                license = xp_keywords_data.decode("utf-16le", "ignore").strip()
            else:
                if debug:
                    print(f"[DEBUG] Unexpected XPKeywords data type: {type(xp_keywords_data)}")
                license = str(xp_keywords_data)
        year = extract_creation_year(img_path)

        attribution_b64 = get_attribution_bytes(author, copyright_holder, license, year)
        if debug:
            print("[DEBUG] Author       :", repr(author))
            print("[DEBUG] Copyright    :", repr(copyright_holder))
            print("[DEBUG] License URL  :", repr(license))
            print("[DEBUG] Attribution  :", repr(attribution_b64.decode('utf-8', 'ignore')[:80]) + "...")

        sha256 = compute_visual_hash(img_path, attribution_b64)
        if debug:
            print("[DEBUG] Computed SHA-256:", sha256[:64])

        # Write signature to temp file for verification
        from signature_utils import write_signature_to_temp_file
        tmp_sig_filename = write_signature_to_temp_file(signature)
        result = gpg_manager.verify_data(sha256, tmp_sig_filename)
        import os
        os.unlink(tmp_sig_filename)
        
        if result:
            print("✅ Signature is valid and image is unchanged.")
            return True
        else:
            if debug:
                print("[DEBUG] Signature failed to verify.")
            return False

    except Exception as e:
        print(f"[!] Verification error: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify signed image")
    parser.add_argument("image", help="Path to the signed image")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    from signature_viewer import verify_signed_image
    result = verify_signed_image(args.image, debug=args.debug)
    exit(0 if result else 1)
