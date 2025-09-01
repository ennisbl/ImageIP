"""
gui.py — User interface for ImageIP Digital Rights Management Tool.

This module provides the main graphical user interface for ImageIP, which enables
photographers and content creators to:

- Create and manage signing profiles
- Digitally sign images with cryptographic signatures
- Embed copyright and licensing metadata into image files
- Verify the authenticity and integrity of signed images
- Browse and view embedded signatures

The GUI provides an intuitive interface for all core ImageIP functionality,
including automatic GPG key generation, batch folder processing, and
signature verification.

Key Components:
    - Profile management (create, edit, delete, select)
    - Folder-based image signing workflow
    - Signature viewing and verification tools
    - Cross-platform file handling

Dependencies:
    - tkinter (GUI framework)
    - profile_manager (profile creation and management)
    - signing_engine (core signing functionality)
    - signature_viewer (signature display)
    - signature_verifier (signature validation)

Author: Bernard Ennis
License: MIT
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# Correct local module imports:
from profile_manager import (
    launch_profile_browser,
    prompt_for_profile,
    save_profiles,
    load_profiles,
    save_last_used_profile,
    load_last_used_profile
)
from signing_engine import sign_images_in_folder
from signature_viewer import view_embedded_signature
from signature_verifier import verify_image_signature

def get_version():
    """Get version from setup.py without triggering setuptools."""
    import os
    import re
    setup_path = os.path.join(os.path.dirname(__file__), 'setup.py')
    with open(setup_path, 'r') as f:
        content = f.read()
    
    # Find VERSION = "x.x.x" pattern
    version_match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        return version_match.group(1)
    return "1.1.0"  # fallback

def launch_gui():
    """Start the ImageIP main window."""
    root = tk.Tk()
    root.title(f"ImageIP — Digital Rights & Signature Assistant v{get_version()}")
    root.geometry("360x260")
    root.resizable(False, False)

    ttk.Label(root, text="Welcome to ImageIP", font=("Segoe UI", 16)).pack(pady=(15, 5))

    # Active profile tracker
    _selected_profile = {}
    active_profile_text = tk.StringVar(value="No profile selected")
    ttk.Label(root, textvariable=active_profile_text, font=("Segoe UI", 9, "italic"), foreground="#444").pack()

    profiles = load_profiles()
    last_name = load_last_used_profile()
    if last_name and last_name in profiles:
        _selected_profile = profiles[last_name]
        active_profile_text.set(f"Active Profile: {last_name}")

    button_frame = ttk.Frame(root)
    button_frame.pack()

    open_folder_var = tk.BooleanVar(value=True)

    def _create_profile():
        profile = prompt_for_profile()
        if profile:
            profiles = load_profiles()
            profiles[profile['name']] = profile
            save_profiles(profiles)

    def _on_profile_selected(profile):
        nonlocal _selected_profile
        _selected_profile = profile
        active_profile_text.set(f"Active Profile: {profile.get('name', '—')}")
        save_last_used_profile(profile["name"])  # Record selection

    def _choose_and_tag_folder():
        if not _selected_profile:
            messagebox.showwarning("No Profile Selected", "Please select a profile first.")
            return
        path = filedialog.askdirectory(title="Choose Folder to Tag")
        if path:
            print("[GUI DEBUG] No passphrase needed - using passphrase-less signing")
            sign_images_in_folder(path, _selected_profile, open_folder=open_folder_var.get())

    def on_verify_signature():
        img_path = filedialog.askopenfilename(title="Select image to verify", filetypes=[("JPEG", "*.jpg *.jpeg")])
        if img_path:
            if not _selected_profile:
                messagebox.showwarning("Verification Failed", "No active profile selected. Please select a profile first.")
                return
            try:
                if verify_image_signature(img_path, _selected_profile, debug=True):
                    messagebox.showinfo("Verified", "This image is authentic and unaltered.")
            except Exception as e:
                messagebox.showerror("Verification Failed", str(e))
        else:
            messagebox.showwarning("Verification Failed", "No image selected.")

    ttk.Button(button_frame, text="➕ Create Profile", command=_create_profile).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="🗂 Browse Profiles", command=lambda: launch_profile_browser(root, _on_profile_selected)).pack(pady=5,
                                                                                                                        fill="x",
                                                                                                                        padx=20)
    ttk.Button(button_frame, text="📁 Tag Folder", command=_choose_and_tag_folder).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="🔍 View Signature", command=view_embedded_signature).pack(pady=5, fill="x", padx=20)
    ttk.Checkbutton(button_frame, text="Open folder after tagging", variable=open_folder_var).pack(pady=5)
    ttk.Button(button_frame, text="✅ Verify Signature", command=on_verify_signature).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="❌ Exit", command=root.destroy).pack(pady=15)

    root.mainloop()


if __name__ == "__main__":
    launch_gui()
