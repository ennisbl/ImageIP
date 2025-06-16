"""
profile_manager.py — Create, display, and manage metadata profiles for ImageIP

Includes:
- Profile creation/editing
- Expandable card-style selector UI
- GPG key verification and creation
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from utils import gpg_key_exists, generate_gpg_key
from copyright_types import LICENSE_CHOICES

PROFILE_DIR = "profiles"
PROFILE_FILE = os.path.join(PROFILE_DIR, "profiles.json")

def ensure_profile_storage():
    """Ensure the profile storage directory and file exist."""
    os.makedirs(PROFILE_DIR, exist_ok=True)
    if not os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "w") as f:
            json.dump({}, f)

def load_profiles():
    """Load all saved profiles."""
    ensure_profile_storage()
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profiles(data):
    """Save profile data dictionary to disk."""
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def prompt_for_profile(existing=None):
    """Launch profile creation/edit modal GUI and return saved profile dict."""
    win = tk.Toplevel()
    win.title("Create/Edit Profile")
    win.geometry("360x340")
    win.resizable(False, False)

    # --- Fields ---
    ttk.Label(win, text="Image Author").pack(pady=(10, 0))
    author_var = tk.StringVar()
    author_entry = ttk.Entry(win, textvariable=author_var)
    author_entry.pack()
    author_entry.insert(0, existing.get("author", "") if existing else "")
    author_entry.focus_set()

    ttk.Label(win, text="Copyright Holder").pack(pady=(10, 0))
    copyright_var = tk.StringVar()
    copyright_entry = ttk.Entry(win, textvariable=copyright_var)
    copyright_entry.pack()
    copyright_entry.insert(0, existing.get("copyright", "") if existing else "")

    ttk.Label(win, text="GPG Key (Email)").pack(pady=(10, 0))
    gpg_var = tk.StringVar()
    gpg_entry = ttk.Entry(win, textvariable=gpg_var)
    gpg_entry.pack()
    gpg_entry.insert(0, existing.get("gpg_key", "") if existing else "")

    ttk.Label(win, text="License").pack(pady=(10, 0))
    license_var = tk.StringVar()
    license_combo = ttk.Combobox(win, textvariable=license_var, values=LICENSE_CHOICES, state="readonly")
    license_combo.pack()
    license_combo.set(existing.get("license", LICENSE_CHOICES[0]) if existing else LICENSE_CHOICES[0])

    def on_submit():
        author = author_var.get()
        gpg_key = gpg_var.get()
        license_choice = license_var.get()
        copyright_holder = copyright_var.get()

        if not author:
            messagebox.showwarning("Missing Info", "Please enter an author name.")
            return

        if gpg_key and not gpg_key_exists(gpg_key):
            if messagebox.askyesno("GPG Key Missing", f"No GPG key found for '{gpg_key}'. Generate it now?"):
                generate_gpg_key(gpg_key)
                messagebox.showinfo("GPG Key Created", f"New key generated for {gpg_key}.")

        profile = {
            "name": existing.get("name") if existing else author.replace(" ", "_"),
            "author": author,
            "gpg_key": gpg_key,
            "license": license_choice,
            "copyright": copyright_holder
        }

        if existing:
            profiles = load_profiles()
            profiles[profile["name"]] = profile
            save_profiles(profiles)

        win.result = profile
        win.destroy()

    # Save button
    ttk.Button(win, text="Save Profile", command=on_submit).pack(pady=15)

    # Enter navigation
    def focus_next(event, widget):
        widget.focus_set()
        return "break"

    author_entry.bind("<Return>", lambda e: focus_next(e, copyright_entry))
    copyright_entry.bind("<Return>", lambda e: focus_next(e, gpg_entry))
    gpg_entry.bind("<Return>", lambda e: focus_next(e, license_combo))
    license_combo.bind("<Return>", lambda e: on_submit())

    win.result = None
    win.wait_window()
    return win.result
