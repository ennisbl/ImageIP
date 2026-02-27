"""
signature_viewer.py — View and verify embedded GPG signatures in images

Provides:
- A GUI file picker to inspect the EXIF > UserComment field
- Displays the full GPG signature in a read-only window
- Verifies the embedded signature using centralized verification service

Usage:
Call `view_embedded_signature()` from your GUI to allow users to inspect signed image files.

Requires:
- piexif
- GPG keys already present in the local keyring
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from verification_service import VerificationService


def view_embedded_signature():
    """
    Opens a file dialog for the user to select a JPEG image, extracts an embedded GPG signature 
    from the image's EXIF UserComment field, verifies the signature, and displays the verification 
    result in a new window.
    
    Workflow:
      1. Prompts the user to select a JPEG image file
      2. Uses centralized verification service to check signature validity
      3. Extracts signature and contact information for display
      4. Shows verification result and signature in a new window
    """
    filetypes = [("JPEG Images", "*.jpg *.jpeg")]
    path = filedialog.askopenfilename(title="Select Image to Inspect", filetypes=filetypes)
    if not path:
        return

    try:
        # Get signature information using centralized service
        sig_info = VerificationService.get_signature_info(path)
        
        if not sig_info["has_signature"]:
            messagebox.showinfo("No Signature", "This image doesn't contain an embedded signature.")
            return
        
        # Verify signature using centralized service
        verified = VerificationService.verify_with_exif_extraction(path, debug=True)
        
        # Display results
        sigwin = tk.Toplevel()
        sigwin.title("Embedded Signature & Metadata")
        sigwin.geometry("650x500")

        status = "✅ Signature is valid" if verified else "⚠️ Signature could not be verified"
        fg = "green" if verified else "orange"

        tk.Label(sigwin, text=status, foreground=fg, font=("Segoe UI", 10, "bold")).pack(pady=(10, 5))
        
        # Display contact information if available
        contact_info = sig_info["contact_info"]
        if contact_info:
            contact_frame = tk.Frame(sigwin)
            contact_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            tk.Label(contact_frame, text="📧 Contact Information:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
            
            contact_text = tk.Text(contact_frame, height=4, wrap="word", font=("Segoe UI", 9))
            contact_content = ""
            if contact_info.get("author"):
                contact_content += f"Author: {contact_info['author']}\n"
            if contact_info.get("email"):
                contact_content += f"Email: {contact_info['email']}\n"
            if contact_info.get("copyright"):
                contact_content += f"Copyright: {contact_info['copyright']}\n"
            if contact_info.get("license"):
                contact_content += f"License: {contact_info['license']}\n"
            
            contact_text.insert("1.0", contact_content)
            contact_text.configure(state="disabled")
            contact_text.pack(fill="x", pady=(2, 0))
        
        tk.Label(sigwin, text="🔐 GPG Signature (EXIF > UserComment):", font=("Segoe UI", 9, "bold")).pack()

        box = scrolledtext.ScrolledText(sigwin, wrap="word", font=("Consolas", 9))
        box.insert("1.0", sig_info["signature"].strip())
        box.configure(state="disabled")
        box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    except Exception as e:
        messagebox.showerror("Error", f"Could not read or verify signature:\n{e}")


def verify_signed_image(img_path: str, debug: bool = False) -> bool:
    """
    Verifies the signature embedded in the image's EXIF UserComment field.
    Uses the centralized verification service with EXIF profile extraction.
    
    Args:
        img_path (str): Path to the image file
        debug (bool, optional): Enable debug output
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    return VerificationService.verify_with_exif_extraction(img_path, debug)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify signed image")
    parser.add_argument("image", help="Path to the signed image")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    result = verify_signed_image(args.image, debug=args.debug)
    exit(0 if result else 1)
