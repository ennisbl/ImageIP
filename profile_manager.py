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
from crypto_fingerprint import gpg_manager
from copyright_types import LICENSE_CHOICES

PROFILE_DIR = "profiles"
PROFILE_FILE = os.path.join(PROFILE_DIR, "profiles.json")
LAST_USED_FILE = os.path.join(PROFILE_DIR, "last_used.json")

def ensure_profile_storage():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    if not os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "w") as f:
            json.dump({}, f)

def load_profiles():
    ensure_profile_storage()
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profiles(data):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def prompt_for_profile(existing=None):
    win = tk.Toplevel()
    win.title("Create/Edit Profile")
    win.geometry("360x370")
    win.resizable(False, False)

    ttk.Label(win, text="Profile Name").pack(pady=(10, 0))
    name_var = tk.StringVar()
    name_entry = ttk.Entry(win, textvariable=name_var)
    name_entry.pack()
    name_entry.insert(0, existing.get("name", "") if existing else "")
    name_entry.focus_set()

    ttk.Label(win, text="Image Author").pack(pady=(10, 0))
    author_var = tk.StringVar()
    author_entry = ttk.Entry(win, textvariable=author_var)
    author_entry.pack()
    author_entry.insert(0, existing.get("author", "") if existing else "")

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
    
    # Info about automatic key generation
    info_text = "A signing key will be created automatically for this email"
    ttk.Label(win, text=info_text, font=("Segoe UI", 8), foreground="gray").pack(pady=(5, 0))

    ttk.Label(win, text="License").pack(pady=(10, 0))
    license_var = tk.StringVar()
    license_combo = ttk.Combobox(win, textvariable=license_var, values=LICENSE_CHOICES, state="readonly")
    license_combo.pack()
    license_combo.set(existing.get("license", LICENSE_CHOICES[0]) if existing else LICENSE_CHOICES[0])

    def on_submit():
        name = name_var.get().strip()
        author = author_var.get().strip()
        copyright_holder = copyright_var.get().strip()
        gpg_key = gpg_var.get().strip()
        license_choice = license_var.get().strip()

        if not name or not author:
            messagebox.showwarning("Missing Info", "Profile name and author are required.")
            return

        if gpg_key and not gpg_manager.key_exists(gpg_key):
            if messagebox.askyesno("GPG Key Missing", f"No signing key found for '{gpg_key}'. Generate it automatically?"):
                try:
                    # Generate key with no passphrase for automatic signing
                    fingerprint = gpg_manager.generate_key(gpg_key, passphrase="")
                    messagebox.showinfo("Key Created", f"Signing key for {gpg_key} created successfully!\nFingerprint: {fingerprint[:16]}...")
                except Exception as e:
                    messagebox.showerror("Key Generation Failed", f"Failed to create signing key: {e}")
                    return

        profile = {
            "name": name,
            "author": author,
            "gpg_key": gpg_key,
            "license": license_choice,
            "copyright": copyright_holder
        }

        profiles = load_profiles()
        profiles[name] = profile
        save_profiles(profiles)

        win.result = profile
        win.destroy()

    ttk.Button(win, text="Save Profile", command=on_submit).pack(pady=15)

    def focus_next(event, widget):
        widget.focus_set()
        return "break"

    name_entry.bind("<Return>", lambda e: focus_next(e, author_entry))
    author_entry.bind("<Return>", lambda e: focus_next(e, copyright_entry))
    copyright_entry.bind("<Return>", lambda e: focus_next(e, gpg_entry))
    gpg_entry.bind("<Return>", lambda e: focus_next(e, license_combo))
    license_combo.bind("<Return>", lambda e: on_submit())

    win.result = None
    win.wait_window()
    return win.result

def launch_profile_browser(parent, on_select):
    profiles = load_profiles()
    if not profiles:
        messagebox.showinfo("No Profiles", "Create a profile first.")
        return

    win = tk.Toplevel(parent)
    win.title("Select a Profile")
    win.geometry("500x500")

    canvas = tk.Canvas(win)
    scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    for key, prof in profiles.items():
        card = ttk.Frame(scroll_frame, relief="ridge", padding=10)
        card.pack(fill="x", expand=True, pady=5, padx=5)

        ttk.Label(card, text=prof["name"], font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(card, text=f"Author: {prof.get('author', '—')}").pack(anchor="w")
        ttk.Label(card, text=f"Copyright: {prof.get('copyright', '—')}").pack(anchor="w")
        ttk.Label(card, text=f"License: {prof.get('license', 'All rights reserved')}").pack(anchor="w")
        ttk.Label(card, text=f"GPG Key: {prof.get('gpg_key', '')}").pack(anchor="w")

        btn_frame = ttk.Frame(card)
        btn_frame.pack(anchor="e", pady=(5, 0))

        ttk.Button(btn_frame, text="✅ Use", command=lambda p=prof: [win.destroy(), on_select(p)]).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏ Edit", command=lambda k=key: _edit_profile(k, parent, win)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑 Delete", command=lambda k=key: _delete_profile(k, win)).pack(side="left", padx=5)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def _edit_profile(profile_key, parent, refresh_win):
    profiles = load_profiles()
    current = profiles.get(profile_key)

    updated = prompt_for_profile(existing=current)
    if updated:
        profiles[profile_key] = updated
        save_profiles(profiles)
        refresh_win.destroy()
        launch_profile_browser(parent, lambda _: None)

def _delete_profile(profile_key, refresh_win):
    profiles = load_profiles()
    if profile_key in profiles:
        confirm = messagebox.askyesno("Delete Profile", f"Delete profile '{profile_key}' permanently?")
        if confirm:
            del profiles[profile_key]
            save_profiles(profiles)
            refresh_win.destroy()
            launch_profile_browser(refresh_win.master, lambda _: None)

def save_last_used_profile(profile_name):
    with open(LAST_USED_FILE, "w", encoding="utf-8") as f:
        json.dump({"last": profile_name}, f)

def load_last_used_profile():
    try:
        with open(LAST_USED_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("last")
    except Exception:
        return None

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main root window

    def on_profile_selected(profile):
        print("Selected profile:")
        print(json.dumps(profile, indent=2))

    launch_profile_browser(root, on_profile_selected)
    root.mainloop()