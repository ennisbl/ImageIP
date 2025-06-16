"""
gui.py — User interface for ImageIP

Handles:
- Main window with buttons
- Profile selection browser
- Folder chooser for signing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from profile_manager import launch_profile_browser, prompt_for_profile, save_profiles, load_profiles, save_last_used_profile, load_last_used_profile
from signing_engine import sign_images_in_folder


def launch_gui():
    """Start the ImageIP main window."""
    root = tk.Tk()
    root.title("ImageIP — Digital Rights & Signature Assistant")
    root.geometry("360x260")
    root.resizable(False, False)

    ttk.Label(root, text="Welcome to ImageIP", font=("Segoe UI", 16)).pack(pady=(15, 5))

    # 🎯 Active profile tracker
    _selected_profile = {}
    active_profile_text = tk.StringVar(value="No profile selected")
    ttk.Label(root, textvariable=active_profile_text, font=("Segoe UI", 9, "italic"), foreground="#444").pack()

    profiles = load_profiles()
    last_name = load_last_used_profile()
    if last_name and last_name in profiles:
        _selected_profile = profiles[last_name]
        active_profile_text.set(f"Active Profile: {last_name}")

    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)

    open_folder_var = tk.BooleanVar(value=True)
    _selected_profile = {}

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
        save_last_used_profile(profile["name"])  # ✅ record selection

    def _choose_and_tag_folder():
        if not _selected_profile:
            messagebox.showwarning("No Profile Selected", "Please select a profile first.")
            return
        path = filedialog.askdirectory(title="Choose Folder to Tag")
        if path:
            sign_images_in_folder(path, _selected_profile, open_folder=open_folder_var.get())

    ttk.Button(button_frame, text="➕ Create Profile", command=_create_profile).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="🗂 Browse Profiles", command=lambda: launch_profile_browser(root, _on_profile_selected)).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="📁 Tag Folder", command=_choose_and_tag_folder).pack(pady=5, fill="x", padx=20)
    ttk.Checkbutton(button_frame, text="Open folder after tagging", variable=open_folder_var).pack(pady=5)
    ttk.Button(button_frame, text="❌ Exit", command=root.destroy).pack(pady=15)

    root.mainloop()
