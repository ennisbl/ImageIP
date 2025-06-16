import subprocess
import platform
import webbrowser
import os
import tempfile
from PIL import Image
import piexif
from piexif.helper import UserComment
from tkinter import messagebox
from utils import has_transparency, extract_creation_year, tag_filesystem_metadata, gpg
from copyright_types import LICENSE_URLS

SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.webp', '.tiff', '.bmp')

def sign_images_in_folder(folder_path: str, profile: dict, open_folder=True):
    """
    Process all images in the given folder using the selected profile.
    """
    if not os.path.isdir(folder_path):
        messagebox.showerror("Invalid Folder", f"Folder not found: {folder_path}")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(SUPPORTED_FORMATS)]

    author = profile.get("author", "")
    copyright_holder = profile.get("copyright", "")
    license_type = profile.get("license", "All rights reserved")
    gpg_key = profile.get("gpg_key")
    license_url = LICENSE_URLS.get(license_type)

    for filename in files:
        filepath = os.path.join(folder_path, filename)
        try:
            image = Image.open(filepath)
            year = extract_creation_year(filepath)

            if has_transparency(image):
                label = f"© {year} {copyright_holder}"
                tag_filesystem_metadata(filepath, label)
                continue

            rgb = image.convert("RGB")
            out_path = os.path.splitext(filepath)[0] + "_signed.jpg"
            rgb.save(out_path, "JPEG", quality=100, subsampling=0)

            # Generate GPG signature
            with open(out_path, 'rb') as f_in:
                with tempfile.NamedTemporaryFile(delete=False) as temp_sig:
                    gpg.sign_file(f_in, detach=True, output=temp_sig.name, keyid=gpg_key)

                with open(temp_sig.name, 'r', encoding="utf-8", errors="ignore") as f_sig:
                    signature = f_sig.read()
                os.remove(temp_sig.name)

            # Copy and embed EXIF metadata
            try:
                exif_dict = piexif.load(filepath)
            except Exception:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

            exif_dict["0th"][piexif.ImageIFD.Artist] = author.encode()
            exif_dict["0th"][piexif.ImageIFD.Copyright] = f"© {year} {copyright_holder}".encode()

            if license_url:
                exif_dict["0th"][piexif.ImageIFD.XPComment] = license_url.encode("utf-16le")

            exif_dict["Exif"][piexif.ExifIFD.UserComment] = UserComment.dump(signature)

            piexif.insert(piexif.dump(exif_dict), out_path)

        except Exception as e:
            print(f"[!] Error processing {filename}: {e}")

    messagebox.showinfo("Done", f"Processed {len(files)} images in: {folder_path}")
    # Open folder in system file browser
    if platform.system() == "Windows":
        os.startfile(folder_path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", folder_path])
    else:  # Linux
        try:
            subprocess.run(["xdg-open", folder_path])
        except Exception:
            webbrowser.open(f"file://{os.path.abspath(folder_path)}")

    if open_folder:
        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            print(f"[!] Could not open folder: {e}")
            webbrowser.open(f"file://{os.path.abspath(folder_path)}")

