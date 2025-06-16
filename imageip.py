import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
from PIL import Image
import piexif
from piexif.helper import UserComment
import gnupg
import json, os, platform
from datetime import datetime

# --- Constants ---
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.webp', '.tiff', '.gif')
LICENSES = {
    "All rights reserved": None,
    "CC BY": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-SA": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-ND": "https://creativecommons.org/licenses/by-nd/4.0/",
    "CC BY-NC": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC BY-NC-SA": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "CC BY-NC-ND": "https://creativecommons.org/licenses/by-nc-nd/4.0/"
}
PROFILE_DIR = "profiles"
SETTINGS_FILE = "settings.json"

# --- GPG ---
gpg = gnupg.GPG()

# --- Utilities ---
def ensure_dirs():
    os.makedirs(PROFILE_DIR, exist_ok=True)

def load_profiles():
    ensure_dirs()
    path = os.path.join(PROFILE_DIR, "profiles.json")
    return json.load(open(path)) if os.path.exists(path) else {}

def save_profiles(data):
    with open(os.path.join(PROFILE_DIR, "profiles.json"), "w") as f:
        json.dump(data, f, indent=2)

def gpg_key_exists(key_id):
    return any(key_id in uid for key in gpg.list_keys() for uid in key['uids'])

def generate_gpg_key(name_email):
    name, email = name_email.split("@")[0], name_email
    input_data = gpg.gen_key_input(name_email=email, name_real=name, passphrase='')
    gpg.gen_key(input_data)

def has_transparency(image):
    return image.mode in ("RGBA", "LA") or (image.mode == "P" and 'transparency' in image.info)

def get_year(image_path):
    try:
        exif = piexif.load(image_path)
        for ifd in ("0th", "Exif"):
            for tag in exif.get(ifd, {}):
                val = exif[ifd][tag]
                if isinstance(val, bytes):
                    val = val.decode(errors='ignore')
                try:
                    dt = datetime.strptime(val, "%Y:%m:%d %H:%M:%S")
                    return dt.year
                except:
                    pass
    except:
        pass
    try:
        stat = os.stat(image_path)
        return min(datetime.fromtimestamp(stat.st_ctime), datetime.fromtimestamp(stat.st_mtime)).year
    except:
        return datetime.now().year

def tag_filesystem(path, author, year):
    system = platform.system()
    label = f"© {year} {author}"
    try:
        if system == "Darwin" or system == "Linux":
            import xattr
            xattr.setxattr(path, b"user.comment", label.encode())
        elif system == "Windows":
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
            folder = shell.Namespace(os.path.dirname(path))
            item = folder.ParseName(os.path.basename(path))
            folder.GetDetailsOf(item, 21)  # Comments column
            item.ExtendedProperty("System.Comment", label)
        else:
            raise NotImplementedError
    except:
        with open(f"{path}.meta.json", "w") as f:
            json.dump({"author": author, "year": year}, f)

# --- GUI Helpers ---
def create_profile():
    profiles = load_profiles()
    name = simpledialog.askstring("Profile Name", "Enter profile name:")
    if not name: return

    author = simpledialog.askstring("Author", "Enter your name or organization:")
    license_choice = simpledialog.askstring("License", "\n".join(LICENSES.keys()), initialvalue="All rights reserved")
    gpg_key = simpledialog.askstring("GPG Key", "Enter GPG key email:")
    if not gpg_key_exists(gpg_key):
        if messagebox.askyesno("GPG Key", f"Generate new GPG key for {gpg_key}?"):
            generate_gpg_key(gpg_key)

    profiles[name] = {"author": author, "license": license_choice, "gpg_key": gpg_key}
    save_profiles(profiles)
    messagebox.showinfo("Done", f"Profile '{name}' saved.")

def choose_profile():
    profiles = load_profiles()
    if not profiles:
        messagebox.showerror("No Profiles", "Please create a profile first.")
        return None
    window = tk.Toplevel()
    window.title("Select Profile")
    choice = tk.StringVar(window)
    choice.set(next(iter(profiles)))
    ttk.Label(window, text="Choose profile:").pack(pady=5)
    menu = ttk.OptionMenu(window, choice, choice.get(), *profiles.keys())
    menu.pack(pady=10)
    btn = ttk.Button(window, text="OK", command=window.destroy)
    btn.pack(pady=10)
    window.wait_window()
    return profiles.get(choice.get())

# --- Main Logic ---
def sign_and_tag():
    profile = choose_profile()
    if not profile: return

    author = profile["author"]
    license_label = profile["license"]
    license_url = LICENSES.get(license_label)
    gpg_key = profile["gpg_key"]

    folder = filedialog.askdirectory()
    if not folder: return

    files = [f for f in os.listdir(folder) if f.lower().endswith(SUPPORTED_FORMATS)]
    for i, fname in enumerate(files):
        full = os.path.join(folder, fname)
        try:
            img = Image.open(full)
            year = get_year(full)
            if has_transparency(img):
                tag_filesystem(full, author, year)
            else:
                rgb = img.convert("RGB")
                out_jpg = os.path.splitext(full)[0] + "_signed.jpg"
                rgb.save(out_jpg, "JPEG", quality=100, subsampling=0)

                with open(out_jpg, 'rb') as f:
                    sig = gpg.sign_file(f, detach=True, output='signature.sig', default_key=gpg_key)
                signature = open("signature.sig", "rb").read().decode(errors='ignore')

                exif = piexif.load(out_jpg)
                exif["0th"][piexif.ImageIFD.Artist] = author.encode()
                copyright_str = f"© {year} {author}"
                if license_label and license_label != "All rights reserved":
                    copyright_str += f" — Licensed under {license_label}"
                exif["0th"][piexif.ImageIFD.Copyright] = copyright_str.encode()
                if license_url:
                    exif["0th"][piexif.ImageIFD.XPComment] = license_url.encode('utf-16le')
                exif["Exif"][piexif.ExifIFD.UserComment] = UserComment.dump(signature)
                piexif.insert(piexif.dump(exif), out_jpg)
        except Exception as e:
            print(f"[{i+1}] Failed to process {fname}: {e}")
    messagebox.showinfo("Done", f"Tagged and signed {len(files)} images.")

# --- GUI ---
root = tk.Tk()
root.title("ImageIP — Creative Signing Tool")

ttk.Button(root, text="Create Profile", command=create_profile).pack(padx=20, pady=10)
ttk.Button(root, text="Sign & Tag Folder", command=sign_and_tag).pack(padx=20, pady=10)
ttk.Button(root, text="Exit", command=root.quit).pack(padx=20, pady=10)

root.mainloop()
