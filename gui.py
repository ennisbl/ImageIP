"""
gui.py — User interface for ImageIP

Handles:
- Main window with buttons
- Profile selection browser
- Folder chooser for signing
"""

import tkinter as tk
from tkinter import ttk, filedialog
from profile_manager import launch_profile_browser
from signing_engine import sign_images_in_folder
from profile_manager import prompt_for_profile, save_profiles, load_profiles

def launch_gui():
    """Start the ImageIP main window."""
    root = tk.Tk()
    root.title("ImageIP — Digital Rights & Signature Assistant")
    root.geometry("360x240")
    root.resizable(False, False)

    ttk.Label(root, text="Welcome to ImageIP", font=("Segoe UI", 16)).pack(pady=15)

    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="➕ Create Profile", command=_create_profile).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="🗂 Browse Profiles", command=lambda: launch_profile_browser(root, _on_profile_selected)).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="📁 Tag Folder", command=lambda: _choose_and_tag_folder(root)).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="❌ Exit", command=root.destroy).pack(pady=15)

    root.mainloop()

# 🧠 Callbacks and helpers
_selected_profile = {}

def _create_profile():
    profile = prompt_for_profile()
    if profile:
        profiles = load_profiles()
        profiles[profile['name']] = profile
        save_profiles(profiles)

def _on_profile_selected(profile):
    global _selected_profile
    _selected_profile = profile

def _choose_and_tag_folder(parent):
    if not _selected_profile:
        from tkinter import messagebox
        messagebox.showwarning("No Profile Selected", "Please select a profile first.")
        return
    path = filedialog.askdirectory(title="Choose Folder to Tag")
    if path:
        sign_images_in_folder(path, _selected_profile)
